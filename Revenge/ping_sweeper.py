import os, sys, platform, subprocess, socket
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
        "\n[bold #F1C40F]██████╗ ██╗███╗   ██╗ ██████╗ [/bold #F1C40F]\n"
        "[bold #F1C40F]██╔══██╗██║████╗  ██║██╔════╝ [/bold #F1C40F]\n"
        "[bold white]██████╔╝██║██╔██╗ ██║██║  ███╗[/bold white]\n"
        "[bold white]██╔═══╝ ██║██║╚██╗██║██║   ██║[/bold white]\n"
        "[bold #F1C40F]██║     ██║██║ ╚████║╚██████╔╝[/bold #F1C40F]\n"
        "[bold #F1C40F]╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ [/bold #F1C40F]\n"
        "[dim white]     Ping Sweeper By DarkoDevv v1.0[/dim white]"
    )
    console.print(Align.center(Panel(Align.center(banner_texto), border_style="#F1C40F", box=box.ROUNDED, width=55)))
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close(); return ip
    except: return None
def ping_host(ip):
    param = '-n' if os.name == 'nt' else '-c'
    try: subprocess.check_output(['ping', param, '1', '-W', '2', ip], stderr=subprocess.DEVNULL, timeout=3); return ip, True
    except: return ip, False
def sweep_network():
    local_ip = get_local_ip()
    if not local_ip: print("\033[1;31m[-] No se pudo detectar tu red local.\033[0m"); return
    base_ip = ".".join(local_ip.split('.')[:3])
    print(f"\n\033[1;33m[+] Tu IP Local es: {local_ip}\033[0m")
    print(f"\033[1;33m[+] Escaneando red: {base_ip}.1 a {base_ip}.254\033[0m")
    print("\033[2mBuscando TODOS los dispositivos (esto puede tardar unos segundos)...\033[0m\n")
    online_hosts = []
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(ping_host, f"{base_ip}.{i}") for i in range(1, 255)]
        for future in futures:
            ip, is_online = future.result()
            if is_online: online_hosts.append(ip)
    if online_hosts:
        table = Table(title="📡 Dispositivos en tu Red", box=box.ROUNDED, border_style="#F1C40F", title_style="bold #F1C40F")
        table.add_column("Dirección IP", style="cyan", justify="center"); table.add_column("Tipo", style="white", justify="center")
        for ip in sorted(online_hosts, key=lambda x: int(x.split('.')[-1])):
            tipo = "Tu Celular" if ip == local_ip else ("Router" if ip == f"{base_ip}.1" else "Dispositivo")
            table.add_row(ip, tipo)
        console.print(Align.center(table))
        print(f"\n\033[1;32m✅ Total de dispositivos conectados: {len(online_hosts)}\033[0m")
    else: print("\033[1;31m[-] No se encontraron dispositivos.\033[0m")
def menu():
    while True:
        _clear(); draw_banner()
        print("\n\033[1;33m[1]\033[0m Escanear mi Red Local (Wi-Fi)")
        print("\033[1;33m[0]\033[0m Salir\n")
        print("\033[1;33m┌──\033[0m(\033[1;33mPingSweeper\033[0m㉿\033[1;33m" + _get_os_name() + "\033[0m)")
        print("\033[1;33m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip(); print("\033[F\033[K", end="", flush=True)
        if choice == "0":
            _clear(); draw_banner(); print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n"); break
        elif choice == "1":
            _clear(); draw_banner(); sweep_network(); input("\nPresiona Enter para volver...")
if __name__ == "__main__": menu()
