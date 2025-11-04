#!/usr/bin/env python3

import os
import sys
import logging
from datetime import datetime

# Adiciona o diretório atual ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_test_logging():
    """Setup de logging para teste sem permissões administrativas"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Apenas saída no console
        ]
    )
    return logging.getLogger(__name__)

def test_imports():
    """Testa se todos os módulos podem ser importados"""
    logger = setup_test_logging()
    logger.info("=== TESTE DE IMPORTAÇÃO DE MÓDULOS ===")
    
    try:
        from config import Config
        logger.info("✓ Módulo config importado com sucesso")
        
        from backup import DatabaseBackup
        logger.info("✓ Módulo backup importado com sucesso")
        
        from retention import BackupRetentionManager
        logger.info("✓ Módulo retention importado com sucesso")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro na importação: {e}")
        return False

def test_config_validation():
    """Testa validação de configuração sem arquivo .env"""
    logger = setup_test_logging()
    logger.info("=== TESTE DE VALIDAÇÃO DE CONFIG ===")
    
    try:
        from config import Config
        
        # Simula algumas variáveis de ambiente mínimas para teste
        os.environ['DB_PASSWORD'] = 'test_password'
        os.environ['AWS_ACCESS_KEY_ID'] = 'test_key'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'test_secret'
        os.environ['S3_BUCKET_NAME'] = 'test-bucket'
        os.environ['DB_NAMES'] = ''  # Teste sem DB_NAMES
        
        Config.validate()  # Deve passar agora que removemos a validação obrigatória de DB_NAMES
        logger.info("✓ Validação de config passou (modo automático de databases)")
        
        # Testa com DB_NAMES configurado
        os.environ['DB_NAMES'] = 'test1,test2'
        Config.validate()
        logger.info("✓ Validação de config passou (modo manual de databases)")
        
        # Mostra configurações
        logger.info(f"Servidor: {Config.SERVER_NAME}")
        logger.info(f"Host DB: {Config.DB_HOST}")
        logger.info(f"Databases: {Config.DB_NAMES}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro na validação: {e}")
        return False
    finally:
        # Limpa variáveis de teste
        for var in ['DB_PASSWORD', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME', 'DB_NAMES']:
            if var in os.environ:
                del os.environ[var]

def main():
    logger = setup_test_logging()
    logger.info("=== SISTEMA DE BACKUP - TESTE DE DEPENDÊNCIAS ===")
    
    tests = [
        ("Importação de Módulos", test_imports),
        ("Validação de Configuração", test_config_validation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        else:
            logger.error(f"Teste '{test_name}' falhou")
    
    logger.info(f"\n=== RESULTADO DOS TESTES ===")
    logger.info(f"Testes executados: {total}")
    logger.info(f"Testes aprovados: {passed}")
    logger.info(f"Testes falharam: {total - passed}")
    
    if passed == total:
        logger.info("✅ TODOS OS TESTES PASSARAM - Sistema está pronto!")
        return True
    else:
        logger.error("❌ ALGUNS TESTES FALHARAM - Verifique as dependências")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)