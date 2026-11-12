import os, sys, platform, requests, re
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
        "\n[bold #E67E22]███╗   ███╗ █████╗  ██████╗     ██╗     ██╗   ██╗[/bold #E67E22]\n"
        "[bold #E67E22]████╗ ████║██╔══██╗██╔════╝     ██║     ██║   ██║[/bold #E67E22]\n"
        "[bold white]██╔████╔██║███████║██║          ██║     ██║   ██║[/bold white]\n"
        "[bold white]██║╚██╔╝██║██╔══██║██║          ██║     ██║   ██║[/bold white]\n"
        "[bold #E67E22]██║ ╚═╝ ██║██║  ██║╚██████╗     ███████╗╚██████╔╝[/bold #E67E22]\n"
        "[bold #E67E22]╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝     ╚══════╝ ╚═════╝ [/bold #E67E22]\n"
        "[dim white]       MAC Lookup By DarkoDevv v1.0[/dim white]"
    )
    console.print(Align.center(Panel(Align.center(banner_texto), border_style="#E67E22", box=box.ROUNDED, width=60)))
def lookup_mac(mac):
    clean_mac = re.sub(r'[^A-Fa-f0-9]', '', mac).upper()
    if len(clean_mac) < 6: print("\033[1;31m[-] La dirección MAC es demasiado corta.\033[0m"); return
    oui = clean_mac[:6]
    print(f"\n\033[1;33m[+] Consultando fabricante para OUI: {oui}\033[0m\n")
    try:
        r = requests.get(f"https://api.macvendors.com/{oui}", timeout=10)
        vendor = r.text if r.status_code == 200 else ("Fabricante no encontrado" if r.status_code == 404 else f"Error HTTP {r.status_code}")
    except Exception as e: vendor = f"Error de red: {e}"
    table = Table(title="🖥️ Información del Dispositivo", box=box.ROUNDED, border_style="#E67E22", title_style="bold #E67E22")
    table.add_column("Propiedad", style="cyan", justify="right", width=15); table.add_column("Valor", style="white", justify="left", width=40)
    table.add_row("MAC Original", mac); table.add_row("OUI", oui); table.add_row("Fabricante", f"[bold green]{vendor}[/bold green]")
    console.print(Align.center(table))
def menu():
    while True:
        _clear(); draw_banner()
        print("\n\033[1;33m[1]\033[0m Buscar Fabricante por MAC Address")
        print("\033[1;33m[0]\033[0m Salir\n")
        print("\033[1;33m┌──\033[0m(\033[1;33mMACLookup\033[0m㉿\033[1;33m" + _get_os_name() + "\033[0m)")
        print("\033[1;33m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip(); print("\033[F\033[K", end="", flush=True)
        if choice == "0":
            _clear(); draw_banner(); print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n"); break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;33mIngresa la MAC Address (ej: A4:C3:F0:12:34:56):\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip(); print()
            if target: lookup_mac(target); input("\nPresiona Enter para volver...")
if __name__ == "__main__": menu()
