import os, sys, platform, socket, time
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align

try:
    import requests
except ImportError:
    print("\033[1;31m[-] Falta 'requests'. Instala: pip install requests\033[0m")
    sys.exit(1)

console = Console(highlight=False)

C1 = "#00FFFF"
C2 = "#0080FF"
C3 = "#00008B"

def _clear(): os.system('cls' if os.name == 'nt' else 'clear')

def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    if os.name == "nt": return "powershell" if "PS" in os.environ.get("PROMPT", "") else "cmd"
    return platform.system().lower()

def draw_banner():
    banner_texto = (
        f"\n[bold {C1}]██████╗ ███████╗██████╗ ███████╗[/bold {C1}]\n"
        f"[bold {C1}]██╔══██╗██╔════╝██╔══██╗██╔════╝[/bold {C1}]\n"
        f"[bold {C2}]██████╔╝█████╗  ██║  ██║█████╗  [/bold {C2}]\n"
        f"[bold {C2}]██╔══██╗██╔══╝  ██║  ██║██╔══╝  [/bold {C2}]\n"
        f"[bold {C3}]██║  ██║███████╗██████╔╝███████╗[/bold {C3}]\n"
        f"[bold {C3}]╚═╝  ╚═╝╚══════╝╚═════╝ ╚══════╝[/bold {C3}]\n"
        f"\n[dim {C1}]Net/Infra Toolkit By DarkoDevv v1.0[/dim {C1}]"
    )
    panel = Panel(
        Align.center(banner_texto, vertical="middle"),
        border_style=C1, box=box.ROUNDED, width=55, padding=(0, 1)
    )
    console.print(Align.center(panel))

def traceroute(target, max_hops=30):
    print(f"\n\033[1;36m[+] Traceroute hacia: {target}\033[0m\n")
    try:
        dest_ip = socket.gethostbyname(target)
    except socket.gaierror:
        print("\033[1;31m[-] No se pudo resolver el dominio.\033[0m")
        return

    print(f"\033[2mIP Destino: {dest_ip} | Max Hops: {max_hops}\033[0m\n")
    
    table = Table(title=f"🗺️ Ruta hacia {dest_ip}", box=box.ROUNDED, border_style=C1, title_style=f"bold {C1}", header_style=f"bold {C1}")
    table.add_column("Hop", style=C1, justify="center", width=6)
    table.add_column("IP", style="white", justify="left", width=18)
    table.add_column("Latencia", style="green", justify="right", width=10)

    for ttl in range(1, max_hops + 1):
        icmp = socket.getprotobyname("icmp")
        try:
            recv_socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        except PermissionError:
            print("\033[1;31m[-] Se requieren permisos de root (sudo) para traceroute nativo.\033[0m")
            return
            
        send_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        recv_socket.settimeout(2)
        send_socket.setsockopt(socket.SOL_IP, socket.IP_TTL, ttl)
        
        start_time = time.time()
        send_socket.sendto(b"", (dest_ip, 33434))
        
        try:
            _, curr_addr = recv_socket.recvfrom(512)
            curr_addr = curr_addr[0]
            elapsed = (time.time() - start_time) * 1000
            table.add_row(str(ttl), curr_addr, f"{elapsed:.1f} ms")
        except socket.timeout:
            table.add_row(str(ttl), "*", "Timeout")
        finally:
            send_socket.close()
            recv_socket.close()

        if curr_addr == dest_ip:
            break
            
    console.print(Align.center(table))

def grab_banner(target, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        s.connect((target, port))
        if port in (80, 443, 8080, 8443):
            s.sendall(b"HEAD / HTTP/1.1\r\nHost: " + target.encode() + b"\r\n\r\n")
        banner = s.recv(1024).decode('utf-8', errors='ignore').strip()
        s.close()
        return banner
    except Exception:
        return None

def run_banner_grab(target):
    print(f"\n\033[1;36m[+] Banner Grab hacia: {target}\033[0m\n")
    ports = {21: "FTP", 22: "SSH", 25: "SMTP", 80: "HTTP", 443: "HTTPS", 3306: "MySQL", 8080: "HTTP-Alt"}
    
    table = Table(title=f"📡 Banners de {target}", box=box.ROUNDED, border_style=C1, title_style=f"bold {C1}", header_style=f"bold {C1}")
    table.add_column("Puerto", style=C1, justify="center", width=8)
    table.add_column("Servicio", style="cyan", justify="center", width=12)
    table.add_column("Banner (Primera línea)", style="white", justify="left", width=45)

    for port, service in ports.items():
        banner = grab_banner(target, port)
        if banner:
            first_line = banner.split('\n')[0][:45]
            table.add_row(str(port), service, first_line)
        else:
            table.add_row(str(port), service, "[dim]Sin respuesta / Cerrado[/dim]")
            
    console.print(Align.center(table))

def check_http_methods(target):
    if not target.startswith(("http://", "https://")):
        target = "https://" + target
    print(f"\n\033[1;36m[+] Auditando métodos HTTP en: {target}\033[0m\n")
    
    methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "TRACE", "HEAD"]
    table = Table(title="Métodos HTTP Permitidos", box=box.ROUNDED, border_style=C1, title_style=f"bold {C1}", header_style=f"bold {C1}")
    table.add_column("Método", style=C1, justify="center", width=10)
    table.add_column("Status", justify="center", width=10)
    table.add_column("Allow Header", style="white", justify="left", width=30)

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r_opt = requests.options(target, headers=headers, timeout=10)
        allow = r_opt.headers.get("Allow", "No especificado")
        
        for m in methods:
            try:
                r = requests.request(m, target, headers=headers, timeout=5)
                color = "green" if r.status_code < 400 else "red"
                table.add_row(m, f"[{color}]{r.status_code}[/{color}]", allow if m == "OPTIONS" else "-")
            except:
                table.add_row(m, "[red]Error[/red]", "-")
                
        console.print(Align.center(table))
    except Exception as e:
        print(f"\033[1;31m[-] Error: {e}\033[0m")

