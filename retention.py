import boto3
from datetime import datetime, timedelta
from config import Config, setup_logging

class BackupRetentionManager:
    def __init__(self):
        self.logger = setup_logging()
        Config.validate()
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
    
    def list_backup_objects(self):
        try:
            prefix = f"{Config.SERVER_NAME}/"
            response = self.s3_client.list_objects_v2(
                Bucket=Config.S3_BUCKET_NAME,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                self.logger.info(f"Nenhum backup encontrado no S3 para o servidor {Config.SERVER_NAME}")
                return []
            
            objects = response['Contents']
            self.logger.info(f"Encontrados {len(objects)} objetos de backup no S3 para o servidor {Config.SERVER_NAME}")
            
            return objects
            
        except Exception as e:
            self.logger.error(f"Erro ao listar objetos no S3: {e}")
            raise
    
    def calculate_retention_date(self):
        retention_date = datetime.now() - timedelta(days=Config.BACKUP_RETENTION_DAYS)
        self.logger.info(f"Data limite para retenção: {retention_date.strftime('%Y-%m-%d %H:%M:%S')}")
        return retention_date
    
    def get_expired_backups(self, objects, retention_date):
        expired_objects = []
        
        for obj in objects:
            last_modified = obj['LastModified'].replace(tzinfo=None)
            
            if last_modified < retention_date:
                expired_objects.append({
                    'Key': obj['Key'],
                    'LastModified': last_modified,
                    'Size': obj['Size']
                })
        
        return expired_objects
    
    def delete_expired_backups(self, expired_objects):
        if not expired_objects:
            self.logger.info("Nenhum backup expirado encontrado")
            return []
        
        deleted_objects = []
        total_size_freed = 0
        
        self.logger.info(f"Iniciando exclusão de {len(expired_objects)} backups expirados")
        
        for obj in expired_objects:
            try:
                self.s3_client.delete_object(
                    Bucket=Config.S3_BUCKET_NAME,
                    Key=obj['Key']
                )
                
                deleted_objects.append(obj)
                total_size_freed += obj['Size']
                
                self.logger.info(f"✓ Removido: {obj['Key']} (modificado em {obj['LastModified']})")
                
            except Exception as e:
                self.logger.error(f"✗ Erro ao remover {obj['Key']}: {e}")
        
        size_mb = total_size_freed / (1024 * 1024)
        self.logger.info(f"Limpeza concluída. {len(deleted_objects)} arquivos removidos, {size_mb:.2f} MB liberados")
        
        return deleted_objects
    
    def generate_retention_report(self, all_objects, expired_objects, deleted_objects):
        total_objects = len(all_objects)
        expired_count = len(expired_objects)
        deleted_count = len(deleted_objects)
        remaining_objects = total_objects - deleted_count
        
        report = f"""
=== RELATÓRIO DE RETENÇÃO DE BACKUPS ===
Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Servidor: {Config.SERVER_NAME}
Bucket S3: {Config.S3_BUCKET_NAME}
Período de retenção: {Config.BACKUP_RETENTION_DAYS} dias

Total de backups no S3: {total_objects}
Backups expirados encontrados: {expired_count}
Backups removidos com sucesso: {deleted_count}
Backups mantidos: {remaining_objects}

Status: {'✓ SUCESSO' if expired_count == deleted_count else '⚠ PARCIAL'}
"""
        
        self.logger.info(report)
        return report
    
    def clean_expired_backups(self):
        try:
            all_objects = self.list_backup_objects()
            
            if not all_objects:
                return
            
            retention_date = self.calculate_retention_date()
            expired_objects = self.get_expired_backups(all_objects, retention_date)
            deleted_objects = self.delete_expired_backups(expired_objects)
            
            self.generate_retention_report(all_objects, expired_objects, deleted_objects)
            
            return len(deleted_objects)
            
        except Exception as e:
            self.logger.error(f"Erro no processo de limpeza: {e}")
            raise

def main():
    try:
        retention_manager = BackupRetentionManager()
        deleted_count = retention_manager.clean_expired_backups()
        
        logger = setup_logging()
        logger.info(f"Processo de retenção concluído. {deleted_count or 0} arquivos removidos")
        exit(0)
        
    except Exception as e:
        logger = setup_logging()
        logger.error(f"Erro crítico no processo de retenção: {e}")
        exit(1)

if __name__ == "__main__":
    main()