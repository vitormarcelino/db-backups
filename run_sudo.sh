#!/bin/bash

# Wrapper para executar com sudo (logs em /var/log)
# Use este script quando quiser logs em /var/log

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

if [ "$EUID" -ne 0 ]; then
    echo "🔐 Executando com sudo para logs em /var/log..."
    exec sudo -E "$0" "$@"
fi

# Se chegou aqui, já está com sudo
./run.sh "$@"