import os, sys, json, platform, requests
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
        "\n[bold #9B59B6]███████╗██╗   ██╗██████╗     ███████╗██╗███╗   ██╗██████╗[/bold #9B59B6]\n"
        "[bold #9B59B6]██╔════╝██║   ██║██╔══██╗    ██╔════╝██║████╗  ██║██╔══██╗[/bold #9B59B6]\n"
        "[bold white]███████╗██║   ██║██████╔╝    █████╗  ██║██╔██╗ ██║██║  ██║[/bold white]\n"
        "[bold white]╚════██║██║   ██║██╔══██╗    ██╔══╝  ██║██║╚██╗██║██║  ██║[/bold white]\n"
        "[bold #9B59B6]███████║╚██████╔╝██████╔╝    ██║     ██║██║ ╚████║██████╔╝[/bold #9B59B6]\n"
        "[bold #9B59B6]╚══════╝ ╚═════╝ ╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═══╝╚═════╝ [/bold #9B59B6]\n"
        "[dim white]        Subdomain Finder By DarkoDevv v1.0[/dim white]"
    )
    console.print(Align.center(Panel(Align.center(banner_texto), border_style="#9B59B6", box=box.ROUNDED, width=75)))
def find_subdomains(domain):
    print(f"\n\033[1;35m[+] Buscando subdominios para: {domain}\033[0m")
    print("\033[2mConsultando base de datos de certificados SSL (crt.sh)...\033[0m\n")
    subdomains = set()
    try:
        url = f"https://crt.sh/?q=%25.{domain}&output=json"
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            for entry in data:
                names = entry.get("name_value", "").split("\n")
                for name in names:
                    name = name.strip().lower()
                    if name.startswith("*."): name = name[2:]
                    if name.endswith(domain) and name != domain and "*" not in name: subdomains.add(name)
        else: print(f"\033[1;31m[-] Error en el servidor (HTTP {r.status_code})\033[0m"); return
    except Exception as e: print(f"\033[1;31m[-] Error al conectar con crt.sh: {e}\033[0m"); return
    if subdomains:
        table = Table(title=f"🌐 Subdominios Encontrados ({len(subdomains)})", box=box.ROUNDED, border_style="#9B59B6", title_style="bold #9B59B6")
        table.add_column("Subdominio", style="cyan", justify="left")
        for sub in sorted(subdomains): table.add_row(sub)
        console.print(Align.center(table))
    else: print("\033[1;32m[✅] No se encontraron subdominios públicos para este dominio.\033[0m")
def menu():
    while True:
        _clear(); draw_banner()
        print("\n\033[1;35m[1]\033[0m Buscar Subdominios de un Dominio")
        print("\033[1;35m[0]\033[0m Salir\n")
        print("\033[1;35m┌──\033[0m(\033[1;35mSubdomainFinder\033[0m㉿\033[1;35m" + _get_os_name() + "\033[0m)")
        print("\033[1;35m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip(); print("\033[F\033[K", end="", flush=True)
        if choice == "0":
            _clear(); draw_banner(); print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n"); break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;35mIngresa el Dominio (ej: apple.com):\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip(); print()
            if target: find_subdomains(target); input("\nPresiona Enter para volver...")
if __name__ == "__main__": menu()
