import os, sys, platform, socket, ssl, time
import requests
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align
console = Console(highlight=False)
MG = "#00FF41"; MGD = "#008F11"; MGD2 = "#003B00"
def _clear(): os.system('cls' if os.name == 'nt' else 'clear')
def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    return platform.system().lower()
def draw_banner():
    banner_texto = (
        f"\n[bold {MG}]██╗    ██╗██╗  ██╗ ██████╗ ██╗███████╗[/bold {MG}]\n"
        f"[bold {MG}]██║    ██║██║  ██║██╔═══██╗██║██╔════╝[/bold {MG}]\n"
        f"[bold {MG}]██║ █╗ ██║███████║██║   ██║██║███████╗[/bold {MG}]\n"
        f"[bold {MGD}]██║███╗██║██╔══██║██║   ██║██║╚════██║[/bold {MGD}]\n"
        f"[bold {MGD}]╚███╔███╔╝██║  ██║╚██████╔╝██║███████║[/bold {MGD}]\n"
        f"[bold {MGD2}] ╚══╝╚══╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝[/bold {MGD2}]\n"
        f"\n[dim {MG}]  WHOIS / RECON Toolkit By DarkoDevv v1.0  [/dim {MG}]"
    )
    panel = Panel(Align.center(banner_texto, vertical="middle"), border_style=MG, box=box.ROUNDED, width=62, padding=(0, 1))
    console.print(Align.center(panel))
def whois_lookup(target):
    print(f"\n\033[1;32m[+] Consultando WHOIS: {target}\033[0m\n")
    try:
        partes = target.replace("https://", "").replace("http://", "").split("/")[0].split(".")
        dominio_raiz = ".".join(partes[-2:]) if len(partes) > 2 else target
        if dominio_raiz != target: print(f"\033[2m[*] Extrayendo dominio raíz: {dominio_raiz}\033[0m\n")
        r = requests.get(f"https://rdap.org/domain/{dominio_raiz}", timeout=20, headers={"Accept": "application/rdap+json"})
        if r.status_code != 200: print(f"\033[1;31m[-] No se pudo obtener WHOIS para '{dominio_raiz}' (HTTP {r.status_code})\033[0m"); return
        d = r.json()
        table = Table(title=f"📋 WHOIS de {dominio_raiz}", box=box.ROUNDED, border_style=MG, title_style=f"bold {MG}", header_style=f"bold {MG}")
        table.add_column("Campo", style=MG, justify="left", width=18, no_wrap=True); table.add_column("Valor", style="white", justify="left", width=42)
        table.add_row("Dominio", d.get("ldhName", dominio_raiz)); table.add_row("Handle", d.get("handle", "N/A")); table.add_row("Estado", ", ".join(d.get("status", ["N/A"])))
        for ev in d.get("events", []):
            act = ev.get("eventAction", "").capitalize()
            if act in ("Registration", "Expiration", "Last changed", "Last update of rdap database"): table.add_row(f"Fecha {act}", ev.get("eventDate", "N/A"))
        ns = [n.get("ldhName", "") for n in d.get("nameservers", [])]; table.add_row("Nameservers", "\n".join(ns) if ns else "N/A")
        for ent in d.get("entities", []):
            if "registrar" in ent.get("roles", []):
                vcard = ent.get("vcardArray", [[], []])[1]; nombre = "N/A"
                for item in vcard:
                    if item[0] == "fn": nombre = item[3]; break
                table.add_row("Registrar", nombre); break
        console.print(Align.center(table))
        for ent in d.get("entities", []):
            if "registrant" in ent.get("roles", []):
                vcard = ent.get("vcardArray", [[], []])[1]; info = {}
                for item in vcard:
                    if item[0] == "fn": info["Nombre"] = item[3]
                    if item[0] == "adr": info["Dirección"] = " ".join(str(x) for x in item[3] if x)
                    if item[0] == "email": info["Email"] = item[3]
                if info:
                    t2 = Table(title="👤 Registrante", box=box.ROUNDED, border_style=MG, title_style=f"bold {MG}", header_style=f"bold {MG}")
                    t2.add_column("Campo", style=MG, justify="left", no_wrap=True); t2.add_column("Valor", style="white", justify="left")
                    for k, v in info.items(): t2.add_row(k, str(v))
                    console.print(Align.center(t2))
                break
    except Exception as e: print(f"\033[1;31m[-] Error: {e}\033[0m")
