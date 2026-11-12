import os, sys, time, random, smtplib, socket, concurrent.futures
import dns.resolver
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich import box
from rich.align import Align

console = Console(highlight=False)

# Configuración DNS Rápida
resolver = dns.resolver.Resolver(configure=False)
resolver.nameservers = ['8.8.8.8', '1.1.1.1']
resolver.timeout = 3
resolver.lifetime = 3

_HITS_DIR = "GmailHits"
if not os.path.exists(_HITS_DIR): os.makedirs(_HITS_DIR)

def draw_banner():
    banner = (
        "\n[bold #4285F4] ██████╗ ███╗   ███╗ █████╗ ██╗██╗     [/bold #4285F4]\n"
        "[bold #EA4335]██╔════╝ ████╗ ████║██╔══██╗██║██║     [/bold #EA4335]\n"
        "[bold #FBBC05]██║  ███╗██╔████╔██║███████║██║██║     [/bold #FBBC05]\n"
        "[bold #34A853]██║   ██║██║╚██╔╝██║██╔══██║██║██║     [/bold #34A853]\n"
        "[bold white]╚██████╔╝██║ ╚═╝ ██║██║  ██║██║███████╗[/bold white]\n"
        "[bold white] ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚══════╝[/bold white]\n"
        "[dim white]       Gmail Checker VPS Edition[/dim white]"
    )
    console.print(Align.center(Panel(Align.center(banner), border_style="#4285F4", box=box.ROUNDED, width=60)))

def check_email(email):
    domain = email.split('@')[1]
    try:
        records = resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)
    except Exception:
        return "ERR", "Sin DNS"
        
    try:
        server = smtplib.SMTP(timeout=5)
        server.connect(mx_record, 25)
        server.helo('localhost')
        server.mail('checker@verify.com')
        code, message = server.rcpt(str(email))
        server.quit()
        
        if code == 250:
            return "LIVE", "Válido"
        elif code == 550:
            return "DEAD", ""
        else:
            return "ERR", f"Code {code}"
    except Exception as e:
        return "ERR", "Timeout"

def main():
    os.system('clear')
    draw_banner()
    
    print("\n\033[1;34m[1]\033[0m Escanear Prefijo (Ej: devzynx)")
    print("\033[1;34m[0]\033[0m Salir\n")
    
    print("\033[1;34m┌──\033[0m(\033[1;34mGmailVPS\033[0m㉿\033[1;34mroot\033[0m)")
    print("\033[1;34m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)
    choice = input().strip()

    if choice == "0":
        sys.exit()
    elif choice == "1":
        os.system('clear')
        draw_banner()
        print("\n\033[1;34mPrefijo (sin @gmail.com):\033[0m ", end="", flush=True)
        prefix = input().strip()
        print("\033[1;34mLímite de escaneo:\033[0m ", end="", flush=True)
        limit = int(input().strip())
        
        # Generar lista de correos
        emails = [f"{prefix}{i}@gmail.com" for i in range(1, limit + 1)]
        hits = 0
        output_file = os.path.join(_HITS_DIR, f"hits_{prefix}.txt")
        
        print(f"\n\033[2m▶ Escaneando {limit} correos usando 10 hilos paralelos...\033[0m\n")
        
        # Usar Progress Bar de Rich para ver el avance
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[bold blue]{task.completed}/{task.total}"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Escaneando...", total=limit)
            
            # Paralelismo (10 hilos a la vez)
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(check_email, emails)
                
                for email, (status, info) in zip(emails, results):
                    progress.update(task, advance=1)
                    
                    if status == "LIVE":
                        hits += 1
                        with open(output_file, "a") as f:
                            f.write(f"{email}\n")
                        # Para que la barra no se dañe, usamos console.print
                        console.print(f"  \033[1;32m●\033[0m \033[1;32m{email}\033[0m", highlight=False)
        
        print(f"\n\033[1;34m■ Completado.\033[0m Encontrados: \033[1;32m{hits}\033[0m LIVE.")
        print(f"\033[2mGuardados en: {output_file}\033[0m")
        input("\nPresiona Enter para volver al menú...")
        main()

if __name__ == "__main__":
    main()