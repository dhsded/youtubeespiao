"""
High-Precision Metrics Calculator for YouTube Video Performance & Traffic Dynamics (vidIQ Benchmark).
Features:
- Robust Statistical VPH (Views Per Hour) Engine using Rolling Window & Ordinary Least Squares (OLS) Linear Regression.
- Neutralizes YouTube CDN batch synchronization and cache latency ('staircase effect').
- Adaptive rolling window: 2-4 hours for active videos, expanding to 12-24 hours for long-tail/historical videos.
- Comprehensive Edge-case handling (Insufficient samples fallback, negative audit delta clamping with 'audit_detected' flag, sub-0.1 jitter threshold).
- Calibrated Power-Law Search & Evergreen Decay Curve baseline for single-snapshot videos.
- Traffic Vitality Status (Viral, Tráfego Acelerado, Evergreen Ativo, Residual, Estagnado).
- 90-Day Recent Traffic Calculation ('Views nos Últimos 90 Dias').
- Daily, Monthly, and Annual passive traffic projections.
"""

import re
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Union, Tuple, List

# In-memory snapshot history storage for real-time statistical OLS VPH tracking across cycles
_VIDEO_SNAPSHOT_HISTORY: Dict[str, List[Tuple[float, int]]] = {}

# Backward-compatibility alias
_VIDEO_SNAPSHOTS: Dict[str, Tuple[float, int]] = {}

def record_video_snapshot(video_id: str, view_count: int, timestamp: Optional[float] = None):
    """
    Store timestamped view count snapshots in a rolling history buffer for statistical OLS VPH calculation.
    """
    if not video_id:
        return
    now_ts = timestamp or datetime.now(timezone.utc).timestamp()
    
    # Update backward-compatible map
    _VIDEO_SNAPSHOTS[video_id] = (now_ts, int(view_count))

    if video_id not in _VIDEO_SNAPSHOT_HISTORY:
        _VIDEO_SNAPSHOT_HISTORY[video_id] = []
    
    history = _VIDEO_SNAPSHOT_HISTORY[video_id]
    if not history or history[-1][0] < (now_ts - 1.0):
        history.append((now_ts, int(view_count)))
    else:
        history[-1] = (now_ts, int(view_count))

    # Keep rolling buffer capped to the last 48 hours to manage memory
    cutoff_48h = now_ts - (48.0 * 3600.0)
    _VIDEO_SNAPSHOT_HISTORY[video_id] = [h for h in history if h[0] >= cutoff_48h]

def calculate_ols_vph_from_history(
    history: List[Tuple[float, int]],
    now_ts: float,
    min_window_hours: float = 4.0,
    max_window_hours: float = 24.0
) -> Tuple[Optional[float], bool]:
    """
    Computes statistical Views Per Hour (VPH) using Ordinary Least Squares (OLS)
    over an adaptive rolling time window.
    
    Returns:
        (calculated_vph, audit_detected_flag)
    """
    if not history or len(history) < 2:
        return None, False

    # 1. Rolling Window Selection (2 to 4 hours retroactive from current point)
    cutoff_recent = now_ts - (min_window_hours * 3600.0)
    window_points = [p for p in history if p[0] >= cutoff_recent]

    # For older / long-tail videos or low variance in recent window, expand window to 12-24 hours
    if len(window_points) < 3 or (window_points[-1][1] - window_points[0][1] == 0 and len(history) >= 3):
        cutoff_expanded = now_ts - (max_window_hours * 3600.0)
        window_points = [p for p in history if p[0] >= cutoff_expanded]

    if len(window_points) < 2:
        return None, False

    t_0 = window_points[0][0]
    t_last = window_points[-1][0]
    delta_total_hours = (t_last - t_0) / 3600.0

    # 3. Edge Cases: Insufficient samples (< 3 records) or total time span < 1 hour
    if len(window_points) < 3 or delta_total_hours < 1.0:
        if delta_total_hours >= 0.05: # At least 3 minutes between measurements
            v_start = window_points[0][1]
            v_end = window_points[-1][1]
            delta_v = v_end - v_start
            if delta_v < 0:
                # YouTube audit / bot views removed
                return 0.0, True
            raw_vph = delta_v / delta_total_hours
            if raw_vph < 0.1:
                return 0.0, False
            return raw_vph, False
        else:
            return None, False

    # 2. Smoothing Algorithm: Ordinary Least Squares (OLS) Linear Regression
    # Points (t_i, V_i) where t_i is elapsed time in hours relative to t_0
    N = len(window_points)
    sum_t = 0.0
    sum_v = 0.0
    sum_tv = 0.0
    sum_t2 = 0.0

    for ts_i, v_i in window_points:
        t_i = (ts_i - t_0) / 3600.0 # Time in hours as floating-point
        sum_t += t_i
        sum_v += float(v_i)
        sum_tv += (t_i * float(v_i))
        sum_t2 += (t_i * t_i)

    # Slope formula: m = [ N * Σ(t * V) - (Σt * ΣV) ] / [ N * Σ(t²) - (Σt)² ]
    denom = (N * sum_t2) - (sum_t * sum_t)
    if abs(denom) < 1e-9:
        # Fallback to direct extreme difference
        delta_v = window_points[-1][1] - window_points[0][1]
        if delta_v < 0:
            return 0.0, True
        raw_vph = delta_v / max(0.01, delta_total_hours)
        return (0.0 if raw_vph < 0.1 else raw_vph), False

    slope_m = ((N * sum_tv) - (sum_t * sum_v)) / denom

    # Edge Case: YouTube Audit (Negative slope) -> Clamp to 0 and signal audit
    if slope_m < 0:
        return 0.0, True

    # Edge Case: Near zero (< 0.1 VPH) -> Clamp to 0 to prevent floating-point noise
    if slope_m < 0.1:
        return 0.0, False

    return slope_m, False

