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

# Função para detectar sistema operacional
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        echo $ID
    else
        echo "unknown"
    fi
}

# Verificar Python 3
echo "Verificando Python 3..."
if command_exists python3; then
    echo "✓ Python 3 encontrado: $(python3 --version)"
else
    echo "✗ Python 3 não encontrado. Instale Python 3.6+ e tente novamente."
    exit 1
fi

# Verificar/instalar PostgreSQL client tools
echo "Verificando PostgreSQL client tools..."
if command_exists psql && command_exists pg_dump; then
    echo "✓ PostgreSQL client tools encontrados"
else
    echo "⚠ PostgreSQL client tools não encontrados"
    echo "Instalando PostgreSQL client tools..."
    
    OS=$(detect_os)
    case $OS in
        ubuntu|debian)
            echo "Sistema detectado: Ubuntu/Debian"
            sudo apt update -qq
            sudo apt install -y postgresql-client
            ;;
        centos|rhel|fedora)
            echo "Sistema detectado: CentOS/RHEL/Fedora"
            if command_exists dnf; then
                sudo dnf install -y postgresql
            elif command_exists yum; then
                sudo yum install -y postgresql
            fi
            ;;
        *)
            echo "❌ Sistema operacional não reconhecido: $OS"
            echo "Instale manualmente:"
            echo "  Ubuntu/Debian: sudo apt install postgresql-client"
            echo "  CentOS/RHEL: sudo yum install postgresql"
            read -p "Continuar mesmo assim? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac
    
    # Verifica se instalação foi bem-sucedida
    if command_exists psql && command_exists pg_dump; then
        echo "✓ PostgreSQL client tools instalados com sucesso"
    else
        echo "⚠ Falha na instalação do PostgreSQL client"
        read -p "Continuar mesmo assim? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
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

# Criar/recriar ambiente virtual se não existir ou estiver corrompido
if [ ! -f "venv/bin/activate" ]; then
    if [ -d "venv" ]; then
        echo "Removendo ambiente virtual corrompido..."
        rm -rf venv
    fi
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
if [ $? -ne 0 ]; then
    echo "✗ Erro ao ativar ambiente virtual"
    exit 1
fi

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

# Criar diretórios necessários
echo "Criando diretórios necessários..."
mkdir -p logs
mkdir -p /tmp/db_backups
echo "✓ Diretórios criados"

# Configurar permissões para logs em /var/log
echo "Configurando permissões para logs..."
if [ -w "/var/log" ]; then
    echo "✓ Permissão para escrever em /var/log: OK"
else
    echo "⚠ Sem permissão para /var/log - logs serão salvos em ./logs/"
fi

# Testar instalação
echo "Executando testes de validação..."
python3 test_dependencies.py
if [ $? -eq 0 ]; then
    echo "✓ Teste de dependências: PASSOU"
else
    echo "❌ Teste de dependências: FALHOU"
    exit 1
fi

# Teste adicional sem PostgreSQL
python3 test_backup_dry_run.py >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✓ Teste de configuração: PASSOU"
else
    echo "⚠ Teste de configuração: FALHOU (verifique .env)"
fi

echo ""
echo "✅ SETUP CONCLUÍDO COM SUCESSO!"
echo "=================================="
echo "📋 PRÓXIMOS PASSOS:"
echo ""
echo "1. 🔧 Configure o arquivo .env:"
echo "   nano .env"
echo ""
echo "2. 🧪 Teste a configuração:"
echo "   python3 test_s3_connection.py"
echo ""
echo "3. 🚀 Execute o backup:"
echo "   sudo ./run.sh --backup-only     # Logs em /var/log"
echo "   ./run.sh --backup-only          # Logs em ./logs"
echo ""
echo "4. ⏰ Configure cron (opcional):"
echo "   sudo crontab -e"
echo "   # Adicione: 0 2 * * * /caminho/para/run.sh"
echo ""
echo "5. 📊 Verifique status:"
echo "   ./status.sh"
echo "=================================="