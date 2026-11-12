import os, sys, platform, requests
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
        "\n[bold #2ECC71]██╗   ██╗██████╗ ██╗         ███████╗██╗  ██╗██████╗ [/bold #2ECC71]\n"
        "[bold #2ECC71]██║   ██║██╔══██╗██║         ██╔════╝╚██╗██╔╝██╔══██╗[/bold #2ECC71]\n"
        "[bold white]██║   ██║██████╔╝██║         █████╗   ╚███╔╝ ██████╔╝[/bold white]\n"
        "[bold white]██║   ██║██╔══██╗██║         ██╔══╝   ██╔██╗ ██╔═══╝ [/bold white]\n"
        "[bold #2ECC71]╚██████╔╝██║  ██║███████╗    ███████╗██╔╝ ██╗██║     [/bold #2ECC71]\n"
        "[bold #2ECC71] ╚═════╝ ╚═╝  ╚═╝╚══════╝    ╚══════╝╚═╝  ╚═╝╚═╝     [/bold #2ECC71]\n"
        "[dim white]        URL Expander By DarkoDevv v1.0[/dim white]"
    )
    console.print(Align.center(Panel(Align.center(banner_texto), border_style="#2ECC71", box=box.ROUNDED, width=65)))
def expand_url(url):
    print(f"\n\033[1;32m[+] Analizando URL: {url}\033[0m\n")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"}
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        history = r.history; final_url = r.url
        if history:
            table = Table(title="🔗 Redirecciones Detectadas", box=box.ROUNDED, border_style="#2ECC71", title_style="bold #2ECC71")
            table.add_column("Salto", style="cyan", justify="center", width=10); table.add_column("URL de Destino", style="white")
            table.add_row("Inicio", url)
            for i, resp in enumerate(history, 1): table.add_row(f"Salto {i}", resp.url)
            console.print(Align.center(table))
        else: print("\033[1;33m[!] No hubo redirecciones.\033[0m")
        print(f"\n\033[1;32m[✅] URL Final:\033[0m {final_url}")
    except Exception as e: print(f"\033[1;31m[-] Error al expandir: {e}\033[0m")
def menu():
    while True:
        _clear(); draw_banner()
        print("\n\033[1;32m[1]\033[0m Expandir una URL")
        print("\033[1;32m[0]\033[0m Salir\n")
        print("\033[1;32m┌──\033[0m(\033[1;32mURLExpander\033[0m㉿\033[1;32m" + _get_os_name() + "\033[0m)")
        print("\033[1;32m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip(); print("\033[F\033[K", end="", flush=True)
        if choice == "0":
            _clear(); draw_banner(); print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n"); break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;32mPega la URL a expandir:\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip(); print()
            if target: expand_url(target); input("\nPresiona Enter para volver...")
if __name__ == "__main__": menu()
