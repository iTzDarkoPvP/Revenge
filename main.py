import os, sys, subprocess, platform, time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align

console = Console(highlight=False)

R1 = "#E74C3C"
R2 = "#922B21"
W1 = "#FFFFFF"
G1 = "#BDC3C7"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(BASE_DIR, "Revenge")

def _clear(): os.system('cls' if os.name == 'nt' else 'clear')
def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    return platform.system().lower()

def draw_banner():
    banner_ascii = (
        f"\n[bold {W1}]██████╗ ███████╗██╗   ██╗███████╗███╗   ██╗ ██████╗ ███████╗[/bold {W1}]\n"
        f"[bold {W1}]██╔══██╗██╔════╝██║   ██║██╔════╝████╗  ██║██╔════╝ ██╔════╝[/bold {W1}]\n"
        f"[bold {R1}]██████╔╝█████╗  ██║   ██║█████╗  ██╔██╗ ██║██║  ███╗█████╗  [/bold {R1}]\n"
        f"[bold {R1}]██╔══██╗██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║██║   ██║██╔══╝  [/bold {R1}]\n"
        f"[bold {R2}]██║  ██║███████╗ ╚████╔╝ ███████╗██║ ╚████║╚██████╔╝███████╗[/bold {R2}]\n"
        f"[bold {R2}]╚═╝  ╚═╝╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝[/bold {R2}]\n"
    )
    panel = Panel(
        Align.center(banner_ascii, vertical="middle"),
        border_style=R2, box=box.ROUNDED, width=66, padding=(1, 0)
    )
    console.print(Align.center(panel))
    console.print(Align.center(f"[bold {W1}]Revenge KIT v1.0 By DarkoDev[/bold {W1}]\n"))

TOOLS = {
    "1": {"name": "Steam Checker", "file": "steam_chk.py", "desc": "Cuentas Steam"},
    "2": {"name": "Crunchy Checker", "file": "crunchy_chk.py", "desc": "Cuentas Crunchy"},
    "3": {"name": "IP Tracker", "file": "ip_tracker.py", "desc": "Ubicacion IPs"},
    "4": {"name": "Port Scanner", "file": "port_scanner.py", "desc": "Puertos abiertos"},
    "5": {"name": "DNS Lookup", "file": "dns_lookup.py", "desc": "Registros DNS"},
    "6": {"name": "Subdomain Finder", "file": "subdomain_finder.py", "desc": "Subdominios"},
    "7": {"name": "Recon Tool", "file": "recon_tool.py", "desc": "OSINT de IP"},
    "8": {"name": "Ping Sweeper", "file": "ping_sweeper.py", "desc": "Red Wi-Fi local"},
    "9": {"name": "MAC Lookup", "file": "mac_lookup.py", "desc": "Fabricante MAC"},
    "10": {"name": "URL Shortener", "file": "url_shortener.py", "desc": "Acortar enlaces"},
    "11": {"name": "URL Expander", "file": "url_expander.py", "desc": "Expandir enlaces"},
    "12": {"name": "Whois/Recon", "file": "whois.py", "desc": "WHOIS + Tech + Headers + SSL"},
    "13": {"name": "Net/Infra", "file": "net_infra.py", "desc": "Traceroute+Banners+HTTP+WAF"},
    "14": {"name": "BruteForce", "file": "bruteforce.py", "desc": "Credenciales SSH/FTP/HTTP"},
    "15": {"name": "Terminal SSH", "file": "terminal.py", "desc": "Conexión SSH interactiva"},
}

def check_tool_exists(filename):
    return os.path.exists(os.path.join(TOOLS_DIR, filename))

def run_tool(filename):
    _clear()
    console.print(f"\n[bold {R1}]▶ Ejecutando {filename}...[/bold {R1}]\n")
    try:
        ruta_completa = os.path.join(TOOLS_DIR, filename)
        subprocess.run([sys.executable, ruta_completa])
    except KeyboardInterrupt:
        console.print("\n[bold red]⏹ Detenido por el usuario.[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error al ejecutar: {e}[/bold red]")
    
    input("\nPresiona Enter para volver al menú principal...")

def menu():
    while True:
        _clear()
        draw_banner()
        
        table = Table(show_header=True, box=box.ROUNDED, border_style=R2, padding=(0, 1), expand=False)
        table.add_column("Op", style=W1, justify="center")
        table.add_column("Herramienta", style=f"bold {R1}")
        table.add_column("Descripción", style=W1)
        table.add_column("Estado", justify="center")

        for key, tool in TOOLS.items():
            exists = check_tool_exists(tool["file"])
            status = "[green]✓[/green]" if exists else f"[{R1}]✗[/{R1}]"
            table.add_row(key, tool["name"], tool["desc"], status)

        console.print(Align.center(table))
        print(f"\n\033[1;31m[0]\033[0m Salir\n")
        
        print(f"\033[1;31m┌──\033[0m(\033[1;31mRevengeMenu\033[0m㉿\033[1;31m{_get_os_name()}\033[0m)")
        print(f"\033[1;31m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        
        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear()
            draw_banner()
            console.print(f"\n[bold {W1}]Hasta luego, espero que vuelvas 👋🏻[/bold {W1}]\n")
            break
        elif choice in TOOLS:
            tool = TOOLS[choice]
            if check_tool_exists(tool["file"]):
                run_tool(tool["file"])
            else:
                console.print(f"\n[bold {R1}]✗ El archivo '{tool['file']}' no existe en la carpeta Revenge/.[/bold {R1}]")
                time.sleep(2)
        else:
            console.print(f"\n[bold {R1}]Opción inválida.[/bold {R1}]")
            time.sleep(1)

if __name__ == "__main__":
    menu()
