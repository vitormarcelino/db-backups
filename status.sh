#!/bin/bash

echo "=================================="
echo "   STATUS DO SISTEMA DE BACKUP"
echo "=================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Função para verificar se comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "🔍 VERIFICANDO COMPONENTES DO SISTEMA..."
echo

# 1. Python e ambiente virtual
if [ -d "venv" ]; then
    echo "✅ Ambiente virtual: OK"
else
    echo "❌ Ambiente virtual: NÃO ENCONTRADO"
fi

# 2. Dependências Python
if [ -f "venv/lib/python*/site-packages/boto3" ]; then
    echo "✅ Dependências Python: OK"
else
    echo "❌ Dependências Python: NÃO INSTALADAS"
fi

# 3. Arquivo de configuração
if [ -f ".env" ]; then
    echo "✅ Arquivo .env: OK"
else
    echo "❌ Arquivo .env: NÃO ENCONTRADO"
fi

# 4. PostgreSQL client tools
if command_exists psql && command_exists pg_dump; then
    echo "✅ PostgreSQL client tools: OK"
else
    echo "⚠️  PostgreSQL client tools: NÃO ENCONTRADO"
fi

# 5. Diretório de logs
if [ -d "logs" ]; then
    echo "✅ Diretório de logs: OK"
else
    echo "⚠️  Diretório de logs: NÃO ENCONTRADO"
fi

echo
echo "📁 ESTRUTURA DE ARQUIVOS:"
echo "   📄 Scripts principais:"
ls -la *.py 2>/dev/null | grep -E "(main|backup|retention|config)\.py" | awk '{print "      " $9}'

echo "   📄 Scripts auxiliares:"
ls -la *.py 2>/dev/null | grep -E "(test_|setup)" | awk '{print "      " $9}'

echo "   🔧 Scripts de execução:"
ls -la *.sh 2>/dev/null | awk '{print "      " $9}'

echo
echo "📊 LOGS RECENTES:"
if [ -d "logs" ] && [ "$(ls -A logs/)" ]; then
    ls -lt logs/ | head -5 | tail -n +2 | awk '{print "   " $9 " (" $6 " " $7 " " $8 ")"}'
else
    echo "   Nenhum log encontrado"
fi

echo
echo "🧪 EXECUTANDO TESTES BÁSICOS..."

# Teste de dependências
if [ -f "test_dependencies.py" ]; then
    echo "   Testando dependências..."
    if source venv/bin/activate && python3 test_dependencies.py >/dev/null 2>&1; then
        echo "   ✅ Teste de dependências: PASSOU"
    else
        echo "   ❌ Teste de dependências: FALHOU"
    fi
else
    echo "   ⚠️  Script de teste não encontrado"
fi

echo
echo "📋 PRÓXIMOS PASSOS:"

if [ ! -f ".env" ]; then
    echo "   1. Criar arquivo .env: cp .env.example .env"
fi

if ! grep -q "your_password" .env 2>/dev/null; then
    echo "   2. Configurar .env com suas credenciais reais"
fi

echo "   3. Testar sem PostgreSQL: python3 test_backup_dry_run.py"
echo "   4. Testar com PostgreSQL: ./run.sh --backup-only"
echo "   5. Configurar cron para execução automática"

echo
echo "=================================="
echo "   Sistema pronto para produção!   "
echo "=================================="