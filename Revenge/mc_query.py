import os, sys, platform, time, json, socket, struct, re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich import box
from rich.align import Align

console = Console(highlight=False)

C1 = "#00FF00"
C2 = "#008000"
W1 = "#FFFFFF"

def _clear(): os.system('cls' if os.name == 'nt' else 'clear')

def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    if os.name == "nt": return "powershell" if "PS" in os.environ.get("PROMPT", "") else "cmd"
    return platform.system().lower()

def draw_banner():
    banner_texto = (
        f"\n[bold {C1}]███╗   ███╗ ██████╗     ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗[/bold {C1}]\n"
        f"[bold {C1}]████╗ ████║██╔════╝    ██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝[/bold {C1}]\n"
        f"[bold {W1}]██╔████╔██║██║         ██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝ [/bold {W1}]\n"
        f"[bold {W1}]██║╚██╔╝██║██║         ██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝  [/bold {W1}]\n"
        f"[bold {C2}]██║ ╚═╝ ██║╚██████╗    ╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║   [/bold {C2}]\n"
        f"[bold {C2}]╚═╝     ╚═╝ ╚═════╝     ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   [/bold {C2}]\n"
        f"\n[dim {W1}]        Minecraft Query By DarkoDevv v2.0        [/dim {W1}]"
    )
    panel = Panel(
        Align.center(banner_texto, vertical="middle"),
        border_style=C1, box=box.ROUNDED, width=72, padding=(0, 0)
    )
    console.print(Align.center(panel))

def _pack_varint(num):
    out = b""
    while True:
        b = num & 0x7F
        num >>= 7
        if num:
            out += bytes([b | 0x80])
        else:
            out += bytes([b])
            return out

def _read_varint(sock):
    num = 0
    for i in range(5):
        byte = sock.recv(1)
        if not byte:
            return None
        b = byte[0]
        num |= (b & 0x7F) << (7 * i)
        if not (b & 0x80):
            return num
    return None