def web_tech_detector(url):
    if not url.startswith(("http://", "https://")): url = "https://" + url
    print(f"\n\033[1;32m[+] Detectando tecnologías en: {url}\033[0m\n")
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        headers = r.headers; html = r.text.lower(); techs = []
        if "server" in headers: techs.append(("Web Server", headers["server"]))
        if "x-powered-by" in headers: techs.append(("Backend", headers["x-powered-by"]))
        firmas = {"WordPress": ["wp-content", "wp-includes"],"Drupal": ["drupal.js", "sites/default/files"],"Joomla": ["/media/system/js/", "joomla"],"Shopify": ["cdn.shopify.com", "shopify"],"Wix": ["wix.com", "wixstatic"],"React": ["_next/static", "react"],"Vue.js": ["vue.js", "vue.min.js"],"Angular": ["ng-version", "angular"],"Bootstrap": ["bootstrap.min.css", "bootstrap.css"],"jQuery": ["jquery.min.js", "jquery.js"],"Tailwind": ["tailwind"],"Cloudflare": ["cloudflare"],"Google Analytics": ["google-analytics", "gtag("],"Font Awesome": ["font-awesome", "fontawesome"]}
        for nombre, patrones in firmas.items():
            if any(p in html for p in patrones): techs.append(("Frontend/CMS", nombre))
        cookies_detect = {"PHPSESSID": "PHP", "JSESSIONID": "Java","ASP.NET_SessionId": "ASP.NET", "csrftoken": "Django","laravel_session": "Laravel"}
        for c in r.cookies:
            if c.name in cookies_detect: techs.append(("Framework", cookies_detect[c.name]))
        table = Table(title=f"🧩 Tecnologías en {url}", box=box.ROUNDED, border_style=MG, title_style=f"bold {MG}", header_style=f"bold {MG}")
        table.add_column("Categoría", style=MG, justify="left", width=18, no_wrap=True); table.add_column("Tecnología", style="white", justify="left", width=42)
        if techs:
            vistos = set()
            for cat, t in techs:
                if (cat, t) not in vistos: table.add_row(cat, t); vistos.add((cat, t))
        else: table.add_row("—", "No se detectaron tecnologías")
        console.print(Align.center(table)); print(f"\033[1;32m🌐 Status HTTP: {r.status_code}\033[0m")
    except Exception as e: print(f"\033[1;31m[-] Error: {e}\033[0m")
def http_headers(url):
    if not url.startswith(("http://", "https://")): url = "https://" + url
    print(f"\n\033[1;32m[+] Analizando headers de: {url}\033[0m\n")
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"}); headers = r.headers
        table = Table(title="📨 Headers HTTP", box=box.ROUNDED, border_style=MG, title_style=f"bold {MG}", header_style=f"bold {MG}")
        table.add_column("Header", style=MG, justify="left", width=26, no_wrap=True); table.add_column("Valor", style="white", justify="left", width=50)
        for k, v in headers.items(): table.add_row(k, v)
        console.print(Align.center(table))
        sec = {"Strict-Transport-Security": "HSTS","Content-Security-Policy": "CSP","X-Frame-Options": "Anti-Clickjacking","X-Content-Type-Options": "Anti-MIME-Sniffing","Referrer-Policy": "Referrer Policy","Permissions-Policy": "Permissions Policy","X-XSS-Protection": "XSS Protection"}
        t2 = Table(title="🛡️ Headers de Seguridad", box=box.ROUNDED, border_style=MG, title_style=f"bold {MG}", header_style=f"bold {MG}")
        t2.add_column("Header", style=MG, justify="left", width=26, no_wrap=True); t2.add_column("Estado", justify="left", width=40)
        for h, desc in sec.items():
            if h in headers: t2.add_row(h, f"[green]✓ Presente[/green] ({desc})")
            else: t2.add_row(h, f"[red]✗ Ausente[/red] ({desc})")
        console.print(Align.center(t2))
    except Exception as e: print(f"\033[1;31m[-] Error: {e}\033[0m")
