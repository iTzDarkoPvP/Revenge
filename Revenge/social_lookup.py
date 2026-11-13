import os, sys, platform, time, json, re, asyncio
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False

console = Console(highlight=False)

C = "#E50914"
W = "#FFFFFF"
GR = "#A9A9A9"

def _clear(): os.system('cls' if os.name == 'nt' else 'clear')

def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    if os.name == "nt": return "powershell" if "PS" in os.environ.get("PROMPT", "") else "cmd"
    return platform.system().lower()

def draw_banner():
    banner_texto = (
        f"[bold {W}]███████╗ ██████╗  ██████╗██╗ █████╗ ██╗[/bold {W}]\n"
        f"[bold {W}]██╔════╝██╔═══██╗██╔════╝██║██╔══██╗██║[/bold {W}]\n"
        f"[bold {C}]███████╗██║   ██║██║     ██║███████║██║[/bold {C}]\n"
        f"[bold {C}]╚════██║██║   ██║██║     ██║██╔══██║██║[/bold {C}]\n"
        f"[bold {W}]███████║╚██████╔╝╚██████╗██║██║  ██║███████╗[/bold {W}]\n"
        f"[bold {W}]╚══════╝ ╚═════╝  ╚═════╝╚═╝╚═╝  ╚═╝╚══════╝[/bold {W}]"
    )
    
    panel = Panel(
        Align.center(banner_texto),
        border_style=C,
        box=box.ROUNDED,
        padding=(1, 3),
        expand=False
    )
    
    console.print("\n", end="")
    console.print(Align.center(panel))
    console.print(Align.center(f"[dim {GR}]TikTok + Instagram Lookup By DarkoDevv v1.0[/dim {GR}]\n"))

def _fmt_number(n):
    if n is None:
        return "N/A"
    try:
        n = int(str(n).replace(".", "").replace(",", ""))
        if n >= 1_000_000_000:
            return f"{n/1_000_000_000:.1f}B ({n:,})".replace(",", ".")
        if n >= 1_000_000:
            return f"{n/1_000_000:.1f}M ({n:,})".replace(",", ".")
        if n >= 1_000:
            return f"{n/1_000:.1f}K ({n:,})".replace(",", ".")
        return f"{n:,}".replace(",", ".")
    except Exception:
        return str(n)

async def _fetch_tiktok(username):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}, locale="en-US"
        )
        page = await context.new_page()
        url = f"https://www.tiktok.com/@{username}"
        try:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            data = await page.evaluate("""() => {
                const out = {};
                const scripts = document.querySelectorAll('script');
                for (const s of scripts) {
                    if (s.id === '__UNIVERSAL_DATA_FOR_REHYDRATION__') {
                        try {
                            const j = JSON.parse(s.textContent);
                            const scope = j.__DEFAULT_SCOPE__ || {};
                            const ud = scope['webapp.user-detail'] || {};
                            const ui = ud.userInfo || {};
                            if (ui.user && ui.user.id) { out.user = ui.user; out.stats = ui.stats || {}; return out; }
                        } catch(e) {}
                    }
                }
                return out;
            }""")
            user = data.get("user") or {}
            stats = data.get("stats") or {}
            if not user or not user.get("id"):
                title = await page.title()
                if "Couldn't find" in title or "not found" in title.lower():
                    await browser.close(); return {"error": "not_found"}
                try:
                    h1 = await page.query_selector("[data-e2e='user-title']")
                    nick = (await h1.inner_text()).strip() if h1 else username
                    h2 = await page.query_selector("[data-e2e='user-subtitle']")
                    uname = (await h2.inner_text()).strip().replace("@", "") if h2 else username
                    bio_el = await page.query_selector("[data-e2e='user-bio']")
                    bio = (await bio_el.inner_text()).strip() if bio_el else ""
                    followers = await page.query_selector("[data-e2e='followers-count']")
                    following = await page.query_selector("[data-e2e='following-count']")
                    likes = await page.query_selector("[data-e2e='likes-count']")
                    followers_n = (await followers.inner_text()).strip() if followers else "0"
                    following_n = (await following.inner_text()).strip() if following else "0"
                    likes_n = (await likes.inner_text()).strip() if likes else "0"
                    avatars = await page.query_selector_all("img[data-e2e='user-avatar']")
                    avatar = await avatars[0].get_attribute("src") if avatars else "N/A"
                    if not nick and not followers_n:
                        await browser.close(); return {"error": "not_found"}
                    await browser.close()
                    return {
                        "user": {"nickname": nick, "signature": bio, "verified": False, "privateAccount": False, "region": "N/A", "id": "N/A"},
                        "stats": {"followerCount": followers_n, "followingCount": following_n, "heartCount": likes_n, "videoCount": 0},
                        "avatar": avatar, "url": url
                    }
                except Exception:
                    await browser.close(); return {"error": "no_data"}
            avatar = user.get("avatarLarger") or user.get("avatarMedium") or "N/A"
            await browser.close()
            return {"user": user, "stats": stats, "avatar": avatar, "url": url}
        except Exception as e:
            await browser.close(); return {"error": f"exception:{e}"}

