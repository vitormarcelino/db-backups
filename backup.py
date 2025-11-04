import os
import subprocess
import gzip
import boto3
from datetime import datetime
from config import Config, setup_logging

class DatabaseBackup:
    def __init__(self):
        self.logger = setup_logging()
        Config.validate()
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
        
        os.makedirs(Config.BACKUP_DIR, exist_ok=True)
    
    def get_all_databases(self):
        """Lista todos os databases disponíveis no servidor PostgreSQL"""
        list_command = [
            'psql',
            '-h', Config.DB_HOST,
            '-p', Config.DB_PORT,
            '-U', Config.DB_USER,
            '-d', 'postgres',  # conecta ao database padrão
            '-t',  # sem cabeçalhos
            '-c', "SELECT datname FROM pg_database WHERE NOT datistemplate AND datname NOT IN ('postgres', 'template0', 'template1');"
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = Config.DB_PASSWORD
        
        try:
            self.logger.info("Listando todos os databases disponíveis...")
            result = subprocess.run(
                list_command,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse da saída - remove espaços e linhas vazias
            databases = [db.strip() for db in result.stdout.split('\n') if db.strip()]
            
            if not databases:
                self.logger.warning("Nenhum database disponível para backup encontrado")
                return []
                
            self.logger.info(f"Databases encontrados: {', '.join(databases)}")
            return databases
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Erro ao listar databases: {e}")
            self.logger.error(f"STDERR: {e.stderr}")
            raise
    
    def create_pg_dump(self, database_name):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{database_name}_{timestamp}.sql"
        backup_path = os.path.join(Config.BACKUP_DIR, backup_filename)
        
        dump_command = [
            'pg_dump',
            '-h', Config.DB_HOST,
            '-p', Config.DB_PORT,
            '-U', Config.DB_USER,
            '-d', database_name,
            '-f', backup_path,
            '--verbose',
            '--no-password'
        ]
        
        env = os.environ.copy()
        env['PGPASSWORD'] = Config.DB_PASSWORD
        
        try:
            self.logger.info(f"Iniciando backup do database: {database_name}")
            result = subprocess.run(
                dump_command,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            self.logger.info(f"Backup criado com sucesso: {backup_path}")
            return backup_path
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Erro ao criar backup de {database_name}: {e}")
            self.logger.error(f"STDERR: {e.stderr}")
            raise
    
    def compress_backup(self, backup_path):
        compressed_path = f"{backup_path}.gz"
        
        try:
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.writelines(f_in)
            
            os.remove(backup_path)
            self.logger.info(f"Backup comprimido: {compressed_path}")
            return compressed_path
            
        except Exception as e:
            self.logger.error(f"Erro ao comprimir backup {backup_path}: {e}")
            raise
    
    def upload_to_s3(self, local_file_path):
        filename = os.path.basename(local_file_path)
        s3_key = f"{Config.SERVER_NAME}/{filename}"
        
        try:
            self.logger.info(f"Enviando {filename} para S3 no diretório {Config.SERVER_NAME}...")
            
            self.s3_client.upload_file(
                local_file_path,
                Config.S3_BUCKET_NAME,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
            )
            
            self.logger.info(f"Upload concluído: s3://{Config.S3_BUCKET_NAME}/{s3_key}")
            return s3_key
            
        except Exception as e:
            self.logger.error(f"Erro no upload para S3: {e}")
            raise
    
    def cleanup_local_files(self, file_path):
        try:
            os.remove(file_path)
            self.logger.info(f"Arquivo local removido: {file_path}")
        except Exception as e:
            self.logger.warning(f"Erro ao remover arquivo local {file_path}: {e}")
    
    def backup_database(self, database_name):
        try:
            backup_path = self.create_pg_dump(database_name)
            compressed_path = self.compress_backup(backup_path)
            s3_key = self.upload_to_s3(compressed_path)
            self.cleanup_local_files(compressed_path)
            
            return s3_key
            
        except Exception as e:
            self.logger.error(f"Falha no backup de {database_name}: {e}")
            raise
    
    def backup_all_databases(self):
        successful_backups = []
        failed_backups = []
        
        # Determina quais databases fazer backup
        if Config.DB_NAMES and Config.DB_NAMES != ['']:
            # Usa lista configurada
            databases_to_backup = [db.strip() for db in Config.DB_NAMES if db.strip()]
            self.logger.info(f"Usando databases configurados: {', '.join(databases_to_backup)}")
        else:
            # Lista todos os databases automaticamente
            self.logger.info("DB_NAMES não configurado - fazendo backup de todos os databases")
            databases_to_backup = self.get_all_databases()
        
        if not databases_to_backup:
            self.logger.warning("Nenhum database encontrado para backup")
            return [], []
        
        self.logger.info("Iniciando processo de backup de todos os databases")
        
        for db_name in databases_to_backup:
                
            try:
                s3_key = self.backup_database(db_name)
                successful_backups.append((db_name, s3_key))
                self.logger.info(f"✓ Backup de {db_name} concluído com sucesso")
                
            except Exception as e:
                failed_backups.append((db_name, str(e)))
                self.logger.error(f"✗ Falha no backup de {db_name}")
        
        self.logger.info(f"Processo concluído. Sucessos: {len(successful_backups)}, Falhas: {len(failed_backups)}")
        
        if failed_backups:
            self.logger.error("Databases com falha:")
            for db_name, error in failed_backups:
                self.logger.error(f"  - {db_name}: {error}")
        
        return successful_backups, failed_backups

def main():
    try:
        backup_manager = DatabaseBackup()
        successful, failed = backup_manager.backup_all_databases()
        
        if failed:
            exit(1)
        else:
            exit(0)
            
    except Exception as e:
        logger = setup_logging()
        logger.error(f"Erro crítico no processo de backup: {e}")
        exit(1)

if __name__ == "__main__":
    main()