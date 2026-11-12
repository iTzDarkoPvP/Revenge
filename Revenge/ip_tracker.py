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
        "\n[bold #3498DB]████████╗██████╗  █████╗  ██████╗██╗  ██╗[/bold #3498DB]\n"
        "[bold #3498DB]╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝[/bold #3498DB]\n"
        "[bold white]   ██║   ██████╔╝███████║██║     █████╔╝ [/bold white]\n"
        "[bold white]   ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ [/bold white]\n"
        "[bold #3498DB]   ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗[/bold #3498DB]\n"
        "[bold #3498DB]   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝[/bold #3498DB]\n"
        "[dim white]         IP Tracker By DarkoDevv v1.0[/dim white]"
    )
    console.print(Align.center(Panel(Align.center(banner_texto), border_style="#3498DB", box=box.ROUNDED, width=60)))

def trace_ip(target):
    print(f"\n\033[1;34m[+] Rastreando IP/Dominio: {target}\033[0m\n")
    try:
        r = requests.get(f"http://ip-api.com/json/{target}?fields=status,message,continent,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query,proxy,hosting,mobile", timeout=15)
        data = r.json()
        if data.get("status") == "success":
            es_vpn = "❌ No"
            if data.get("proxy") or data.get("hosting"): es_vpn = "✅ Sí (Proxy/VPN/Hosting)"
            elif data.get("mobile"): es_vpn = "📱 Móvil (Probable 4G/5G)"
            table = Table(title=f"🌍 Información de {data.get('query')}", box=box.ROUNDED, border_style="#3498DB", title_style="bold #3498DB")
            table.add_column("Propiedad", style="cyan", justify="right", width=15)
            table.add_column("Valor", style="white", justify="left", width=40)
            table.add_row("IP Pública", data.get("query"))
            table.add_row("Continente", data.get("continent", "N/A"))
            table.add_row("País", f"{data.get('country')} ({data.get('countryCode')})")
            table.add_row("Región", data.get("regionName"))
            table.add_row("Ciudad", data.get("city"))
            table.add_row("Código Postal", str(data.get("zip", "N/A")))
            table.add_row("Zona Horaria", data.get("timezone"))
            table.add_row("ISP", data.get("isp"))
            table.add_row("Organización", data.get("org"))
            table.add_row("ASN", data.get("as"))
            table.add_row("VPN / Proxy", es_vpn)
            table.add_row("Coordenadas", f"{data.get('lat')}, {data.get('lon')}")
            console.print(Align.center(table))
            lat, lon = data.get('lat'), data.get('lon')
            print(f"\n\033[1;32m📍 Mapa: https://www.google.com/maps?q={lat},{lon}\033[0m")
        else:
            print(f"\033[1;31m[-] Error: {data.get('message')}\033[0m")
    except Exception as e:
        print(f"\033[1;31m[-] Error de conexión: {e}\033[0m")

def menu():
    while True:
        _clear()
        draw_banner()
        print("\n\033[1;34m[1]\033[0m Rastrear una IP o Dominio")
        print("\033[1;34m[0]\033[0m Salir\n")
        print("\033[1;34m┌──\033[0m(\033[1;34mIPTracker\033[0m㉿\033[1;34m" + _get_os_name() + "\033[0m)")
        print("\033[1;34m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)
        if choice == "0":
            _clear(); draw_banner(); print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n"); break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;34mIngresa la IP o Dominio (Enter = tu propia IP):\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip()
            if not target:
                try:
                    target = requests.get("https://api.ipify.org", timeout=10).text
                    print(f"\033[2mUsando tu IP: {target}\033[0m")
                except:
                    print("\033[1;31m[-] No se pudo obtener tu IP.\033[0m"); continue
            print(); trace_ip(target); input("\nPresiona Enter para volver...")
if __name__ == "__main__": menu()
