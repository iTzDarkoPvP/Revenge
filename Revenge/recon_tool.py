import os, sys, json, time, platform, requests
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
        "\n[bold #00FF00]██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗[/bold #00FF00]\n"
        "[bold #00FF00]██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║[/bold #00FF00]\n"
        "[bold white]██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║[/bold white]\n"
        "[bold white]██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║[/bold white]\n"
        "[bold #00FF00]██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║[/bold #00FF00]\n"
        "[bold #00FF00]╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝[/bold #00FF00]\n"
        "[dim white]       OSINT Recon Tool By DarkoDevv v1.0[/dim white]"
    )
    console.print(Align.center(Panel(Align.center(banner_texto), border_style="#00FF00", box=box.ROUNDED, width=60)))
def scan_ip(target):
    print(f"\n\033[1;36m[+] Escaneando IP/Dominio: {target}\033[0m\n")
    try:
        r = requests.get(f"http://ip-api.com/json/{target}?fields=status,message,continent,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query", timeout=10)
        data = r.json()
        if data.get("status") == "success":
            table = Table(title="🌍 Información de Red y Ubicación", box=box.ROUNDED, border_style="#00FF00", title_style="bold #00FF00")
            table.add_column("Propiedad", style="cyan"); table.add_column("Valor", style="white")
            table.add_row("IP Pública", data.get("query")); table.add_row("País", f"{data.get('country')} ({data.get('countryCode')})")
            table.add_row("Región", data.get("regionName")); table.add_row("Ciudad", data.get("city"))
            table.add_row("Zona Horaria", data.get("timezone")); table.add_row("ISP", data.get("isp"))
            table.add_row("Organización", data.get("org")); table.add_row("ASN", data.get("as"))
            table.add_row("Coordenadas", f"{data.get('lat')}, {data.get('lon')}")
            console.print(Align.center(table))
        else: print(f"\033[1;31m[-] Error al escanear IP: {data.get('message')}\033[0m"); return
    except Exception as e: print(f"\033[1;31m[-] Error de conexión: {e}\033[0m"); return
    print("\n\033[1;36m[+] Buscando en filtraciones de datos...\033[0m")
    try:
        r_spam = requests.get(f"https://api.stopforumspam.org/api?ip={target}", timeout=10)
        if "yes" in r_spam.text: print("\033[1;31m[!] ¡ALERTA! Esta IP está en la lista de SPAM de StopForumSpam.\033[0m")
        else: print("\033[1;32m[✅] La IP no está reportada en StopForumSpam.\033[0m")
    except: print("\033[1;33m[?] No se pudo verificar en StopForumSpam.\033[0m")
def menu():
    while True:
        _clear(); draw_banner()
        print("\n\033[1;32m[1]\033[0m Escanear una IP o Dominio (OSINT)")
        print("\033[1;32m[0]\033[0m Salir\n")
        print("\033[1;32m┌──\033[0m(\033[1;32mReconTool\033[0m㉿\033[1;32m" + _get_os_name() + "\033[0m)")
        print("\033[1;32m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip(); print("\033[F\033[K", end="", flush=True)
        if choice == "0":
            _clear(); draw_banner(); print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n"); break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;32mIngresa la IP o Dominio:\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip(); print()
            if target: scan_ip(target); input("\nPresiona Enter para volver...")
if __name__ == "__main__": menu()
