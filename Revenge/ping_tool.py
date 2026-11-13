import os, sys, platform, subprocess, time, socket, re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich import box
from rich.align import Align

console = Console(highlight=False)

C1 = "#00FFCC"
C2 = "#00B3B3"
W1 = "#FFFFFF"

def _clear(): os.system('cls' if os.name == 'nt' else 'clear')

def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    if os.name == "nt": return "powershell" if "PS" in os.environ.get("PROMPT", "") else "cmd"
    return platform.system().lower()

def draw_banner():
    banner_texto = (
        f"\n[bold {C1}]██████╗ ██╗███╗   ██╗ ██████╗ [/bold {C1}]\n"
        f"[bold {C1}]██╔══██╗██║████╗  ██║██╔════╝ [/bold {C1}]\n"
        f"[bold {W1}]██████╔╝██║██╔██╗ ██║██║  ███╗[/bold {W1}]\n"
        f"[bold {W1}]██╔═══╝ ██║██║╚██╗██║██║   ██║[/bold {W1}]\n"
        f"[bold {C2}]██║     ██║██║ ╚████║╚██████╔╝[/bold {C2}]\n"
        f"[bold {C2}]╚═╝     ╚═╝╚═╝  ╚═══╝ ╚═════╝ [/bold {C2}]\n"
        f"\n[dim {C1}]      Ping Tool By DarkoDevv v1.0      [/dim {C1}]"
    )
    panel = Panel(
        Align.center(banner_texto, vertical="middle"),
        border_style=C2, box=box.ROUNDED, width=45, padding=(0, 1)
    )
    console.print(Align.center(panel))

def run_ping(target, count=4):
    param = '-n' if os.name == 'nt' else '-c'
    
    print(f"\n\033[1;36m[+] Haciendo ping a: {target} ({count} paquetes)\033[0m\n")
    
    try:
        ip = socket.gethostbyname(target)
        print(f"\033[2m[*] IP Resuelta: {ip}\033[0m\n")
    except:
        print(f"\033[1;31m[-] No se pudo resolver el host: {target}\033[0m")
        return

    try:
        output = subprocess.check_output(['ping', param, str(count), target], stderr=subprocess.STDOUT, timeout=15).decode('utf-8', errors='ignore')
    except subprocess.CalledProcessError as e:
        output = e.output.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"\033[1;31m[-] Error al ejecutar ping: {e}\033[0m")
        return

    table = Table(title=f"Paquetes de {target}", box=box.ROUNDED, border_style=C2, title_style=f"bold {C1}", header_style=f"bold {C1}")
    table.add_column("Nº", style=C1, justify="center", width=4)
    table.add_column("Tiempo (ms)", style=W1, justify="center", width=15)
    table.add_column("TTL", style=C2, justify="center", width=10)
    table.add_column("Tamaño", style="dim white", justify="center", width=10)

    lines = output.split('\n')
    packet_count = 0
    
    for line in lines:
        if "bytes from" in line and "time=" in line:
            ttl_match = re.search(r'ttl=(\d+)', line)
            time_match = re.search(r'time=([\d\.]+)', line)
            size_match = re.search(r'(\d+) bytes', line)
            
            if ttl_match and time_match:
                packet_count += 1
                ttl = ttl_match.group(1)
                latency = float(time_match.group(1))
                size = size_match.group(1) if size_match else "64"
                
                if latency < 50: color = "green"
                elif latency < 150: color = "yellow"
                else: color = "red"
                    
                table.add_row(str(packet_count), f"[{color}]{latency}[/{color}]", ttl, size)

    if packet_count == 0:
        print("\033[1;33m[!] No se pudieron extraer los paquetes individuales. Mostrando salida completa:\033[0m\n")
        print(output)
    else:
        console.print(Align.center(table))

    stats_table = Table(title="Estadísticas del Ping", box=box.ROUNDED, border_style=C2, title_style=f"bold {C1}", header_style=f"bold {C1}")
    stats_table.add_column("Métrica", style=C1, justify="left", width=15)
    stats_table.add_column("Valor", style=W1, justify="left", width=30)

    loss_match = re.search(r'(\d+)% packet loss', output)
    min_avg_max_match = re.search(r'min/avg/max/(?:mdev|stddev) = ([\d\.]+)/([\d\.]+)/([\d\.]+)/([\d\.]+)', output)
    
    if loss_match:
        loss = loss_match.group(1)
        color = "green" if loss == "0" else ("yellow" if int(loss) < 50 else "red")
        stats_table.add_row("Pérdida", f"[{color}]{loss}%[/{color}]")
    
    if min_avg_max_match:
        min_l, avg_l, max_l, mdev = min_avg_max_match.groups()
        stats_table.add_row("Mínimo", f"{min_l} ms")
        stats_table.add_row("Promedio", f"{avg_l} ms")
        stats_table.add_row("Máximo", f"{max_l} ms")
        stats_table.add_row("Jitter", f"{mdev} ms")
    
    ip_match = re.search(r'\(([\d\.]+)\)', output)
    if ip_match:
        stats_table.add_row("IP Destino", ip_match.group(1))

    console.print(Align.center(stats_table))

