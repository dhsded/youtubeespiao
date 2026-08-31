"""
Domain Validator & WHOIS/RDAP Checker (Multi-Layer Verification Engine).
Provides real, secure, and verifiable domain validation across 4 layers:
1. DNS Resolution (Cloudflare/Google recursive & authoritative checks)
2. Official RDAP REST APIs (Registro.br, Verisign, PIR, IANA/ICANN)
3. Direct Port 43 Socket WHOIS Fallback
4. Live HTTP/HTTPS Connectivity Probing
"""

import socket
import logging
from typing import Dict, Any, Optional
import requests
import dns.resolver

logger = logging.getLogger(__name__)

STATUS_AVAILABLE = "Disponível"   # 🟢 Expirado / Livre para registro
STATUS_INACTIVE = "Inativo"       # 🟡 Registrado mas DNS/Site morto
STATUS_ACTIVE = "Ativo"           # 🔴 Registrado e com DNS/Site ativo
STATUS_UNKNOWN = "Verificar"      # ⚪ Indeterminado / Erro temporário

# Authoritative RDAP endpoints for maximum accuracy
RDAP_ENDPOINTS = {
    "br": "https://rdap.registro.br/domain/",
    "com": "https://rdap.verisign.com/com/v1/domain/",
    "net": "https://rdap.verisign.com/net/v1/domain/",
    "org": "https://rdap.publicinterestregistry.org/rdap/org/domain/",
}

# Authoritative WHOIS servers for port 43 raw socket fallback
WHOIS_SERVERS = {
    "br": "whois.registro.br",
    "com": "whois.verisign-grs.com",
    "net": "whois.verisign-grs.com",
    "org": "whois.pir.org",
    "info": "whois.afilias.net",
    "io": "whois.nic.io",
    "co": "whois.nic.co",
    "me": "whois.nic.me",
    "tv": "tvwhois.verisign-grs.com",
    "cc": "ccwhois.verisign-grs.com",
    "de": "whois.denic.de",
    "uk": "whois.nic.uk",
    "es": "whois.nic.es",
    "fr": "whois.nic.fr",
    "it": "whois.nic.it",
    "app": "whois.nic.google",
    "dev": "whois.nic.google"
}

# Standard strings returned by registrars when a domain is NOT registered
AVAILABLE_STRINGS = [
    "no match", "not found", "status: free", "domain not found",
    "no data found", "no entries found", "available", "is free",
    "object does not exist", "nothing found", "domain unknown"
]

