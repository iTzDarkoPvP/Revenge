import os, sys, platform, urllib.parse, urllib.request
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
        "\n[bold #1ABC9C]███████╗██╗  ██╗ ██████╗ ██████╗ ████████╗[/bold #1ABC9C]\n"
        "[bold #1ABC9C]██╔════╝██║  ██║██╔═══██╗██╔══██╗╚══██╔══╝[/bold #1ABC9C]\n"
        "[bold white]███████╗███████║██║   ██║██████╔╝   ██║   [/bold white]\n"
        "[bold white]╚════██║██╔══██║██║   ██║██╔══██╗   ██║   [/bold white]\n"
        "[bold #1ABC9C]███████║██║  ██║╚██████╔╝██║  ██║   ██║   [/bold #1ABC9C]\n"
        "[bold #1ABC9C]╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   [/bold #1ABC9C]\n"
        "[dim white]    URL Shortener By DarkoDevv v1.0[/dim white]"
    )
    console.print(Panel(Align.center(banner_texto), border_style="#1ABC9C", box=box.ROUNDED))
def shorten_url(long_url):
    print(f"\n\033[1;36m[+] Acortando URL: {long_url}\033[0m\n")
    api_url = "https://tinyurl.com/api-create.php?url=" + urllib.parse.quote(long_url)
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            short_url = r.read().decode('utf-8').strip()
            if short_url.startswith("http"):
                table = Table(title="🔗 Enlace Acortado", box=box.ROUNDED, border_style="#1ABC9C", title_style="bold #1ABC9C")
                table.add_column("Propiedad", style="cyan", justify="right", width=15); table.add_column("Valor", style="white", justify="left", width=40)
                table.add_row("URL Original", long_url); table.add_row("URL Corta", f"[bold green]{short_url}[/bold green]")
                console.print(Align.center(table))
            else: print(f"\033[1;31m[-] Error: {short_url}\033[0m")
    except Exception as e: print(f"\033[1;31m[-] Error de conexión: {e}\033[0m")
def menu():
    while True:
        _clear(); draw_banner()
        print("\n\033[1;36m[1]\033[0m Acortar una URL larga")
        print("\033[1;36m[0]\033[0m Salir\n")
        print("\033[1;36m┌──\033[0m(\033[1;36mURLShortener\033[0m㉿\033[1;36m" + _get_os_name() + "\033[0m)")
        print("\033[1;36m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip(); print("\033[F\033[K", end="", flush=True)
        if choice == "0":
            _clear(); draw_banner(); print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n"); break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;36mPega la URL a acortar:\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip(); print()
            if target: shorten_url(target); input("\nPresiona Enter para volver...")
if __name__ == "__main__": menu()
