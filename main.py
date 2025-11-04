#!/usr/bin/env python3

import sys
import argparse
from datetime import datetime
from config import Config, setup_logging

def run_backup():
    from backup import DatabaseBackup
    
    logger = setup_logging()
    logger.info("=== INICIANDO PROCESSO DE BACKUP ===")
    
    try:
        backup_manager = DatabaseBackup()
        successful, failed = backup_manager.backup_all_databases()
        
        if failed:
            logger.error(f"Backup concluído com falhas. {len(failed)} databases falharam")
            return False
        else:
            logger.info(f"Backup concluído com sucesso. {len(successful)} databases salvos")
            return True
            
    except Exception as e:
        logger.error(f"Erro crítico no backup: {e}")
        return False

def run_retention():
    from retention import BackupRetentionManager
    
    logger = setup_logging()
    logger.info("=== INICIANDO PROCESSO DE RETENÇÃO ===")
    
    try:
        retention_manager = BackupRetentionManager()
        deleted_count = retention_manager.clean_expired_backups()
        
        logger.info(f"Retenção concluída. {deleted_count or 0} arquivos removidos")
        return True
        
    except Exception as e:
        logger.error(f"Erro crítico na retenção: {e}")
        return False

def run_full_process():
    logger = setup_logging()
    start_time = datetime.now()
    
    logger.info("=== INICIANDO PROCESSO COMPLETO DE BACKUP E RETENÇÃO ===")
    
    backup_success = run_backup()
    retention_success = run_retention()
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info(f"=== PROCESSO COMPLETO FINALIZADO ===")
    logger.info(f"Duração total: {duration}")
    logger.info(f"Backup: {'✓ SUCESSO' if backup_success else '✗ FALHA'}")
    logger.info(f"Retenção: {'✓ SUCESSO' if retention_success else '✗ FALHA'}")
    
    return backup_success and retention_success

def main():
    parser = argparse.ArgumentParser(
        description='Sistema de Backup Automático PostgreSQL para S3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                    - Executa backup e retenção
  python main.py --backup-only      - Executa apenas backup
  python main.py --retention-only   - Executa apenas retenção
  python main.py --help            - Mostra esta ajuda
        """
    )
    
    parser.add_argument(
        '--backup-only',
        action='store_true',
        help='Executa apenas o processo de backup'
    )
    
    parser.add_argument(
        '--retention-only',
        action='store_true',
        help='Executa apenas o processo de retenção'
    )
    
    args = parser.parse_args()
    
    try:
        Config.validate()
    except ValueError as e:
        logger = setup_logging()
        logger.error(f"Erro de configuração: {e}")
        logger.error("Verifique o arquivo .env e certifique-se de que todas as variáveis necessárias estão definidas")
        sys.exit(1)
    
    success = True
    
    if args.backup_only:
        success = run_backup()
    elif args.retention_only:
        success = run_retention()
    else:
        success = run_full_process()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()