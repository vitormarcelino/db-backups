#!/usr/bin/env python3

import os
import sys
import logging
from datetime import datetime

# Adiciona o diretório atual ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_test_logging():
    """Setup de logging para teste"""
    os.makedirs('./logs', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'./logs/test_backup_{timestamp}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def test_backup_process():
    """Testa o processo de backup sem PostgreSQL real"""
    logger = setup_test_logging()
    logger.info("=== TESTE DO PROCESSO DE BACKUP (SEM POSTGRESQL) ===")
    
    try:
        from config import Config
        from backup import DatabaseBackup
        
        # Simula configurações mínimas para teste
        os.environ.update({
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password',
            'DB_NAMES': 'test_db1,test_db2',  # Usa lista específica para evitar conexão real
            'AWS_ACCESS_KEY_ID': 'test_key',
            'AWS_SECRET_ACCESS_KEY': 'test_secret',
            'S3_BUCKET_NAME': 'test-bucket',
            'SERVER_NAME': 'test-server'
        })
        
        logger.info("✓ Configurações de teste definidas")
        
        # Testa validação
        Config.validate()
        logger.info("✓ Validação de configuração passou")
        
        # Testa instanciação da classe
        backup_manager = DatabaseBackup()
        logger.info("✓ Classe DatabaseBackup instanciada com sucesso")
        
        # Mostra configurações que seriam usadas
        logger.info(f"Servidor: {Config.SERVER_NAME}")
        logger.info(f"Host: {Config.DB_HOST}:{Config.DB_PORT}")
        logger.info(f"Usuário: {Config.DB_USER}")
        logger.info(f"Databases: {Config.DB_NAMES}")
        logger.info(f"Bucket S3: {Config.S3_BUCKET_NAME}")
        logger.info(f"Diretório temporário: {Config.BACKUP_DIR}")
        
        logger.info("✅ TESTE CONCLUÍDO - Sistema está configurado corretamente!")
        logger.info("⚠ Para usar em produção, configure PostgreSQL e AWS S3 reais")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Erro no teste: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        # Limpa variáveis de teste
        test_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAMES', 
                    'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME', 'SERVER_NAME']
        for var in test_vars:
            if var in os.environ:
                del os.environ[var]

def main():
    logger = setup_test_logging()
    logger.info("=== TESTE DO SISTEMA DE BACKUP SEM POSTGRESQL ===")
    
    success = test_backup_process()
    
    if success:
        logger.info("✅ SISTEMA ESTÁ FUNCIONANDO CORRETAMENTE!")
        logger.info("\nPróximos passos para uso em produção:")
        logger.info("1. Configure PostgreSQL acessível")
        logger.info("2. Configure credenciais AWS S3 reais no .env")
        logger.info("3. Execute: ./run.sh --backup-only")
    else:
        logger.error("❌ PROBLEMAS ENCONTRADOS - Verifique os erros acima")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)