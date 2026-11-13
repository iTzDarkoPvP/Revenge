import os, sys, platform, time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.align import Align

try:
    import phonenumbers
    from phonenumbers import geocoder, carrier, timezone, number_type
    try:
        from phonenumbers import PhoneNumberType
    except ImportError:
        PhoneNumberType = None
    PHONENUMBERS_OK = True
except ImportError:
    phonenumbers = None
    geocoder = None
    carrier = None
    timezone = None
    number_type = None
    PhoneNumberType = None
    PHONENUMBERS_OK = False

console = Console(highlight=False)

C1 = "#00CED1"
C2 = "#20B2AA"
C3 = "#008080"
W1 = "#FFFFFF"

def _clear(): os.system('cls' if os.name == 'nt' else 'clear')

def _get_os_name():
    if "com.termux" in os.environ.get("PREFIX", ""): return "termux"
    if os.name == "nt": return "powershell" if "PS" in os.environ.get("PROMPT", "") else "cmd"
    return platform.system().lower()

def draw_banner():
    banner_texto = (
        f"\n[bold {C1}]██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗[/bold {C1}]\n"
        f"[bold {C1}]██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝[/bold {C1}]\n"
        f"[bold {W1}]██████╔╝███████║██║   ██║██╔██╗ ██║█████╗  [/bold {W1}]\n"
        f"[bold {W1}]██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║██╔══╝  [/bold {W1}]\n"
        f"[bold {C2}]██║     ██║  ██║╚██████╔╝██║ ╚████║███████╗[/bold {C2}]\n"
        f"[bold {C2}]╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝[/bold {C2}]\n"
        f"\n[dim {W1}]     Phone Lookup By DarkoDevv v1.0     [/dim {W1}]"
    )
    panel = Panel(
        Align.center(banner_texto, vertical="middle"),
        border_style=C1, box=box.ROUNDED, width=58, padding=(0, 1)
    )
    console.print(Align.center(panel))

def _get_type_names():
    if PhoneNumberType is None:
        return {}
    return {
        PhoneNumberType.MOBILE: "Movil",
        PhoneNumberType.FIXED_LINE: "Fijo",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "Fijo o Movil",
        PhoneNumberType.TOLL_FREE: "Numero gratuito",
        PhoneNumberType.PREMIUM_RATE: "Tarifa premium",
        PhoneNumberType.SHARED_COST: "Costo compartido",
        PhoneNumberType.VOIP: "VoIP",
        PhoneNumberType.PERSONAL_NUMBER: "Personal",
        PhoneNumberType.PAGER: "Pager",
        PhoneNumberType.UAN: "UAN",
        PhoneNumberType.VOICEMAIL: "Voicemail",
        PhoneNumberType.UNKNOWN: "Desconocido",
    }

def lookup_number(raw_number):
    if not PHONENUMBERS_OK:
        print("\033[1;31m[-] Falta la libreria 'phonenumbers'.\033[0m")
        print("\033[1;33m[!] Instala con: pip install phonenumbers\033[0m")
        return

    print(f"\n\033[1;36m[+] Analizando numero: {raw_number}\033[0m\n")

    raw_clean = raw_number.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not raw_clean.startswith("+"):
        print("\033[1;33m[!] Recomendacion: usa el formato internacional (+54..., +1..., +34...)\033[0m\n")

    try:
        num = phonenumbers.parse(raw_clean, None)
    except phonenumbers.NumberParseException as e:
        print(f"\033[1;31m[-] Numero invalido: {e}\033[0m")
        print("\033[1;33m[!] Ejemplo: +5491123456789 o +14155552671\033[0m")
        return

    if not phonenumbers.is_valid_number(num):
        print("\033[1;31m[-] El numero no es valido segun el plan internacional.\033[0m")
        if phonenumbers.is_possible_number(num):
            print("\033[1;33m[!] Pero parece posible (puede estar incompleto).\033[0m")
        return

    region = phonenumbers.region_code_for_number(num) or "N/A"
    country = geocoder.description_for_number(num, "es") or geocoder.description_for_number(num, "en") or "Desconocido"
    carrier_name = carrier.name_for_number(num, "es") or carrier.name_for_number(num, "en") or "Desconocida"

    tz = timezone.time_zones_for_number(num)
    tz_str = ", ".join(tz) if tz else "N/A"

    tipo = number_type(num)
    tipo_str = _get_type_names().get(tipo, "Desconocido")

    formato_intl = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    formato_e164 = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)
    formato_nacional = phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.NATIONAL)

    table = Table(
        title="Informacion del Numero",
        box=box.ROUNDED, border_style=C1,
        title_style=f"bold {C1}", header_style=f"bold {C2}"
    )
    table.add_column("Propiedad", style=C1, justify="left", width=22)
    table.add_column("Valor", style=W1, justify="left", width=45)

    table.add_row("Numero (input)", raw_number)
    table.add_row("Formato Internacional", formato_intl)
    table.add_row("Formato E.164", formato_e164)
    table.add_row("Formato Nacional", formato_nacional)
    table.add_row("Codigo de pais", f"+{num.country_code}")
    table.add_row("Region", region)
    table.add_row("Pais / Ubicacion", country)
    table.add_row("Operadora", carrier_name)
    table.add_row("Tipo de linea", tipo_str)
    table.add_row("Zona horaria", tz_str)

    console.print(Align.center(table))

    print(f"\033[1;32m[+] Google: https://www.google.com/search?q=%22{formato_e164}%22\033[0m")
    print(f"\033[1;32m[+] Truecaller: https://www.truecaller.com/search/{region.lower()}/{formato_e164.replace('+', '')}\033[0m")

def menu():
    os_name = _get_os_name()
    while True:
        _clear()
        draw_banner()
        print(f"\n\033[1;36m[1]\033[0m Analizar numero de telefono")
        print(f"\033[1;36m[0]\033[0m Salir\n")

        print(f"\033[1;36m┌──\033[0m(\033[1;36mPhoneLookup\033[0m㉿\033[1;36m{os_name}\033[0m)")
        print(f"\033[1;36m└─\033[0m\033[1;37m$\033[0m ", end="", flush=True)

        choice = sys.stdin.readline().strip()
        print("\033[F\033[K", end="", flush=True)

        if choice == "0":
            _clear(); draw_banner()
            print("\n\033[1;37mHasta luego, espero que vuelvas\033[0m\n")
            break
        elif choice == "1":
            _clear(); draw_banner()
            print("\n\033[1;36mIngresa el numero (ej: +5491123456789):\033[0m ", end="", flush=True)
            target = sys.stdin.readline().strip()
            if target:
                print()
                lookup_number(target)
                input("\nPresiona Enter para volver...")
        else:
            print("\033[1;31mOpcion invalida.\033[0m")
            time.sleep(1)

if __name__ == "__main__":
    menu()