async def _fetch_instagram(username):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}, locale="en-US"
        )
        page = await context.new_page()
        url = f"https://www.instagram.com/{username}/"
        try:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            await page.wait_for_timeout(3500)
            data = await page.evaluate("""() => {
                const out = {};
                const metas = document.querySelectorAll('meta');
                for (const m of metas) {
                    const prop = m.getAttribute('property') || m.getAttribute('name');
                    const content = m.getAttribute('content') || '';
                    if (prop === 'og:description') out.desc = content;
                    if (prop === 'og:title') out.title = content;
                    if (prop === 'og:image') out.image = content;
                    if (prop === 'description') out.meta_desc = content;
                }
                const spans = document.querySelectorAll('span');
                let counts = [];
                for (const s of spans) {
                    const txt = s.textContent.trim();
                    if (/^[\\d\\.,]+([KMB])?$/.test(txt)) counts.push(txt);
                }
                out.counts = counts;
                const lis = document.querySelectorAll('header li');
                out.li_texts = [];
                for (const li of lis) out.li_texts.push(li.textContent.trim());
                out.login_wall = document.body.innerText.includes('Log in') && !document.querySelector('header');
                return out;
            }""")
            await browser.close()
            if data.get("login_wall") and not data.get("desc"): return {"error": "login_wall"}
            return {"data": data, "url": url}
        except Exception as e:
            await browser.close(); return {"error": f"exception:{e}"}

def _clean_ig_title(title, username):
    if not title: return f"@{username}"
    t = re.sub(r'\s*[•·]\s*Instagram.*$', '', title, flags=re.IGNORECASE)
    t = re.sub(r'\s*\(@[^)]+\)\s*', ' ', t)
    return re.sub(r'\s+', ' ', t).strip() or f"@{username}"

