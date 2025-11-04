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
    
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', '15'))
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    BACKUP_DIR = '/tmp/db_backups'
    SERVER_NAME = os.getenv('SERVER_NAME', socket.gethostname())
    
    @classmethod
    def validate(cls):
        required_vars = [
            'DB_PASSWORD', 'AWS_ACCESS_KEY_ID', 
            'AWS_SECRET_ACCESS_KEY', 'S3_BUCKET_NAME'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # DB_NAMES é opcional - se não especificado, fará backup de todos os databases

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