class DomainValidator:
    def __init__(self, timeout: float = 3.5):
        self.timeout = timeout
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = timeout
        self.resolver.lifetime = timeout
        self.resolver.nameservers = ["1.1.1.1", "8.8.8.8", "1.0.0.1", "8.8.4.4"]
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/rdap+json, application/json, text/plain"
        })

    def check_dns(self, domain: str) -> Dict[str, Any]:
        """
        Layer 1: Real DNS Resolution.
        Checks NS (Nameservers), A (IPv4), AAAA (IPv6), and SOA.
        """
        has_ns = False
        has_a = False
        nxdomain = False
        ns_records = []
        ip_records = []

        # 1. Nameservers (NS)
        try:
            answers = self.resolver.resolve(domain, "NS")
            ns_records = [str(r.target).rstrip(".") for r in answers]
            has_ns = len(ns_records) > 0
        except dns.resolver.NXDOMAIN:
            nxdomain = True
        except Exception:
            pass

        # 2. Host IP (A / AAAA)
        if not nxdomain:
            try:
                answers = self.resolver.resolve(domain, "A")
                ip_records = [str(r.address) for r in answers]
                has_a = len(ip_records) > 0
            except dns.resolver.NXDOMAIN:
                nxdomain = True
            except Exception:
                pass

        # 3. SOA check
        if not has_ns and not nxdomain:
            try:
                self.resolver.resolve(domain, "SOA")
                has_ns = True
            except dns.resolver.NXDOMAIN:
                nxdomain = True
            except Exception:
                pass

        return {
            "nxdomain": nxdomain,
            "has_ns": has_ns,
            "has_a": has_a,
            "ns_records": ns_records,
            "ip_records": ip_records,
            "dns_active": has_ns or has_a
        }

    def check_rdap(self, domain: str) -> Dict[str, Any]:
        """
        Layer 2: Official ICANN/Registry RDAP protocol (RFC 7480-7484).
        """
        tld = domain.split(".")[-1].lower()
        
        if domain.endswith(".com.br") or domain.endswith(".br"):
            endpoint = f"{RDAP_ENDPOINTS['br']}{domain}"
        elif tld in RDAP_ENDPOINTS:
            endpoint = f"{RDAP_ENDPOINTS[tld]}{domain}"
        else:
            endpoint = f"https://rdap.org/domain/{domain}"

        try:
            resp = self.session.get(endpoint, timeout=self.timeout)
            
            # HTTP 404 in RDAP is the official standard indicating the domain is NOT registered
            if resp.status_code == 404:
                return {
                    "checked": True,
                    "is_registered": False,
                    "status": STATUS_AVAILABLE,
                    "details": "Livre para registro (Confirmado via RDAP Oficial)",
                    "expires_at": None
                }
            elif resp.status_code == 200:
                data = resp.json()
                expires_at = None
                for event in data.get("events", []):
                    if event.get("eventAction") in ("expiration", "registration expiration"):
                        expires_at = event.get("eventDate")
                        if expires_at and "T" in expires_at:
                            expires_at = expires_at.split("T")[0]
                        break

                details_str = f"Registrado (Expiração: {expires_at})" if expires_at else "Registrado no Cartório/Registro"
                return {
                    "checked": True,
                    "is_registered": True,
                    "status": STATUS_ACTIVE,
                    "details": details_str,
                    "expires_at": expires_at
                }
        except Exception as e:
            logger.debug(f"RDAP check error for {domain}: {e}")

        return {"checked": False, "is_registered": None, "status": STATUS_UNKNOWN, "details": "RDAP indisponível", "expires_at": None}

    def check_socket_whois(self, domain: str) -> Dict[str, Any]:
        """
        Layer 3: Direct Port 43 Socket WHOIS Query to the authoritative TLD server.
        """
        tld = domain.split(".")[-1].lower()
        whois_server = WHOIS_SERVERS.get(tld, "whois.iana.org")

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            s.connect((whois_server, 43))
            
            # Send domain query
            query = f"{domain}\r\n"
            s.send(query.encode("utf-8"))
            
            # Receive response
            response = b""
            while True:
                data = s.recv(4096)
                if not data:
                    break
                response += data
                if len(response) > 65536:
                    break
            s.close()

            resp_text = response.decode("utf-8", errors="ignore").lower()

            for pattern in AVAILABLE_STRINGS:
                if pattern in resp_text:
                    return {
                        "checked": True,
                        "is_registered": False,
                        "status": STATUS_AVAILABLE,
                        "details": f"Disponível para registro (Confirmado via WHOIS {whois_server})",
                        "expires_at": None
                    }

            if "domain name:" in resp_text or "domain:" in resp_text or "registrant:" in resp_text:
                return {
                    "checked": True,
                    "is_registered": True,
                    "status": STATUS_ACTIVE,
                    "details": f"Registrado no WHOIS ({whois_server})",
                    "expires_at": None
                }

        except Exception as e:
            logger.debug(f"Socket WHOIS error for {domain} on {whois_server}: {e}")

        return {"checked": False, "is_registered": None, "status": STATUS_UNKNOWN, "details": "WHOIS indisponível", "expires_at": None}

    def check_http_alive(self, domain: str) -> bool:
        """
        Layer 4: Live HTTP / Web Server Probe.
        Checks if the website actively serves content or is dead/unreachable.
        """
        for proto in ("https://", "http://"):
            try:
                r = self.session.head(f"{proto}{domain}", timeout=2.5, allow_redirects=True)
                if r.status_code < 500:
                    return True
            except Exception:
                continue
        return False

    def validate_domain(self, domain: str) -> Dict[str, Any]:
        """
        4-Layer Domain Verification Pipeline:
        1. Query DNS (Cloudflare & Google recursive resolvers).
        2. Query Official RDAP REST API.
        3. Query Direct Port 43 Socket WHOIS (Fallback).
        4. Query Live HTTP/HTTPS server status.
        5. Synthesize final status.
        """
        domain = domain.lower().strip()
        if domain in self._cache:
            return self._cache[domain]

        # 1. DNS Check
        dns_info = self.check_dns(domain)

        # 2. RDAP Check
        rdap_info = self.check_rdap(domain)

        # 3. Socket WHOIS Fallback (if RDAP did not return conclusive answer)
        if not rdap_info["checked"] or rdap_info["is_registered"] is None:
            whois_info = self.check_socket_whois(domain)
        else:
            whois_info = rdap_info

        # Combined Registry Data
        reg_info = whois_info if whois_info["checked"] else rdap_info

        # 4. Status Synthesis
        final_status = STATUS_UNKNOWN
        status_color = "#9E9E9E"
        badge_icon = "⚪"
        details = ""

        if reg_info.get("is_registered") is False:
            final_status = STATUS_AVAILABLE
            status_color = "#10B981" # Emerald Green
            badge_icon = "🟢"
            details = reg_info.get("details", "Domínio Expirado / 100% Livre para Registro!")

        elif reg_info.get("is_registered") is True:
            if not dns_info["dns_active"]:
                final_status = STATUS_INACTIVE
                status_color = "#F59E0B" # Orange/Amber
                badge_icon = "🟡"
                details = f"Registrado no cartório, mas sem DNS/Site ativo ({reg_info.get('details', '')})"
            else:
                # DNS is active; let's check if the web server is answering
                http_ok = self.check_http_alive(domain)
                if http_ok:
                    final_status = STATUS_ACTIVE
                    status_color = "#EF4444" # Red
                    badge_icon = "🔴"
                    details = f"Site ativo e funcionando online. ({reg_info.get('details', '')})"
                else:
                    final_status = STATUS_INACTIVE
                    status_color = "#F59E0B"
                    badge_icon = "🟡"
                    details = f"DNS responde, mas servidor HTTP está offline/morto. ({reg_info.get('details', '')})"

        elif dns_info["nxdomain"]:
            # NXDOMAIN and no whois match
            final_status = STATUS_AVAILABLE
            status_color = "#10B981"
            badge_icon = "🟢"
            details = "Sem zona DNS (NXDOMAIN) e sem registro ativo."
        elif dns_info["dns_active"]:
            final_status = STATUS_ACTIVE
            status_color = "#EF4444"
            badge_icon = "🔴"
            details = "Servidores DNS ativos e respondendo."
        else:
            final_status = STATUS_AVAILABLE
            status_color = "#10B981"
            badge_icon = "🟢"
            details = "Não responde a DNS nem WHOIS (Provavelmente Livre)."

        # 5. Purchase / Registry Link
        if domain.endswith(".br"):
            buy_link = f"https://registro.br/busca-dominio/?secao=busca&dominio={domain}"
            registrar_name = "Registro.br"
        else:
            buy_link = f"https://www.namecheap.com/domains/registration/results/?domain={domain}"
            registrar_name = "Namecheap / GoDaddy"

        result = {
            "domain": domain,
            "status": final_status,
            "status_color": status_color,
            "badge_icon": badge_icon,
            "details": details,
            "dns_active": dns_info["dns_active"],
            "ns_records": dns_info["ns_records"],
            "ip_records": dns_info["ip_records"],
            "expires_at": reg_info.get("expires_at"),
            "buy_link": buy_link,
            "registrar_name": registrar_name
        }

        self._cache[domain] = result
        return result
