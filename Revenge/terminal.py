import os, sys, platform, time, subprocess
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich import box

console = Console(highlight=False)

C1 = "#00FF7F"
C2 = "#00CC66"
C3 = "#006633"

def _clear(): os.system('cls' if os.name == 'nt' else 'clear')

def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    if os.name == "nt": return "powershell" if "PS" in os.environ.get("PROMPT", "") else "cmd"
    return platform.system().lower()

def draw_banner():
    banner_texto = (
        f"\n[bold {C1}]████████╗███████╗██████╗ ███╗   ███╗[/bold {C1}]\n"
        f"[bold {C1}]╚══██╔══╝██╔════╝██╔══██╗████╗ ████║[/bold {C1}]\n"
        f"[bold {C2}]   ██║   █████╗  ██████╔╝██╔████╔██║[/bold {C2}]\n"
        f"[bold {C2}]   ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║[/bold {C2}]\n"
        f"[bold {C3}]   ██║   ███████╗██║  ██║██║ ╚═╝ ██║[/bold {C3}]\n"
        f"[bold {C3}]   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝[/bold {C3}]\n"
        f"\n[dim {C1}]  SSH Terminal By DarkoDevv v1.0  [/dim {C1}]"
    )
    panel = Panel(
        Align.center(banner_texto, vertical="middle"),
        border_style=C1, box=box.ROUNDED, width=42, padding=(0, 1)
    )
    console.print(Align.center(panel))

def get_host_port(target):
    target = target.replace("http://", "").replace("https://", "").strip("/")
    if ":" in target:
        parts = target.split(":")
        if len(parts) == 2:
            return parts[0], int(parts[1])
    return target, 22

def ssh_native(host, port, user, pw):
    print(f"\n\033[1;32m[+] Conectando a {host}:{port} como '{user}'...\033[0m")
    print("\033[2m(Usando cliente SSH nativo del sistema)\033[0m\n")
    
    # Verificamos si sshpass está instalado para pasar la contraseña automáticamente
    try:
        subprocess.run(["sshpass", "-V"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        has_sshpass = True
    except FileNotFoundError:
        has_sshpass = False

    if has_sshpass:
        cmd = ["sshpass", "-p", pw, "ssh", "-o", "StrictHostKeyChecking=no", "-p", str(port), f"{user}@{host}"]
    else:
        # Si no hay sshpass, usamos expect-like con ssh normal
        print("\033[1;33m[!] No se detectó 'sshpass'. Instala con: pkg install sshpass\033[0m")
        print("\033[1;33m[!] Usando método alternativo (puede pedir contraseña manualmente).\033[0m\n")
        cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-p", str(port), f"{user}@{host}"]

    try:
        if has_sshpass:
            # Ejecutamos sshpass y pasamos el control total a la terminal
            subprocess.run(cmd, shell=False)
        else:
            # Fallback: enviamos la contraseña usando pexpect si existe
            try:
                import pexpect
                child = pexpect.spawn(" ".join(cmd), encoding='utf-8', timeout=10)
                child.expect("password:")
                child.sendline(pw)
                child.interact()
            except ImportError:
                print("\033[1;31m[-] Ni sshpass ni pexpect disponibles.\033[0m")
                print("\033[1;32m[+] Ejecutando SSH manual...\033[0m\n")
                subprocess.run(cmd)
    except Exception as e:
        print(f"\n\033[1;31m[-] Error: {e}\033[0m")

def menu():
    os_name = _get_os_name()
    while True:
        _clear()
        draw_banner()
        print(f"\n\033[1;32m[1]\033[0m Conectar por SSH")
        print(f"\033[1;32m[0]\033[0m Salir\n")
        
        print(f"\033[1;32m┌──\033[0m(\033[1;32mTerminal\033[0m㉿\033[1;32m{os_name}\033[0m)")
        print(f"\033[1;32m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)

        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear()
            draw_banner()
            print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n")
            break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;32mIP o IP:PUERTO:\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip()
            if not target:
                continue
            host, port = get_host_port(target)

            print("\033[1;32mUsuario:\033[0m ", end="", flush=True)
            user = sys.stdin.readline().strip()
            
            print("\033[1;32mContraseña:\033[0m ", end="", flush=True)
            pw = sys.stdin.readline().strip()

            if not user or not pw:
                print("\033[1;31m[-] Usuario o contraseña vacíos.\033[0m")
                time.sleep(2)
                continue

            print()
            try:
                ssh_native(host, port, user, pw)
            except KeyboardInterrupt:
                print("\n\033[1;33m[!] Sesión finalizada.\033[0m")
            
            input("\nPresiona Enter para volver al menú...")
        else:
            print("\033[1;31mOpción inválida.\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    menu()
