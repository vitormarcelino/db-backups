import os
import logging
import socket
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_NAMES = os.getenv('DB_NAMES', '').split(',')
    
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')

    STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 's3').strip().lower()

    BACKUP_MODE = os.getenv('BACKUP_MODE', 'host').strip().lower()
    DOCKER_CONTAINERS = [c.strip() for c in os.getenv('DOCKER_CONTAINERS', '').split(',') if c.strip()]

    GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME')
    GCS_PROJECT_ID = os.getenv('GCS_PROJECT_ID') or None
    GCS_CREDENTIALS_FILE = os.getenv('GCS_CREDENTIALS_FILE') or None
    GCS_STORAGE_CLASS = os.getenv('GCS_STORAGE_CLASS', 'NEARLINE') or None

    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '15'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    BACKUP_DIR = '/tmp/db_backups'
    SERVER_NAME = os.getenv('SERVER_NAME', socket.gethostname())
    
    @classmethod
    def validate(cls):
        if cls.BACKUP_MODE == 'host':
            required_vars = ['DB_PASSWORD']
        elif cls.BACKUP_MODE == 'docker':
            required_vars = []
        else:
            raise ValueError(f"BACKUP_MODE inválido: {cls.BACKUP_MODE} (use 'host' ou 'docker')")

        if cls.STORAGE_PROVIDER == 's3':
            required_vars += ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME']
        elif cls.STORAGE_PROVIDER == 'gcs':
            required_vars += ['GCS_BUCKET_NAME']
            if cls.GCS_CREDENTIALS_FILE and not os.path.isfile(cls.GCS_CREDENTIALS_FILE):
                raise ValueError(f"GCS_CREDENTIALS_FILE não encontrado: {cls.GCS_CREDENTIALS_FILE}")
        else:
            raise ValueError(f"STORAGE_PROVIDER inválido: {cls.STORAGE_PROVIDER} (use 's3' ou 'gcs')")

        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

def setup_logging():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'/var/log/db_backup_{timestamp}.log'
    
    # Cria diretório /var/log se não existir
    os.makedirs('/var/log', exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)