def generate_continuous_table(target, ip, logs):
    table = Table(title=f"Ping Constante: {target} ({ip})", box=box.ROUNDED, border_style=C2, title_style=f"bold {C1}", header_style=f"bold {C1}", expand=False)
    table.add_column("Bytes", style="dim white", justify="center", width=6)
    table.add_column("Origen", style=W1, justify="center", width=18)
    table.add_column("TTL", style=C2, justify="center", width=6)
    table.add_column("Tiempo", justify="center", width=12)
    table.add_column("Estado", justify="center", width=8)

    for log in logs[-15:]: # Mostrar los últimos 15 pings
        if "timeout" in log:
            table.add_row("*", "*", "*", "*", "[red]TIMEOUT[/red]")
        else:
            latency = float(log['time'])
            if latency < 50: color = "green"
            elif latency < 150: color = "yellow"
            else: color = "red"
            
            table.add_row(
                str(log['bytes']), 
                ip, 
                str(log['ttl']), 
                f"[{color}]{log['time']} ms[/{color}]",
                "[green]OK[/green]"
            )
    return table

def run_ping_continuous(target):
    try:
        ip = socket.gethostbyname(target)
    except:
        print(f"\033[1;31m[-] No se pudo resolver el host: {target}\033[0m")
        return

    _clear(); draw_banner()
    print("\033[1;33m[!] Presiona Ctrl+C para detener el ping.\033[0m\n")
    time.sleep(1)

    logs = []
    param = '-n' if os.name == 'nt' else '-c'
    
    try:
        with Live(generate_continuous_table(target, ip, logs), console=console, refresh_per_second=1, screen=False) as live:
            while True:
                try:
                    output = subprocess.check_output(['ping', param, '1', '-W', '1', target], stderr=subprocess.STDOUT, timeout=3).decode('utf-8', errors='ignore')
                    found = False
                    for line in output.split('\n'):
                        if "bytes from" in line and "time=" in line:
                            found = True
                            ttl_match = re.search(r'ttl=(\d+)', line)
                            time_match = re.search(r'time=([\d\.]+)', line)
                            size_match = re.search(r'(\d+) bytes', line)
                            
                            if ttl_match and time_match:
                                logs.append({
                                    'bytes': size_match.group(1) if size_match else 64,
                                    'ttl': ttl_match.group(1),
                                    'time': time_match.group(1)
                                })
                    if not found:
                        logs.append("timeout")
                except Exception:
                    logs.append("timeout")
                    
                live.update(generate_continuous_table(target, ip, logs))
                time.sleep(1)
                
    except KeyboardInterrupt:
        pass # El Ctrl+C se maneja de forma limpia

def menu():
    os_name = _get_os_name()
    while True:
        _clear()
        draw_banner()
        print(f"\n\033[1;34m[1]\033[0m Ping Normal (4 paquetes)")
        print(f"\033[1;34m[2]\033[0m Ping Constante (Estilo Windows)")
        print(f"\033[1;34m[0]\033[0m Salir\n")
        
        print(f"\033[1;34m┌──\033[0m(\033[1;34mPingTool\033[0m㉿\033[1;34m{os_name}\033[0m)")
        print(f"\033[1;34m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)

        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear(); draw_banner()
            print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n")
            break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;34mIngresa IP o Dominio:\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip()
            if target:
                print("\033[1;34mPaquetes (default 4):\033[0m ", end="", flush=True)
                count_str = sys.stdin.readline().strip()
                count = int(count_str) if count_str.isdigit() else 4
                
                run_ping(target, count)
            input("\nPresiona Enter para volver...")
        elif choice == "2":
            _clear(); draw_banner()
            print("\n\033[1;34mIngresa IP o Dominio:\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip()
            if target:
                run_ping_continuous(target)
            input("\nPresiona Enter para volver...")
        else:
            print("\033[1;31mOpción inválida.\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    menu()
