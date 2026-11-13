import os, sys, platform, time, json
import requests
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align

console = Console(highlight=False)

C1 = "#FF0000"
C2 = "#FFFFFF"
C3 = "#990000"
W1 = "#FFFFFF"

def _clear(): os.system('cls' if os.name == 'nt' else 'clear')

def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    if os.name == "nt": return "powershell" if "PS" in os.environ.get("PROMPT", "") else "cmd"
    return platform.system().lower()

def draw_banner():
    banner_texto = (
        f"\n[bold {C1}]██████╗  ██████╗ ██████╗ ██╗      ██████╗ ██╗  ██╗[/bold {C1}]\n"
        f"[bold {C1}]██╔══██╗██╔═══██╗██╔══██╗██║     ██╔═══██╗╚██╗██╔╝[/bold {C1}]\n"
        f"[bold {W1}]██████╔╝██║   ██║██████╔╝██║     ██║   ██║ ╚███╔╝ [/bold {W1}]\n"
        f"[bold {W1}]██╔══██╗██║   ██║██╔══██╗██║     ██║   ██║ ██╔██╗ [/bold {W1}]\n"
        f"[bold {C3}]██║  ██║╚██████╔╝██████╔╝███████╗╚██████╔╝██╔╝ ██╗[/bold {C3}]\n"
        f"[bold {C3}]╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═╝[/bold {C3}]\n"
        f"\n[dim {W1}]          Roblox Lookup By DarkoDevv v1.0          [/dim {W1}]"
    )
    panel = Panel(
        Align.center(banner_texto, vertical="middle"),
        border_style=C1, box=box.ROUNDED, width=60, padding=(0, 1)
    )
    console.print(Align.center(panel))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