def ssl_checker(dominio):
    print(f"\n\033[1;32m[+] Consultando certificado SSL de: {dominio}\033[0m\n")
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=dominio) as s:
            s.settimeout(15); s.connect((dominio, 443)); cert = s.getpeercert(); tls_version = s.version()
        table = Table(title=f"🔒 Certificado SSL de {dominio}", box=box.ROUNDED, border_style=MG, title_style=f"bold {MG}", header_style=f"bold {MG}")
        table.add_column("Campo", style=MG, justify="left", width=18, no_wrap=True); table.add_column("Valor", style="white", justify="left", width=42)
        subj = {k: v for tup in cert.get("subject", ()) for k, v in tup}
        table.add_row("Common Name", subj.get("commonName", "N/A")); table.add_row("Organización", subj.get("organizationName", "N/A")); table.add_row("País", subj.get("countryName", "N/A"))
        iss = {k: v for tup in cert.get("issuer", ()) for k, v in tup}
        table.add_row("Emisor", iss.get("commonName", "N/A")); table.add_row("Org. Emisora", iss.get("organizationName", "N/A"))
        not_before = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z"); not_after  = datetime.strptime(cert["notAfter"],  "%b %d %H:%M:%S %Y %Z")
        dias = (not_after - datetime.now(timezone.utc).replace(tzinfo=None)).days; color = "green" if dias > 30 else ("yellow" if dias > 7 else "red")
        table.add_row("Válido desde", not_before.strftime("%Y-%m-%d %H:%M")); table.add_row("Válido hasta", not_after.strftime("%Y-%m-%d %H:%M")); table.add_row("Días restantes", f"[{color}]{dias}[/{color}]")
        sans = [v for k, v in cert.get("subjectAltName", ())]; table.add_row("Dominios (SAN)", "\n".join(sans) if sans else "N/A"); table.add_row("Versión TLS", tls_version)
        console.print(Align.center(table))
    except ssl.SSLCertVerificationError as e: print(f"\033[1;31m[-] Certificado inválido: {e}\033[0m")
    except Exception as e: print(f"\033[1;31m[-] Error: {e}\033[0m")
def menu():
    while True:
        _clear(); draw_banner()
        print(f"\n\033[1;32m[1]\033[0m WHOIS de un dominio"); print(f"\033[1;32m[2]\033[0m Detector de Tecnologías Web")
        print(f"\033[1;32m[3]\033[0m Analizador de Headers HTTP"); print(f"\033[1;32m[4]\033[0m Checker SSL/TLS"); print(f"\033[1;32m[0]\033[0m Salir\n")
        print(f"\033[1;32m┌──\033[0m(\033[1;32mWhois\033[0m㉿\033[1;32m{_get_os_name()}\033[0m)"); print(f"\033[1;32m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip(); print("\033[F\033[K", end="", flush=True)
        if choice == "0":
            _clear(); draw_banner(); print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n"); break
        elif choice == "1":
            _clear(); draw_banner(); print("\n\033[1;32mIngresa el dominio (ej: example.com):\033[0m ", end="", flush=True)
            t = sys.stdin.readline().strip()
            if t: print(); whois_lookup(t); input("\nPresiona Enter para volver...")
        elif choice == "2":
            _clear(); draw_banner(); print("\n\033[1;32mIngresa la URL o dominio:\033[0m ", end="", flush=True)
            t = sys.stdin.readline().strip()
            if t: print(); web_tech_detector(t); input("\nPresiona Enter para volver...")
        elif choice == "3":
            _clear(); draw_banner(); print("\n\033[1;32mIngresa la URL o dominio:\033[0m ", end="", flush=True)
            t = sys.stdin.readline().strip()
            if t: print(); http_headers(t); input("\nPresiona Enter para volver...")
        elif choice == "4":
            _clear(); draw_banner(); print("\n\033[1;32mIngresa el dominio (sin https://):\033[0m ", end="", flush=True)
            t = sys.stdin.readline().strip().replace("https://", "").replace("http://", "").split("/")[0]
            if t: print(); ssl_checker(t); input("\nPresiona Enter para volver...")
        else: print("\033[1;31mOpción inválida.\033[0m"); time.sleep(1)
if __name__ == "__main__": menu()
