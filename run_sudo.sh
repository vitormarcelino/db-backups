#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Verifica se precisa de sudo para escrever em /var/log
if [ ! -w "/var/log" ]; then
    echo "⚠️  Necessário permissão sudo para escrever logs em /var/log"
    echo "Executando com sudo..."
    exec sudo -E "$0" "$@"
fi

# Se chegou aqui, tem permissão ou já está com sudo
if [ ! -f ".env" ]; then
    echo "Erro: Arquivo .env não encontrado!"
    echo "Copie .env.example para .env e configure as variáveis necessárias"
    exit 1
fi

if [ ! -f "venv/bin/activate" ]; then
    echo "Criando ambiente virtual Python..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ ! -f "venv/lib/python*/site-packages/boto3" ]; then
    echo "Instalando dependências Python..."
    pip install -r requirements.txt
fi

# Passa todas as variáveis de ambiente do usuário original
python main.py "$@"