def parse_relative_time_text(text: str) -> Optional[float]:
    """
    Parse relative time strings in Portuguese and English to elapsed days.
    Examples:
      - 'há 2 horas', '2 hours ago' -> 2/24 = 0.083 days
      - 'há 35 minutos', '35 minutes ago' -> 35/1440 = 0.024 days
      - 'há 4 dias', '4 days ago' -> 4.0 days
      - 'há 2 semanas', '2 weeks ago' -> 14.0 days
      - 'há 3 meses', '3 months ago' -> 3 * 30.416 = 91.25 days
      - 'há 1 ano', '1 year ago', 'há 5 anos' -> 5 * 365.25 = 1826.25 days
    """
    if not text:
        return None
    clean = text.lower().strip()
    
    nums = re.findall(r"(\d+(?:[.,]\d+)?)", clean)
    if not nums:
        if "ontem" in clean or "yesterday" in clean:
            return 1.0
        if "hora" in clean or "hour" in clean:
            return 0.0416 # ~1 hour
        if "minuto" in clean or "minute" in clean or "segundo" in clean or "second" in clean:
            return 0.01
        return None
    
    val = float(nums[0].replace(",", "."))
    
    if any(u in clean for u in ["segundo", "second", "seg"]):
        return max(0.001, val / 86400.0)
    elif any(u in clean for u in ["minuto", "minute", "min"]):
        return max(0.005, val / 1440.0)
    elif any(u in clean for u in ["hora", "hour", "hr"]):
        return max(0.0416, val / 24.0)
    elif any(u in clean for u in ["dia", "day"]):
        return max(0.5, val)
    elif any(u in clean for u in ["semana", "week"]):
        return max(1.0, val * 7.0)
    elif any(u in clean for u in ["mês", "mes", "month"]):
        return max(15.0, val * 30.416)
    elif any(u in clean for u in ["ano", "year"]):
        return max(180.0, val * 365.25)
    
    return None

def format_vph(vph_val: float) -> str:
    """Format VPH into human-readable notation with decimal precision for sub-1 values."""
    if vph_val is None:
        return "⚡ 0 VPH"
    if vph_val >= 100.0:
        return f"⚡ {format_number(round(vph_val))} VPH"
    elif vph_val >= 10.0:
        return f"⚡ {vph_val:.1f} VPH"
    elif vph_val >= 1.0:
        return f"⚡ {vph_val:.1f} VPH"
    elif vph_val >= 0.05:
        return f"⚡ {vph_val:.2f} VPH"
    else:
        return "⚡ < 0.1 VPH"

