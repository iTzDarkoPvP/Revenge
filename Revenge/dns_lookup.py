import os, sys, platform, socket
import dns.resolver
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align
console = Console(highlight=False)
resolver = dns.resolver.Resolver(configure=False)
resolver.nameservers = ['8.8.8.8', '1.1.1.1']; resolver.timeout = 3; resolver.lifetime = 3
def _clear(): os.system('cls' if os.name == 'nt' else 'clear')
def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    return platform.system().lower()
def draw_banner():
    banner_texto = (
        "\n[bold #E74C3C]██████╗ ███╗   ██╗███████╗[/bold #E74C3C]\n"
        "[bold #E74C3C]██╔══██╗████╗  ██║██╔════╝[/bold #E74C3C]\n"
        "[bold white]██║  ██║██╔██╗ ██║███████╗[/bold white]\n"
        "[bold white]██║  ██║██║╚██╗██║╚════██║[/bold white]\n"
        "[bold #E74C3C]██████╔╝██║ ╚████║███████║[/bold #E74C3C]\n"
        "[bold #E74C3C]╚═════╝ ╚═╝  ╚═══╝╚══════╝[/bold #E74C3C]\n"
        "[dim white]    DNS Lookup By DarkoDevv v1.0[/dim white]"
    )
    console.print(Align.center(Panel(Align.center(banner_texto), border_style="#E74C3C", box=box.ROUNDED, width=60)))
def lookup_dns(domain):
    print(f"\n\033[1;31m[+] Consultando registros DNS de: {domain}\033[0m\n")
    try:
        ips = [str(ip) for ip in resolver.resolve(domain, 'A')]
        table_a = Table(title="📌 Registros A (IPv4)", box=box.ROUNDED, border_style="#E74C3C", title_style="bold #E74C3C")
        table_a.add_column("Dirección IP", style="cyan", justify="center")
        for ip in ips: table_a.add_row(ip)
        console.print(Align.center(table_a))
    except: print("\033[1;33m[!] Sin registros A.\033[0m")
    try:
        mx = sorted([(r.preference, str(r.exchange).rstrip('.')) for r in resolver.resolve(domain, 'MX')])
        table_mx = Table(title="📧 Registros MX (Correo)", box=box.ROUNDED, border_style="#E74C3C", title_style="bold #E74C3C")
        table_mx.add_column("Prioridad", style="yellow", justify="center"); table_mx.add_column("Servidor", style="cyan", justify="left")
        for pref, host in mx: table_mx.add_row(str(pref), host)
        console.print(Align.center(table_mx))
    except: print("\033[1;33m[!] Sin registros MX (No recibe correos).\033[0m")
    try:
        ns = sorted([str(n).rstrip('.') for n in resolver.resolve(domain, 'NS')])
        table_ns = Table(title="🌐 Registros NS (Nameservers)", box=box.ROUNDED, border_style="#E74C3C", title_style="bold #E74C3C")
        table_ns.add_column("Servidor DNS", style="cyan", justify="center")
        for server in ns: table_ns.add_row(server)
        console.print(Align.center(table_ns))
    except: print("\033[1;33m[!] Sin registros NS.\033[0m")
    try:
        txt = [str(t).strip('"') for t in resolver.resolve(domain, 'TXT')]
        if txt:
            table_txt = Table(title="📝 Registros TXT (Seguridad / Info)", box=box.ROUNDED, border_style="#E74C3C", title_style="bold #E74C3C")
            table_txt.add_column("Texto", style="dim white", justify="left", width=50, overflow="fold")
            for t in txt:
                t_short = (t[:60] + '...') if len(t) > 60 else t
                table_txt.add_row(t_short)
            console.print(Align.center(table_txt))
        else: print("\033[1;33m[!] Sin registros TXT.\033[0m")
    except: print("\033[1;33m[!] Sin registros TXT.\033[0m")
def menu():
    while True:
        _clear(); draw_banner()
        print("\n\033[1;31m[1]\033[0m Consultar DNS de un Dominio")
        print("\033[1;31m[0]\033[0m Salir\n")
        print("\033[1;31m┌──\033[0m(\033[1;31mDNSLookup\033[0m㉿\033[1;31m" + _get_os_name() + "\033[0m)")
        print("\033[1;31m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)
        if choice == "0":
            _clear(); draw_banner(); print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n"); break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;31mIngresa el Dominio (ej: google.com):\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip(); print()
            if target: lookup_dns(target); input("\nPresiona Enter para volver...")
if __name__ == "__main__": menu()
