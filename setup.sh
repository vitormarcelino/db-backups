#!/bin/bash

echo "=================================="
echo "   SETUP DO SISTEMA DE BACKUP"
echo "=================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar Python 3
echo "Verificando Python 3..."
if command_exists python3; then
    echo "✓ Python 3 encontrado: $(python3 --version)"
else
    echo "✗ Python 3 não encontrado. Instale Python 3.6+ e tente novamente."
    exit 1
fi

# Verificar PostgreSQL client tools
echo "Verificando PostgreSQL client tools..."
if command_exists psql && command_exists pg_dump; then
    echo "✓ PostgreSQL client tools encontrados"
else
    echo "⚠ PostgreSQL client tools não encontrados"
    echo "  Instale com: sudo apt install postgresql-client"
    read -p "Continuar mesmo assim? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Verificar/instalar python3-venv
echo "Verificando python3-venv..."
if python3 -m venv --help >/dev/null 2>&1; then
    echo "✓ python3-venv disponível"
else
    echo "⚠ python3-venv não encontrado"
    echo "Tentando instalar..."
    if command_exists apt; then
        sudo apt install python3-venv -y
    else
        echo "✗ Não foi possível instalar python3-venv automaticamente"
        echo "  Instale manualmente e execute este script novamente"
        exit 1
    fi
fi

# Criar ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "✗ Erro ao criar ambiente virtual"
        exit 1
    fi
    echo "✓ Ambiente virtual criado"
else
    echo "✓ Ambiente virtual já existe"
fi

# Instalar dependências
echo "Instalando dependências Python..."
source venv/bin/activate
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "✗ Erro ao instalar dependências"
    exit 1
fi
echo "✓ Dependências instaladas com sucesso"

# Criar arquivo .env se não existir
if [ ! -f ".env" ]; then
    echo "Criando arquivo .env..."
    cp .env.example .env
    echo "✓ Arquivo .env criado a partir do exemplo"
    echo "⚠ IMPORTANTE: Edite o arquivo .env com suas configurações antes de usar!"
else
    echo "✓ Arquivo .env já existe"
fi

# Criar diretório de logs local
mkdir -p logs
echo "✓ Diretório de logs criado: ./logs/"

# Testar instalação
echo "Testando instalação..."
python3 test_dependencies.py
if [ $? -eq 0 ]; then
    echo "✅ SETUP CONCLUÍDO COM SUCESSO!"
    echo ""
    echo "Próximos passos:"
    echo "1. Edite o arquivo .env com suas configurações"
    echo "2. Execute: ./run.sh --help para ver as opções"
    echo "3. Teste com: ./run.sh --backup-only (após configurar .env)"
else
    echo "❌ ERRO NO SETUP - Verifique as mensagens acima"
    exit 1
fi