def detect_waf(target):
    if not target.startswith(("http://", "https://")):
        target = "https://" + target
    print(f"\n\033[1;36m[+] Detectando WAF en: {target}\033[0m\n")
    
    payload = f"{target}/?id=1' UNION SELECT 1,2,3-- -"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    wafs = {
        "Cloudflare": ["cloudflare", "cf-ray", "__cfduid"],
        "Akamai": ["akamai", "akamaighost"],
        "Sucuri": ["sucuri", "x-sucuri-id"],
        "Imperva": ["imperva", "incap_ses"],
        "F5 BIG-IP": ["big-ip", "tscookie"],
        "AWS WAF": ["awselb", "aws-waf"],
        "ModSecurity": ["mod_security", "modsecurity"]
    }
    
    detected = []
    
    try:
        r = requests.get(payload, headers=headers, timeout=10)
        resp_headers = str(r.headers).lower()
        resp_body = r.text.lower()
        
        for waf, sigs in wafs.items():
            for sig in sigs:
                if sig in resp_headers or sig in resp_body:
                    detected.append(waf)
                    break
                    
        if r.status_code in (403, 406, 501):
            detected.append("Posible WAF (Bloqueo de Payload)")
            
        table = Table(title="Escudo / WAF Detectado", box=box.ROUNDED, border_style=C1, title_style=f"bold {C1}", header_style=f"bold {C1}")
        table.add_column("WAF / Firewall", style="red", justify="center", width=28)
        
        if detected:
            for d in set(detected):
                table.add_row(f"🛡️ {d}")
            console.print(Align.center(table))
        else:
            print("\033[1;32m[✅] No se detectó WAF obvio ni bloqueo de payload.\033[0m")
            
    except Exception as e:
        print(f"\033[1;31m[-] Error: {e}\033[0m")

def menu():
    os_name = _get_os_name()
    while True:
        _clear()
        draw_banner()
        print(f"\n\033[1;36m[1]\033[0m Traceroute (Ruta de red)")
        print(f"\033[1;36m[2]\033[0m Banner Grabber (Capturar servicios)")
        print(f"\033[1;36m[3]\033[0m HTTP Methods (Auditar verbos)")
        print(f"\033[1;36m[4]\033[0m WAF Detector (Firewalls)")
        print(f"\033[1;36m[0]\033[0m Salir\n")
        
        print(f"\033[1;36m┌──\033[0m(\033[1;36mNetInfra\033[0m㉿\033[1;36m{os_name}\033[0m)")
        print(f"\033[1;36m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)

        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear()
            draw_banner()
            print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n")
            break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;36mIngresa IP o Dominio (requiere root/sudo):\033[0m ", end="", flush=True)
            t = sys.stdin.readline().strip()
            if t:
                traceroute(t)
                input("\nPresiona Enter para volver...")
        elif choice == "2":
            _clear(); draw_banner()
            print("\n\033[1;36mIngresa IP o Dominio:\033[0m ", end="", flush=True)
            t = sys.stdin.readline().strip()
            if t:
                run_banner_grab(t)
                input("\nPresiona Enter para volver...")
        elif choice == "3":
            _clear(); draw_banner()
            print("\n\033[1;36mIngresa la URL o Dominio:\033[0m ", end="", flush=True)
            t = sys.stdin.readline().strip()
            if t:
                check_http_methods(t)
                input("\nPresiona Enter para volver...")
        elif choice == "4":
            _clear(); draw_banner()
            print("\n\033[1;36mIngresa la URL o Dominio:\033[0m ", end="", flush=True)
            t = sys.stdin.readline().strip()
            if t:
                detect_waf(t)
                input("\nPresiona Enter para volver...")
        else:
            print("\033[1;31mOpción inválida.\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    menu()