def _read_exact(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Conexion cerrada")
        data += chunk
    return data

def _pack_string(s):
    encoded = s.encode("utf-8")
    return _pack_varint(len(encoded)) + encoded

def query_java(host, port, timeout=8):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        inicio = time.time()
        sock.connect((host, port))

        handshake = (
            _pack_varint(0x00) +
            _pack_varint(-1 & 0xFFFFFFFF) +
            _pack_string(host) +
            struct.pack(">H", port) +
            _pack_varint(1)
        )
        sock.sendall(_pack_varint(len(handshake)) + handshake)
        sock.sendall(_pack_varint(1) + _pack_varint(0x00))

        length = _read_varint(sock)
        if length is None:
            sock.close()
            return None
        packet_id = _read_varint(sock)
        if packet_id != 0x00:
            sock.close()
            return None
        json_len = _read_varint(sock)
        if json_len is None:
            sock.close()
            return None
        raw = _read_exact(sock, json_len)
        latency = int((time.time() - inicio) * 1000)
        sock.close()

        data = json.loads(raw.decode("utf-8"))

        desc = data.get("description", {})
        if isinstance(desc, dict):
            motd = desc.get("text", "")
            for extra in desc.get("extra", []):
                if isinstance(extra, dict):
                    motd += extra.get("text", "")
                else:
                    motd += str(extra)
        else:
            motd = str(desc)

        version = data.get("version", {}).get("name", "Desconocida")
        protocol = data.get("version", {}).get("protocol", "N/A")
        players = data.get("players", {})
        online = players.get("online", 0)
        max_players = players.get("max", 0)
        sample = [p.get("name", "") for p in players.get("sample", []) if isinstance(p, dict)]

        return {
            "online": True,
            "edition": "Java",
            "motd": motd or "Sin MOTD",
            "version": version,
            "protocol": protocol,
            "online_players": online,
            "max_players": max_players,
            "sample": sample,
            "latency": latency,
            "software": "Java Edition",
        }
    except (socket.timeout, ConnectionError, OSError):
        return None
    except Exception:
        return None

def _query_gs4(host, port=19132, timeout=3):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        session_id = struct.pack(">I", 0x01010101 & 0xFFFFFFFF)
        handshake = b"\xFE\xFD\x09" + session_id
        sock.sendto(handshake, (host, port))

        data, _ = sock.recvfrom(4096)
        if len(data) < 5 or data[0] != 0x09:
            sock.close()
            return None

        token = data[1:5]

        full = b"\xFE\xFD\x00" + session_id + token + b"\x00\x00\x00\x00"
        sock.sendto(full, (host, port))

        data, _ = sock.recvfrom(65535)
        sock.close()

        if len(data) < 16 or data[0] != 0x00:
            return None

        payload = data[16:]
        text = payload.decode("latin-1", errors="ignore")

        if "\x00\x01player_\x00\x00" not in text:
            return None

        kv_part, players_part = text.split("\x00\x01player_\x00\x00", 1)
        kv_part = kv_part.lstrip("\x00")
        tokens = kv_part.split("\x00")
        info = {}
        for i in range(0, len(tokens) - 1, 2):
            info[tokens[i]] = tokens[i + 1]

        sample = [p for p in players_part.split("\x00") if p]
        return {"info": info, "sample": sample}
    except (socket.timeout, OSError):
        return None
    except Exception:
        return None

def query_bedrock(host, port, timeout=5):
    gs_port = 19132 if port in (19132, 19133) else port
    gs = _query_gs4(host, gs_port, timeout=min(3, timeout))
    if gs:
        info = gs["info"]
        software = info.get("software", "").strip() or "Desconocido"
        version = info.get("version", "").strip() or "Desconocida"
        motd = info.get("hostname", "").strip() or info.get("motd", "").strip() or "Sin MOTD"
        motd = re.sub(r"§.", "", motd).strip()
        try:
            online = int(info.get("numplayers", "0"))
        except:
            online = 0
        try:
            max_players = int(info.get("maxplayers", "0"))
        except:
            max_players = 0
        game_mode = info.get("gametype", "N/A")
        return {
            "online": True,
            "edition": "Bedrock",
            "motd": motd,
            "version": version,
            "protocol": info.get("protocol", "N/A"),
            "online_players": online,
            "max_players": max_players,
            "sample": gs["sample"],
            "latency": 0,
            "software": software,
            "game_mode": game_mode,
        }

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)

        MAGIC = b"\x00\xff\xff\x00\xfe\xfe\xfe\xfe\xfd\xfd\xfd\xfd\x12\x34\x56\x78"
        timestamp = struct.pack(">Q", int(time.time()))
        client_guid = struct.pack(">Q", 0x1234567890ABCDEF)
        ping = b"\x01" + timestamp + MAGIC + client_guid

        inicio = time.time()
        sock.sendto(ping, (host, port))
        data, _ = sock.recvfrom(4096)
        latency = int((time.time() - inicio) * 1000)
        sock.close()

        if not data or data[0] != 0x1C:
            return None

        offset = 33
        if len(data) < offset + 2:
            return None
        str_len = struct.unpack(">H", data[offset:offset+2])[0]
        offset += 2
        raw = data[offset:offset+str_len].decode("utf-8", errors="ignore")
        parts = raw.split(";")

        def _get(idx, default=""):
            return parts[idx].strip() if idx < len(parts) else default

        motd_line1 = _get(1)
        protocol    = _get(2, "N/A")
        version_name= _get(3)
        online_str  = _get(4, "0")
        max_str     = _get(5, "0")
        sub_motd    = _get(7)
        game_mode   = _get(8, "N/A")

        online = int(online_str) if online_str.isdigit() else 0
        max_players = int(max_str) if max_str.isdigit() else 0

        motd_line1 = re.sub(r"§.", "", motd_line1).strip()
        sub_motd   = re.sub(r"§.", "", sub_motd).strip()
        motd_full  = motd_line1 + (" | " + sub_motd if sub_motd else "")

        haystack = (sub_motd + " " + motd_line1).lower()
        if "pocketmine" in haystack:
            software = "PocketMine-MP"
        elif "nukkit" in haystack:
            software = "Nukkit"
        elif "cloudburst" in haystack or "powernukkit" in haystack:
            software = "Cloudburst"
        elif "altay" in haystack:
            software = "Altay"
        elif "bedrock dedicated" in haystack or "bds" in haystack:
            software = "Bedrock Dedicated"
        else:
            software = "Desconocido"

        if not version_name:
            version_name = f"Protocolo {protocol}"

        return {
            "online": True,
            "edition": "Bedrock",
            "motd": motd_full or "Sin MOTD",
            "version": version_name,
            "protocol": protocol,
            "online_players": online,
            "max_players": max_players,
            "sample": [],
            "latency": latency,
            "software": software,
            "game_mode": game_mode,
        }
    except (socket.timeout, OSError):
        return None
    except Exception:
        return None

def fetch_server_info(host, port=None):
    if port is None:
        result = query_java(host, 25565)
        if result:
            return result
        result = query_bedrock(host, 19132)
        if result:
            return result
        return None

    if port in (19132, 19133):
        result = query_bedrock(host, port)
        if result:
            return result
        alt_port = 19132 if port == 19133 else 19133
        return query_bedrock(host, alt_port)

    result = query_java(host, port)
    if result:
        return result
    return query_bedrock(host, port)

