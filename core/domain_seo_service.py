import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone
import requests
import dns.resolver
from urllib.parse import quote

logger = logging.getLogger(__name__)

def _get_api_keys_path() -> str:
    appdata = os.getenv('APPDATA') or os.path.expanduser('~')
    return os.path.join(appdata, 'YouTubeEspiao', 'api_keys.json')

def load_api_key(key_name: str) -> str:
    path = _get_api_keys_path()
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(key_name, '')
        except Exception as e:
            logger.error(f"Erro ao carregar chave de API {key_name}: {e}")
    return ''

def save_api_key(key_name: str, value: str):
    path = _get_api_keys_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {}
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data[key_name] = value
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Erro ao salvar chave de API {key_name}: {e}")

class DomainSEOService:
    def __init__(self):
        self.opr_api_key = load_api_key('open_pagerank_key')
        self._is_stopped = False
    
    def stop(self):
        self._is_stopped = True
    
    def set_api_key(self, key: str):
        self.opr_api_key = key
        save_api_key('open_pagerank_key', key)
    
    def analyze_domain(self, root_domain: str) -> Dict[str, Any]:
        """Analisa um único domínio e retorna um dicionário de métricas."""
        logger.info(f"Iniciando análise do domínio: {root_domain}")
        metrics = {
            'domain': root_domain,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }

        if self._is_stopped:
            return metrics

        # 1. Open PageRank
        opr_data = self._fetch_open_pagerank([root_domain])
        if root_domain in opr_data:
            metrics.update(opr_data[root_domain])
        else:
            # Fallback values if API fails
            metrics.update({
                'domain_authority': 0,
                'page_rank': 0.0,
                'referring_domains': 0
            })

        if self._is_stopped:
            return metrics

        # 2. RDAP
        rdap_data = self._fetch_rdap_info(root_domain)
        metrics.update(rdap_data)

        if self._is_stopped:
            return metrics

        # 3. Wayback Machine
        wayback_data = self._fetch_wayback_history(root_domain)
        metrics.update(wayback_data)

        if self._is_stopped:
            return metrics

        # 4. DNS Metrics
        dns_data = self._fetch_dns_metrics(root_domain)
        metrics.update(dns_data)

        # Compute Score
        score_data = self._compute_seo_score(metrics)
        metrics.update(score_data)

        return metrics
    
    def _fetch_open_pagerank(self, domains: List[str]) -> Dict[str, Dict]:
        if not self.opr_api_key:
            logger.warning("Chave da API Open PageRank não configurada.")
            return {}

        results = {}
        # Try to use the endpoint requested by user:
        try:
            url = "https://openpagerank.keywordseverywhere.com/v1/domains/bulk"
            headers = {
                'Authorization': f'Bearer {self.opr_api_key}',
                'Content-Type': 'application/json'
            }
            payload = {"domains": domains}
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    domain = item.get('domain')
                    da = float(item.get('domain_authority', 0) or 0)
                    pr = float(item.get('page_rank_decimal', 0) or 0)
                    ref = int(item.get('referring_domain_count', 0) or 0)
                    results[domain] = {
                        'domain_authority': da,
                        'page_rank': pr,
                        'referring_domains': ref
                    }
            else:
                logger.error(f"Erro na API Open PageRank (KeywordsEverywhere): HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Exceção ao acessar API de KeywordsEverywhere: {e}")

        return results
    
    def _fetch_rdap_info(self, domain: str) -> Dict[str, Any]:
        result = {
            'creation_date': 'N/A',
            'expiration_date': 'N/A',
            'age_days': 0,
            'age_formatted': 'N/A',
            'registrar': 'N/A'
        }
        try:
            url = f"https://rdap.org/domain/{domain}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # entities -> registrar
                entities = data.get('entities', [])
                for entity in entities:
                    if 'registrar' in entity.get('roles', []):
                        vcard = entity.get('vcardArray', [])
                        if len(vcard) > 1:
                            for prop in vcard[1]:
                                if prop[0] == 'fn':
                                    result['registrar'] = prop[3]

                events = data.get('events', [])
                creation_dt = None
                for event in events:
                    action = event.get('eventAction')
                    date_str = event.get('eventDate')
                    if not date_str:
                        continue
                    
                    try:
                        # RDAP dates are usually ISO 8601 like 2018-03-15T00:00:00Z
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        formatted_date = dt.strftime('%d/%m/%Y')
                        
                        if action == 'registration':
                            result['creation_date'] = formatted_date
                            creation_dt = dt
                        elif action == 'expiration':
                            result['expiration_date'] = formatted_date
                    except ValueError:
                        pass
                
                if creation_dt:
                    now = datetime.now(timezone.utc)
                    delta = now - creation_dt
                    result['age_days'] = delta.days
                    years = delta.days // 365
                    months = (delta.days % 365) // 30
                    if years > 0:
                        result['age_formatted'] = f"{years} anos, {months} meses"
                    else:
                        result['age_formatted'] = f"{months} meses"

        except Exception as e:
            logger.error(f"Erro ao buscar RDAP para {domain}: {e}")
        
        return result
    
    def _fetch_wayback_history(self, domain: str) -> Dict[str, Any]:
        result = {
            'wayback_first_date': 'N/A',
            'wayback_total_snapshots': 0,
            'wayback_years_active': 0,
            'wayback_url': 'N/A'
        }
        try:
            # 1. Total snapshots
            count_url = f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json&collapse=urlkey"
            resp = requests.get(count_url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1: # first is header
                    # Usando collapse=urlkey, o Wayback Archive retorna apenas 1 registro se todos forem agrupados.
                    # Mas podemos buscar contagem total se fizermos a query de forma diferente, ou buscar sem limit.
                    # Como não há suporte fácil para contagem total sem puxar tudo, puxamos apenas os campos essenciais.
                    count_resp = requests.get(f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json&fl=timestamp", timeout=10)
                    if count_resp.status_code == 200:
                        count_data = count_resp.json()
                        result['wayback_total_snapshots'] = max(0, len(count_data) - 1)

            # 2. Oldest snapshot
            oldest_url = f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json&limit=1&fl=timestamp,statuscode&filter=statuscode:200"
            resp_oldest = requests.get(oldest_url, timeout=5)
            if resp_oldest.status_code == 200:
                data_oldest = resp_oldest.json()
                if len(data_oldest) > 1: # row 0 is header, row 1 is data
                    ts = data_oldest[1][0]
                    # ts format: 20180501123456
                    if len(ts) >= 8:
                        year = int(ts[0:4])
                        month = int(ts[4:6])
                        day = int(ts[6:8])
                        result['wayback_first_date'] = f"{day:02d}/{month:02d}/{year:04d}"
                        
                        current_year = datetime.now().year
                        result['wayback_years_active'] = current_year - year
                        result['wayback_url'] = f"https://web.archive.org/web/{ts}/https://{domain}"

            time.sleep(0.5)
        except Exception as e:
            logger.error(f"Erro ao buscar Wayback Machine para {domain}: {e}")
        
        return result
    
    def _fetch_dns_metrics(self, domain: str) -> Dict[str, Any]:
        result = {
            'dns_a_records': [],
            'dns_mx_records': [],
            'dns_ns_records': [],
            'dns_total_records': 0,
            'has_email': False,
            'has_nameservers': False
        }
        
        total = 0
        
        # A records
        try:
            answers = dns.resolver.resolve(domain, 'A', lifetime=3)
            for rdata in answers:
                result['dns_a_records'].append(rdata.to_text())
                total += 1
        except Exception:
            pass
            
        # MX records
        try:
            answers = dns.resolver.resolve(domain, 'MX', lifetime=3)
            for rdata in answers:
                result['dns_mx_records'].append(rdata.to_text())
                total += 1
            if len(result['dns_mx_records']) > 0:
                result['has_email'] = True
        except Exception:
            pass

        # NS records
        try:
            answers = dns.resolver.resolve(domain, 'NS', lifetime=3)
            for rdata in answers:
                result['dns_ns_records'].append(rdata.to_text())
                total += 1
            if len(result['dns_ns_records']) > 0:
                result['has_nameservers'] = True
        except Exception:
            pass
            
        result['dns_total_records'] = total
        return result
    
    def _compute_seo_score(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        # DA * 0.35
        da = metrics.get('domain_authority', 0)
        # PageRank * 10 * 0.15
        pr = metrics.get('page_rank', 0.0)
        # min(referring_domains/100, 20) * 0.20
        ref = metrics.get('referring_domains', 0)
        # min(age_years, 10) * 2 * 0.15
        age_days = metrics.get('age_days', 0)
        age_years = age_days / 365.0
        # min(snapshots/100, 15) * 0.15
        snaps = metrics.get('wayback_total_snapshots', 0)
        
        c1 = da * 0.35
        c2 = pr * 10 * 0.15
        c3 = min(ref / 100.0, 20) * 0.20
        c4 = min(age_years, 10) * 2.0 * 0.15
        c5 = min(snaps / 100.0, 15) * 0.15
        
        score = c1 + c2 + c3 + c4 + c5
        # normalize to 0-100
        score = max(0, min(100, int(round(score))))
        
        grade = 'F'
        verdict = 'Sem Relevância SEO'
        if score >= 80:
            grade = 'A'
            verdict = 'Excelente Oportunidade'
        elif score >= 60:
            grade = 'B'
            verdict = 'Boa Oportunidade'
        elif score >= 40:
            grade = 'C'
            verdict = 'Oportunidade Moderada'
        elif score >= 20:
            grade = 'D'
            verdict = 'Baixo Potencial'
            
        base_val = 10
        if da > 30:
            base_val += da * 50
        if ref > 100:
            base_val += ref * 2
        if age_years > 3:
            base_val += int(age_years) * 100
        if snaps > 500:
            base_val += 500
            
        return {
            'seo_score': score,
            'seo_grade': grade,
            'seo_verdict': verdict,
            'estimated_value_usd': base_val
        }
    
    def bulk_analyze(self, domains: List[str], on_progress: Optional[Callable] = None) -> List[Dict[str, Any]]:
        self._is_stopped = False
        results = []
        total = len(domains)
        
        # Batch requests to OPR for efficiency (100 domains max per request)
        batch_size = 100
        opr_results = {}
        for i in range(0, total, batch_size):
            if self._is_stopped:
                break
            batch = domains[i:i+batch_size]
            batch_opr = self._fetch_open_pagerank(batch)
            opr_results.update(batch_opr)
            time.sleep(1) # rate limit
            
        for idx, domain in enumerate(domains):
            if self._is_stopped:
                break
                
            metrics = {
                'domain': domain,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Apply OPR cache
            if domain in opr_results:
                metrics.update(opr_results[domain])
            else:
                metrics.update({
                    'domain_authority': 0,
                    'page_rank': 0.0,
                    'referring_domains': 0
                })
                
            metrics.update(self._fetch_rdap_info(domain))
            if self._is_stopped: break
            
            metrics.update(self._fetch_wayback_history(domain))
            if self._is_stopped: break
            
            metrics.update(self._fetch_dns_metrics(domain))
            
            score_data = self._compute_seo_score(metrics)
            metrics.update(score_data)
            
            results.append(metrics)
            
            if on_progress:
                on_progress(idx + 1, total, domain)
                
            time.sleep(1) # Rate limit entre domínios para RDAP/Wayback
            
        return results