def _clean_ig_bio(bio, username):
    if not bio: return "Sin bio"
    b = re.sub(r'^.*?Instagram:\s*', '', bio, flags=re.IGNORECASE)
    b = re.sub(r'^.*?Instagram photos and videos\s*', '', b, flags=re.IGNORECASE)
    b = re.sub(r'^from\s+.*?\(@[^)]+\)\s*', '', b, flags=re.IGNORECASE)
    b = re.sub(r'^.*?\(@' + re.escape(username) + r'\)\s*', '', b, flags=re.IGNORECASE)
    b = re.sub(r'^\d[\d\.,]*[KMB]?\s+(Followers?|Following|Posts?).*$', '', b, flags=re.IGNORECASE)
    b = re.sub(r'\s*[•·]\s*See.*$', '', b, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', b).strip() or "Sin bio"

def lookup_tiktok(username):
    username = username.replace("@", "").strip()
    print(f"\n\033[1;31m[+] Buscando TikTok:\033[0m \033[1;37m@{username}\033[0m\n")

    if not PLAYWRIGHT_OK:
        print("\033[1;31m[-] Falta Playwright. Instala: pip install playwright && python -m playwright install chromium\033[0m\n")
        return

    result = asyncio.run(_fetch_tiktok(username))

    if "error" in result:
        err = result["error"]
        if err == "not_found": print(f"\033[1;31m[-] El usuario @{username} no existe en TikTok.\033[0m")
        elif err == "no_data": print(f"\033[1;33m[!] TikTok no devolvio datos. Abre manual: https://www.tiktok.com/@{username}\033[0m")
        else: print(f"\033[1;31m[-] Error: {err}\033[0m")
        return

    user = result["user"]; stats = result["stats"]; url = result["url"]
    
    table = Table(box=box.ROUNDED, border_style=C, title=f"[bold {W}]TikTok @{username}[/]", title_justify="center", show_header=False)
    table.add_column("Propiedad", style=C, justify="right", width=18)
    table.add_column("Valor", style=W, justify="left", width=45)

    table.add_row("Nickname", user.get("nickname", "N/A"))
    table.add_row("User ID", str(user.get("id", "N/A")))
    table.add_row("Perfil", url)
    table.add_row("Avatar", result["avatar"])
    table.add_row("Verificado", "[green]Si[/green]" if user.get("verified") else "No")
    table.add_row("Cuenta privada", "[yellow]Si[/yellow]" if user.get("privateAccount") else "No")
    table.add_row("Region", user.get("region", "N/A"))
    table.add_row("Bio", (user.get("signature") or "Sin bio")[:200])
    table.add_row("Seguidores", _fmt_number(stats.get("followerCount", 0)))
    table.add_row("Siguiendo", _fmt_number(stats.get("followingCount", 0)))
    table.add_row("Likes totales", _fmt_number(stats.get("heartCount") or stats.get("heart") or 0))
    table.add_row("Videos", _fmt_number(stats.get("videoCount", 0)))

    console.print(Align.center(table))

def lookup_instagram(username):
    username = username.replace("@", "").strip()
    print(f"\n\033[1;31m[+] Buscando Instagram:\033[0m \033[1;37m@{username}\033[0m\n")

    if not PLAYWRIGHT_OK:
        print("\033[1;31m[-] Falta Playwright.\033[0m")
        return

    result = asyncio.run(_fetch_instagram(username))

    if "error" in result:
        err = result["error"]
        if err == "login_wall": print(f"\033[1;33m[!] Instagram pidio login. Abre manual: https://www.instagram.com/{username}/\033[0m")
        else: print(f"\033[1;31m[-] Error: {err}\033[0m")
        return

    data = result["data"]; url = result["url"]
    desc, meta_desc, raw_title = data.get("desc", ""), data.get("meta_desc", ""), data.get("title", "")
    avatar, counts, li_texts = data.get("image", "N/A"), data.get("counts", []), data.get("li_texts", [])

    followers, following, posts = "N/A", "N/A", "N/A"
    fm = re.search(r'([\d\.,]+[KMB]?)\s*Followers?,\s*([\d\.,]+[KMB]?)\s*Following', desc or meta_desc or "")
    if fm: followers, following = fm.group(1), fm.group(2)
    pm = re.search(r'([\d\.,]+[KMB]?)\s*Posts?', desc or meta_desc or "")
    if pm: posts = pm.group(1)

    for li in li_texts:
        parts = li.split()
        if len(parts) >= 2:
            num, label = parts[0], " ".join(parts[1:]).lower()
            if "post" in label: posts = num
            elif "follower" in label: followers = num
            elif "following" in label: following = num

    if followers == "N/A" and len(counts) >= 3: posts, followers, following = counts[0], counts[1], counts[2]

    nick = _clean_ig_title(raw_title, username)
    bio = _clean_ig_bio(desc or meta_desc, username)

    table = Table(box=box.ROUNDED, border_style=C, title=f"[bold {W}]Instagram @{username}[/]", title_justify="center", show_header=False)
    table.add_column("Propiedad", style=C, justify="right", width=18)
    table.add_column("Valor", style=W, justify="left", width=45)

    table.add_row("Nombre", nick)
    table.add_row("Perfil", url)
    table.add_row("Avatar", avatar)
    table.add_row("Verificado", "[green]Si[/green]" if '"is_verified":true' in str(data) else "No")
    table.add_row("Cuenta privada", "[yellow]Si[/yellow]" if '"is_private":true' in str(data) else "No")
    table.add_row("Bio", bio[:200])
    table.add_row("Seguidores", followers)
    table.add_row("Siguiendo", following)
    table.add_row("Posts", posts)

    console.print(Align.center(table))

def menu():
    os_name = _get_os_name()
    while True:
        _clear()
        draw_banner()
        
        print(f"\033[1;31m[1]\033[0m \033[1;37mTikTok Lookup\033[0m")
        print(f"\033[1;31m[2]\033[0m \033[1;37mInstagram Lookup\033[0m")
        print(f"\033[1;31m[0]\033[0m \033[1;37mSalir\033[0m\n")

        print(f"\033[1;31m┌──\033[0m(\033[1;31mSocialLookup\033[0m㉿\033[1;31m{os_name}\033[0m)")
        print(f"\033[1;31m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)

        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear(); draw_banner()
            print("\n\033[1;37mHasta luego, espero que vuelvas\033[0m\n")
            break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;31mIngresa el Username de TikTok (sin @):\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip()
            if target:
                lookup_tiktok(target)
                input("\n\033[1;37mPresiona Enter para volver...\033[0m")
        elif choice == "2":
            _clear(); draw_banner()
            print("\n\033[1;31mIngresa el Username de Instagram (sin @):\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip()
            if target:
                lookup_instagram(target)
                input("\n\033[1;37mPresiona Enter para volver...\033[0m")
        else:
            print("\033[1;31mOpcion invalida.\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    menu()