def run_query(target):
    if ":" in target:
        host, port_str = target.split(":", 1)
        port = int(port_str) if port_str.isdigit() else None
    else:
        host = target
        port = None

    print(f"\n\033[1;32m[+] Consultando servidor: {host}:{port or 'auto'}\033[0m\n")

    data = fetch_server_info(host, port)

    if not data or not data.get("online"):
        print("\033[1;31m[-] El servidor esta offline o no responde al protocolo nativo.\033[0m")
        return

    table = Table(
        title=f"Servidor: {host}:{port or 'auto'}",
        box=box.ROUNDED, border_style=C1,
        title_style=f"bold {W1}", header_style=f"bold {W1}"
    )
    table.add_column("Propiedad", style=C1, justify="left", width=18)
    table.add_column("Valor", style=W1, justify="left", width=40)

    table.add_row("Edicion", data["edition"])
    table.add_row("MOTD", data["motd"])
    table.add_row("Version", data["version"])
    table.add_row("Protocolo", str(data["protocol"]))
    table.add_row("Software", data["software"])
    if data["edition"] == "Bedrock":
        table.add_row("Modo de juego", data.get("game_mode", "N/A"))

    color = "green" if data["online_players"] > 0 else "white"
    table.add_row(
        "Jugadores",
        f"[{color}]{data['online_players']}[/{color}] / {data['max_players']}"
    )
    table.add_row("Ping", f"{data['latency']} ms")

    if data.get("sample"):
        table.add_row("Jugadores online", ", ".join(data["sample"][:10]))

    console.print(Align.center(table))

def generate_live_table(host, port):
    data = fetch_server_info(host, port)

    if not data or not data.get("online"):
        t = Table(box=box.ROUNDED, border_style=C1, title=f"Ping Constante: {host}:{port or 'auto'}")
        t.add_column("Estado", style="red", justify="center")
        t.add_row("OFFLINE / SIN RESPUESTA")
        return t

    table = Table(
        title=f"Ping Constante: {host}:{port or 'auto'}",
        box=box.ROUNDED, border_style=C1,
        title_style=f"bold {W1}", header_style=f"bold {W1}"
    )
    table.add_column("Estado", style=C1, justify="center")
    table.add_column("Edicion", style=W1, justify="center")
    table.add_column("Jugadores", style=W1, justify="center")
    table.add_column("Version", style=W1, justify="center")
    table.add_column("Software", style=C1, justify="center")
    table.add_column("Ping", style=W1, justify="center")

    color = "green" if data["online_players"] > 0 else "white"
    table.add_row(
        "[bold green]ONLINE[/bold green]",
        data["edition"],
        f"[{color}]{data['online_players']}[/{color}] / {data['max_players']}",
        data["version"],
        data["software"],
        f"{data['latency']} ms"
    )
    return table

def run_query_continuous(target):
    if ":" in target:
        host, port_str = target.split(":", 1)
        port = int(port_str) if port_str.isdigit() else None
    else:
        host = target
        port = None

    _clear(); draw_banner()
    print("\033[1;33m[!] Presiona Ctrl+C para detener el monitoreo.\033[0m\n")
    time.sleep(1)

    try:
        with Live(generate_live_table(host, port), console=console, refresh_per_second=1, screen=False) as live:
            while True:
                live.update(generate_live_table(host, port))
                time.sleep(5)
    except KeyboardInterrupt:
        pass

def menu():
    os_name = _get_os_name()
    while True:
        _clear()
        draw_banner()
        print(f"\n\033[1;32m[1]\033[0m Query Normal")
        print(f"\033[1;32m[2]\033[0m Query Constante")
        print(f"\033[1;32m[0]\033[0m Salir\n")

        print(f"\033[1;32m┌──\033[0m(\033[1;32mMCQuery\033[0m㉿\033[1;32m{os_name}\033[0m)")
        print(f"\033[1;32m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)

        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear(); draw_banner()
            print("\n\033[1;37mHasta luego, espero que vuelvas\033[0m\n")
            break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;32mIP o IP:PUERTO (Enter = auto):\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip()
            if target:
                run_query(target)
            input("\nPresiona Enter para volver...")
        elif choice == "2":
            _clear(); draw_banner()
            print("\n\033[1;32mIP o IP:PUERTO (Enter = auto):\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip()
            if target:
                run_query_continuous(target)
            input("\nPresiona Enter para volver...")
        else:
            print("\033[1;31mOpcion invalida.\033[0m")
        time.sleep(1)

if __name__ == "__main__":
    menu()
