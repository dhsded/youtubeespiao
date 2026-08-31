"""
Metrics Calculator for YouTube Video Performance.
Calculates hourly, daily, monthly, and yearly view averages based on publish date and view count.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union

def calculate_video_metrics(
    view_count: int,
    upload_date: Optional[Union[str, datetime]] = None,
    timestamp: Optional[int] = None,
    published_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate performance metrics for a YouTube video:
    - Hourly average views (Views/hora)
    - Daily average views (Views/dia)
    - Monthly average views (Views/mês)
    - Yearly average views (Views/ano)
    """
    now = datetime.now(timezone.utc)
    pub_dt = None

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

    if not pub_dt:
        days_active = 30.0
        date_str = published_text.strip().capitalize() if published_text else "Recente"
    else:
        diff = (now - pub_dt).total_seconds() / 86400.0
        days_active = max(0.04, diff) # At least 1 hour (0.04 days)
        date_str = pub_dt.strftime("%d/%m/%Y")

    hours_active = max(1.0, days_active * 24.0)
    hourly_avg = float(view_count) / hours_active
    daily_avg = float(view_count) / max(1.0, days_active)
    monthly_avg = daily_avg * 30.416
    yearly_avg = daily_avg * 365.25

    # Velocity / Rating
    if hourly_avg >= 200:
        velocity_badge = "🔥 Super Viral"
        velocity_class = "viral"
    elif hourly_avg >= 40:
        velocity_badge = "🚀 Alto Tráfego"
        velocity_class = "high"
    elif hourly_avg >= 5:
        velocity_badge = "📈 Constante"
        velocity_class = "medium"
    else:
        velocity_badge = "💤 Moderado"
        velocity_class = "low"

    return {
        "view_count": view_count,
        "view_count_formatted": format_number(view_count),
        "days_active": int(days_active),
        "hours_active": round(hours_active, 1),
        "publish_date": date_str,
        "hourly_views": round(hourly_avg, 2),
        "hourly_views_formatted": f"{format_number(round(hourly_avg, 1))}/h",
        "daily_views": round(daily_avg, 1),
        "daily_views_formatted": f"{format_number(round(daily_avg, 1))}/dia",
        "monthly_views": round(monthly_avg, 1),
        "monthly_views_formatted": f"{format_number(round(monthly_avg, 1))}/mês",
        "yearly_views": round(yearly_avg, 1),
        "yearly_views_formatted": f"{format_number(round(yearly_avg, 1))}/ano",
        "velocity_badge": velocity_badge,
        "velocity_class": velocity_class
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
