#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

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

python main.py "$@"