def _get(url, timeout=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None

def _fmt_date(iso_str):
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return iso_str[:19].replace("T", " ")

def _fmt_number(n):
    if n is None:
        return "N/A"
    try:
        return f"{int(n):,}".replace(",", ".")
    except Exception:
        return str(n)

def lookup_user(username):
    print(f"\n\033[1;31m[+] Buscando usuario de Roblox: {username}\033[0m\n")

    data = None
    try:
        r = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={"usernames": [username], "excludeBannedUsers": False},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
        else:
            print("\033[1;31m[-] Error al consultar la API de Roblox.\033[0m")
            return
    except Exception as e:
        print(f"\033[1;31m[-] Error de conexion: {e}\033[0m")
        return

    users = data.get("data", [])
    if not users:
        print(f"\033[1;31m[-] No se encontro el usuario '{username}'.\033[0m")
        return

    uid = users[0].get("id")
    name = users[0].get("name", username)
    display = users[0].get("displayName", name)

    info = _get(f"https://users.roblox.com/v1/users/{uid}")
    if not info:
        print("\033[1;31m[-] No se pudo obtener la informacion del usuario.\033[0m")
        return

    created = _fmt_date(info.get("created"))
    desc = (info.get("description") or "").strip() or "Sin descripcion"
    is_banned = info.get("isBanned", False)
    has_verified = info.get("hasVerifiedBadge", False)

    avatar = _get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={uid}&size=420x420&format=Png&isCircular=false")
    avatar_url = "N/A"
    if avatar and avatar.get("data"):
        avatar_url = avatar["data"][0].get("imageUrl", "N/A")

    friends_count = _get(f"https://friends.roblox.com/v1/users/{uid}/friends/count")
    friends = friends_count.get("count", 0) if friends_count else "N/A"

    followers = _get(f"https://friends.roblox.com/v1/users/{uid}/followers/count")
    followers_n = followers.get("count", 0) if followers else "N/A"

    following = _get(f"https://friends.roblox.com/v1/users/{uid}/followings/count")
    following_n = following.get("count", 0) if following else "N/A"

    groups_data = _get(f"https://groups.roblox.com/v2/users/{uid}/groups/roles")
    groups_n = len(groups_data.get("data", [])) if groups_data else 0
    top_groups = []
    if groups_data and groups_data.get("data"):
        grupos_ordenados = sorted(
            groups_data["data"],
            key=lambda g: g.get("role", {}).get("rank", 0),
            reverse=True
        )
        for g in grupos_ordenados[:5]:
            gname = g.get("group", {}).get("name", "?")
            grank = g.get("role", {}).get("name", "?")
            top_groups.append(f"{gname} ({grank})")

    status = "Desconocido"
    last_online = "N/A"
    game_name = "N/A"
    try:
        r = requests.post(
            "https://presence.roblox.com/v1/presence/users",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={"userIds": [uid]},
            timeout=8
        )
        if r.status_code == 200:
            p = r.json().get("userPresences", [])
            if p:
                pres = p[0]
                tipo = pres.get("userPresenceType", 0)
                if tipo == 1:
                    status = "[green]Online[/green]"
                elif tipo == 2:
                    status = "[cyan]En juego[/cyan]"
                elif tipo == 3:
                    status = "[magenta]En Studio[/magenta]"
                else:
                    status = "[dim]Offline[/dim]"
                if tipo >= 1:
                    last_online = "Ahora (conectado)"
                else:
                    last_online = _fmt_date(pres.get("lastOnline", ""))
                game_name = pres.get("lastLocation", "N/A") or "N/A"
    except Exception:
        pass

    table = Table(
        title=f"Informacion de {name}",
        box=box.ROUNDED, border_style=C1,
        title_style=f"bold {C1}", header_style=f"bold {C3}"
    )
    table.add_column("Propiedad", style=C1, justify="left", width=20)
    table.add_column("Valor", style=W1, justify="left", width=45)

    table.add_row("Username", name)
    table.add_row("Display Name", display)
    table.add_row("User ID", str(uid))
    table.add_row("Perfil", f"https://www.roblox.com/users/{uid}/profile")
    table.add_row("Avatar", avatar_url)
    table.add_row("Fecha de creacion", created)
    table.add_row("Verificado", "[green]Si[/green]" if has_verified else "No")
    table.add_row("Baneado", "[red]Si[/red]" if is_banned else "[green]No[/green]")
    table.add_row("Descripcion", desc[:200])
    table.add_row("Amigos", _fmt_number(friends))
    table.add_row("Seguidores", _fmt_number(followers_n))
    table.add_row("Siguiendo", _fmt_number(following_n))
    table.add_row("Grupos", _fmt_number(groups_n))
    table.add_row("Estado", status)
    table.add_row("Ultima conexion", last_online)
    if game_name != "N/A":
        table.add_row("Jugando", game_name)

    console.print(Align.center(table))

    if top_groups:
        tg = Table(
            title="Top Grupos (por rango)",
            box=box.ROUNDED, border_style=C3,
            title_style=f"bold {C3}", header_style=f"bold {C1}"
        )
        tg.add_column("Grupo", style=W1, justify="left", width=35)
        tg.add_column("Rango", style=C1, justify="left", width=25)
        for g in top_groups:
            nombre, rango = g.rsplit(" (", 1)
            tg.add_row(nombre, rango.rstrip(")"))
        console.print(Align.center(tg))

def lookup_id(user_id):
    print(f"\n\033[1;31m[+] Buscando User ID: {user_id}\033[0m\n")
    info = _get(f"https://users.roblox.com/v1/users/{user_id}")
    if not info:
        print(f"\033[1;31m[-] No se encontro el ID {user_id}.\033[0m")
        return
    name = info.get("name", "?")
    print(f"\033[1;32m[+] Username encontrado: {name}\033[0m")
    lookup_user(name)

def menu():
    os_name = _get_os_name()
    while True:
        _clear()
        draw_banner()
        print(f"\n\033[1;31m[1]\033[0m Buscar por Username")
        print(f"\033[1;31m[2]\033[0m Buscar por User ID")
        print(f"\033[1;31m[0]\033[0m Salir\n")

        print(f"\033[1;31m┌──\033[0m(\033[1;31mRobloxLookup\033[0m㉿\033[1;31m{os_name}\033[0m)")
        print(f"\033[1;31m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)

        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear(); draw_banner()
            print("\n\033[1;37mHasta luego, espero que vuelvas\033[0m\n")
            break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;31mIngresa el Username:\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip()
            if target:
                print()
                lookup_user(target)
                input("\nPresiona Enter para volver...")
        elif choice == "2":
            _clear(); draw_banner()
            print("\n\033[1;31mIngresa el User ID (numeros):\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip()
            if target.isdigit():
                print()
                lookup_id(target)
                input("\nPresiona Enter para volver...")
            else:
                print("\033[1;31m[-] El ID debe ser numerico.\033[0m")
                time.sleep(2)
        else:
            print("\033[1;31mOpcion invalida.\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    menu()
