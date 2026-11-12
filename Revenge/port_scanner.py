import os, sys, platform, socket
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align
console = Console(highlight=False)
def _clear(): os.system('cls' if os.name == 'nt' else 'clear')
def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    return platform.system().lower()
def draw_banner():
    banner_texto = (
        "\n[bold #FF8C00]██████╗  ██████╗ ██████╗ ████████╗[/bold #FF8C00]\n"
        "[bold #FF8C00]██╔══██╗██╔═══██╗██╔══██╗╚══██╔══╝[/bold #FF8C00]\n"
        "[bold white]██████╔╝██║   ██║██████╔╝   ██║   [/bold white]\n"
        "[bold white]██╔═══╝ ██║   ██║██╔══██╗   ██║   [/bold white]\n"
        "[bold #FF8C00]██║     ╚██████╔╝██║  ██║   ██║   [/bold #FF8C00]\n"
        "[bold #FF8C00]╚═╝      ╚═════╝ ╚═╝  ╚═╝   ╚═╝   [/bold #FF8C00]\n"
        "[dim white]            Port Scanner By DarkoDevv v1.0[/dim white]"
    )
    console.print(Align.center(Panel(Align.center(banner_texto), border_style="#FF8C00", box=box.ROUNDED, width=75)))
COMMON_PORTS = {21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB", 1433: "MSSQL", 2082: "cPanel", 2083: "cPanel SSL", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL", 6379: "Redis", 8080: "HTTP Proxy", 8443: "HTTPS Alterno", 27017: "MongoDB"}
def scan_port(ip, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(1.5); result = s.connect_ex((ip, port)); s.close(); return port, result == 0
    except: return port, False
def run_port_scan(target):
    try: ip = socket.gethostbyname(target)
    except: print(f"\n\033[1;31m[-] No se pudo resolver el dominio: {target}\033[0m"); return
    print(f"\n\033[1;33m[+] Objetivo: {ip} ({target})\033[0m"); print("\033[2mEscaneando puertos comunes...\033[0m\n")
    open_ports = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(scan_port, ip, port) for port in COMMON_PORTS.keys()]
        for future in futures:
            port, is_open = future.result()
            if is_open: open_ports.append(port)
    if open_ports:
        table = Table(title="📡 Puertos Abiertos", box=box.ROUNDED, border_style="#FF8C00", title_style="bold #FF8C00")
        table.add_column("Puerto", style="cyan", justify="center", width=8); table.add_column("Servicio", style="white", width=15); table.add_column("Riesgo", style="red", justify="center", width=10)
        for p in sorted(open_ports):
            servicio = COMMON_PORTS.get(p, "Desconocido"); riesgo = "BAJO"
            if p in [21, 23, 445, 3306, 3389]: riesgo = "ALTO"
            elif p in [22, 80, 443]: riesgo = "MEDIO"
            table.add_row(str(p), servicio, riesgo)
        console.print(Align.center(table))
    else: print("\033[1;32m[✅] No se encontraron puertos abiertos.\033[0m")
def menu():
    while True:
        _clear(); draw_banner()
        print("\n\033[1;33m[1]\033[0m Escanear Puertos de una IP/Dominio")
        print("\033[1;33m[0]\033[0m Salir\n")
        print("\033[1;33m┌──\033[0m(\033[1;33mPortScanner\033[0m㉿\033[1;33m" + _get_os_name() + "\033[0m)")
        print("\033[1;33m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip(); print("\033[F\033[K", end="", flush=True)
        if choice == "0":
            _clear(); draw_banner(); print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n"); break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;33mIngresa la IP o Dominio:\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip(); print()
            if target: run_port_scan(target); input("\nPresiona Enter para volver...")
if __name__ == "__main__": menu()
