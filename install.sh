#!/bin/bash

C1="\033[1;31m"
C2="\033[1;37m"
C3="\033[1;33m"
NC="\033[0m"

clear
echo -e "${C1}"
echo "  ██╗███╗   ██╗███████╗████████╗ █████╗ ██╗     ██╗     "
echo "  ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗██║     ██║     "
echo "  ██║██╔██╗ ██║███████╗   ██║   ███████║██║     ██║     "
echo "  ██║██║╚██╗██║╚════██║   ██║   ██╔══██║██║     ██║     "
echo "  ██║██║ ╚████║███████║   ██║   ██║  ██║███████╗███████╗"
echo "  ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝"
echo -e "${NC}"
echo -e "${C2}             Revenge KIT Installer${NC}\n"

if [ -n "$PREFIX" ] && [[ "$PREFIX" == *"com.termux"* ]]; then
    OS="termux"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="mac"
else
    OS="unknown"
fi

echo -e "${C3}[+] Sistema detectado: ${OS}${NC}"

if [ "$OS" == "termux" ]; then
    echo -e "\n${C1}[+] Instalando dependencias del sistema (Termux)...${NC}"
    sleep 1
    pkg update -y && pkg upgrade -y
    pkg install python git binutils libsodium rust clang make openssl libffi sshpass -y
elif [ "$OS" == "linux" ]; then
    echo -e "\n${C1}[+] Instalando dependencias del sistema (Linux)...${NC}"
    sudo apt update -y
    sudo apt install python3 python3-pip git binutils libsodium-dev build-essential libssl-dev libffi-dev sshpass -y
elif [ "$OS" == "mac" ]; then
    echo -e "\n${C1}[+] Instalando dependencias del sistema (macOS)...${NC}"
    brew install python git libsodium openssl
fi

echo -e "\n${C1}[+] Actualizando pip y setuptools...${NC}"
python3 -m pip install --upgrade pip setuptools wheel

echo -e "\n${C1}[+] Instalando librerías de Python...${NC}"
python3 -m pip install rich requests dnspython asyncssh pexpect

echo -e "\n${C1}[+] Instalando Playwright...${NC}"
if [ "$OS" == "termux" ]; then
    pkg install x11-repo -y
    pkg install playwright -y 2>/dev/null || true
fi
python3 -m pip install playwright
python3 -m playwright install chromium

echo -e "\n${C1}[+] Verificando PyNaCl...${NC}"
python3 -c "import nacl" 2>/dev/null
if [ $? -ne 0 ]; then
    if [ "$OS" == "termux" ]; then
        SODIUM_INSTALL=system python3 -m pip install pynacl --no-build-isolation 2>/dev/null || true
    else
        python3 -m pip install pynacl
    fi
fi

echo -e "\n${C2}======================================================${NC}"
echo -e "${C2}   ¡INSTALACIÓN COMPLETA!${NC}"
echo -e "${C2}   Ejecuta: python3 main.py${NC}"
echo -e "${C2}======================================================${NC}"
