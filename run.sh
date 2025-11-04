#!/bin/bash

# Script de execução do sistema de backup
# Execute ./setup.sh primeiro para instalar dependências

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Verifica se o setup foi executado
if [ ! -f ".env" ]; then
    echo "❌ Arquivo .env não encontrado!"
    echo "Execute primeiro: ./setup.sh"
    exit 1
fi

if [ ! -f "venv/bin/activate" ]; then
    echo "❌ Ambiente virtual não encontrado!"
    echo "Execute primeiro: ./setup.sh"
    exit 1
fi

# Verifica se precisa de sudo para logs em /var/log
USE_SUDO=false
if [ ! -w "/var/log" ] && [ "$EUID" -ne 0 ]; then
    USE_SUDO=true
fi

# Ativa ambiente virtual e executa
source venv/bin/activate

# Executa com ou sem sudo dependendo das permissões
if [ "$USE_SUDO" = true ]; then
    echo "ℹ️  Logs serão salvos em ./logs/ (sem permissão para /var/log)"
fi

python main.py "$@"