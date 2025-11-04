#!/usr/bin/env python3

import os
import sys

# Adiciona o diretório atual ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config, setup_logging
from backup import DatabaseBackup

def test_database_listing():
    """Testa a funcionalidade de listagem automática de databases"""
    
    # Simula configuração sem DB_NAMES
    os.environ['DB_NAMES'] = ''
    
    logger = setup_logging()
    logger.info("=== TESTE DE LISTAGEM AUTOMÁTICA DE DATABASES ===")
    
    try:
        Config.validate()
        backup_manager = DatabaseBackup()
        
        # Testa listagem de databases
        logger.info("Testando listagem de databases...")
        databases = backup_manager.get_all_databases()
        
        if databases:
            logger.info(f"✓ Encontrados {len(databases)} databases:")
            for db in databases:
                logger.info(f"  - {db}")
        else:
            logger.warning("⚠ Nenhum database encontrado")
            
    except Exception as e:
        logger.error(f"✗ Erro no teste: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Este é um script de teste para verificar a listagem automática de databases.")
    print("Para funcionar, é necessário ter PostgreSQL configurado e acessível.")
    print("\nExecute apenas se tiver certeza da configuração!")
    
    response = input("\nDeseja continuar? (y/N): ")
    if response.lower() == 'y':
        success = test_database_listing()
        sys.exit(0 if success else 1)
    else:
        print("Teste cancelado.")
        sys.exit(0)