def calculate_video_metrics(
    view_count: int,
    upload_date: Optional[Union[str, datetime]] = None,
    timestamp: Optional[int] = None,
    published_text: Optional[str] = None,
    video_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate high-precision, calibrated performance metrics for a YouTube video:
    - VPH (Views per Hour) using OLS linear regression across rolling windows.
    - Audit detection flag when YouTube removes views.
    - 90-Day Views Volume & Daily Pace ('Views nos Últimos 90 Dias').
    - Current Daily Traffic Estimate (Views/dia correntes).
    - Monthly & Yearly Traffic Projections.
    - Traffic Vitality Status (Viral, Tráfego Acelerado, Evergreen Ativo, Residual, Estagnado).
    """
    now = datetime.now(timezone.utc)
    now_ts = now.timestamp()
    pub_dt = None
    days_active = None
    date_str = None

    if isinstance(upload_date, datetime):
        pub_dt = upload_date if upload_date.tzinfo else upload_date.replace(tzinfo=timezone.utc)
    elif timestamp:
        try:
            pub_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception:
            pass
    elif isinstance(upload_date, str) and upload_date:
        clean_date = upload_date.strip().replace("-", "").replace("/", "")
        if len(clean_date) >= 8 and clean_date[:8].isdigit():
            try:
                pub_dt = datetime(int(clean_date[:4]), int(clean_date[4:6]), int(clean_date[6:8]), tzinfo=timezone.utc)
            except Exception:
                pass
        else:
            for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
                try:
                    pub_dt = datetime.strptime(upload_date[:19], fmt[:len(upload_date[:19])]).replace(tzinfo=timezone.utc)
                    break
                except Exception:
                    continue

    upload_year = None
    if pub_dt:
        diff_days = (now - pub_dt).total_seconds() / 86400.0
        days_active = max(0.01, diff_days) # At least ~15 minutes
        date_str = pub_dt.strftime("%d/%m/%Y")
        upload_year = pub_dt.year
    else:
        # Fallback to relative text parsing (e.g. 'há 2 dias', '3 weeks ago')
        rel_days = parse_relative_time_text(published_text) if published_text else None
        if rel_days is not None:
            days_active = max(0.01, rel_days)
            est_dt = now - timedelta(days=days_active)
            date_str = est_dt.strftime("%d/%m/%Y")
            upload_year = est_dt.year
        else:
            days_active = 30.0
            date_str = published_text.strip().capitalize() if published_text else "Recente"

    hours_active = max(0.25, days_active * 24.0)

    # 1. Statistical OLS VPH Calculation via Rolling Window History
    ols_vph = None
    audit_detected = False
    if video_id:
        record_video_snapshot(video_id, view_count, now_ts)
        history = _VIDEO_SNAPSHOT_HISTORY.get(video_id, [])
        ols_vph, audit_detected = calculate_ols_vph_from_history(history, now_ts)

    # 2. Calibrated Power-Law Search & Evergreen Decay Curve baseline (for initial pass)
    if hours_active <= 72.0:
        # Launch phase (0 to 72 hours): Peak initial launch velocity
        modeled_vph = float(view_count) / hours_active
        daily_rate = modeled_vph * 24.0
        views_90d = int(view_count)
    elif days_active <= 14.0:
        # Early momentum phase (3 to 14 days): Initial post-launch stabilization
        lifetime_daily = float(view_count) / days_active
        stabilization_decay = 1.0 - 0.45 * ((days_active - 3.0) / 11.0)
        daily_rate = max(1.0, lifetime_daily * stabilization_decay)
        modeled_vph = daily_rate / 24.0
        views_90d = int(view_count)
    elif days_active <= 90.0:
        # Consolidation phase (15 to 90 days)
        lifetime_daily = float(view_count) / days_active
        consolidation_decay = 0.55 - 0.30 * ((days_active - 14.0) / 76.0)
        daily_rate = max(0.5, lifetime_daily * consolidation_decay)
        modeled_vph = daily_rate / 24.0
        views_90d = int(view_count)
    elif days_active <= 365.0:
        # Mature Evergreen phase (90 to 365 days): Steady search and browse traffic
        lifetime_daily = float(view_count) / days_active
        decay_factor = 0.25 * math.pow(90.0 / days_active, 0.65)
        daily_rate = max(0.2, lifetime_daily * decay_factor)
        modeled_vph = daily_rate / 24.0
        views_90d = min(int(view_count), max(10, int(daily_rate * 90.0)))
    else:
        # Historical / Long-Tail phase (> 1 year to 10+ years):
        years_old = max(1.0, days_active / 365.25)
        lifetime_daily = float(view_count) / days_active
        retention = max(0.015, 0.12 / math.pow(years_old, 0.85))
        daily_rate = max(0.05, lifetime_daily * retention)
        modeled_vph = daily_rate / 24.0
        views_90d = min(int(view_count), max(5, int(daily_rate * 90.0)))

    # Final VPH: Prefer empirical OLS regression from snapshot window if available
    if ols_vph is not None:
        final_vph = ols_vph
        daily_rate = final_vph * 24.0
    else:
        final_vph = modeled_vph

    # 3. Traffic Projections
    lifetime_daily = float(view_count) / max(1.0, days_active)
    monthly_avg = daily_rate * 30.416
    yearly_avg = daily_rate * 365.25

    # 4. Traffic Vitality & Velocity Classification
    is_active_traffic = final_vph >= 0.5 or daily_rate >= 12.0

    if audit_detected:
        velocity_badge = "⚠️ Auditoria YouTube"
        velocity_class = "stagnant"
        vitality_desc = "Auditoria de visualizações detectada (remoção de views inválidas)."
    elif final_vph >= 50.0:
        velocity_badge = "🔥 Viral em Alta"
        velocity_class = "viral"
        vitality_desc = "Vídeo em forte aceleração de tráfego recente."
    elif final_vph >= 15.0:
        velocity_badge = "🚀 Tráfego Acelerado"
        velocity_class = "high"
        vitality_desc = "Alto volume de visualizações correntes diárias."
    elif final_vph >= 3.0:
        velocity_badge = "🟢 Tráfego Ativo (Evergreen)"
        velocity_class = "medium"
        vitality_desc = "Tráfego contínuo ativo via busca do YouTube (ótimo p/ minerar domínios)."
    elif final_vph >= 0.5:
        velocity_badge = "🟡 Tráfego Residual"
        velocity_class = "low"
        vitality_desc = "Tráfego moderado / buscas ocasionais."
    else:
        velocity_badge = "⚪ Tráfego Estagnado"
        velocity_class = "stagnant"
        vitality_desc = "Vídeo histórico com baixo tráfego recente."

    return {
        "view_count": view_count,
        "view_count_formatted": format_number(view_count),
        "days_active": int(days_active),
        "hours_active": round(hours_active, 1),
        "publish_date": date_str,
        "upload_year": upload_year,
        "views_90d": views_90d,
        "views_90d_formatted": format_number(views_90d),
        "hourly_views": round(final_vph, 2),
        "hourly_views_formatted": format_vph(final_vph),
        "daily_views": round(daily_rate, 1),
        "daily_views_formatted": f"🔥 {format_number(round(daily_rate, 1))}/dia",
        "monthly_views": round(monthly_avg, 1),
        "monthly_views_formatted": f"{format_number(round(monthly_avg, 1))}/mês",
        "yearly_views": round(yearly_avg, 1),
        "yearly_views_formatted": f"{format_number(round(yearly_avg, 1))}/ano",
        "lifetime_daily_views": round(lifetime_daily, 1),
        "velocity_badge": velocity_badge,
        "velocity_class": velocity_class,
        "vitality_desc": vitality_desc,
        "is_active_traffic": is_active_traffic,
        "audit_detected": audit_detected
    }

def format_number(num: Union[float, int, str]) -> str:
    """Format numbers into human-readable compact notation (e.g. 1.2M, 450K, 120)."""
    if num is None:
        return "0"
    try:
        n = float(num)
    except (ValueError, TypeError):
        return str(num)
        
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B".replace(".0B", "B")
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K".replace(".0K", "K")
    elif n >= 10:
        return f"{int(n)}"
    else:
        return f"{n:.1f}" if n % 1 != 0 else f"{int(n)}"
