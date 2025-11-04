#!/usr/bin/env python3

import os
import sys
import boto3
from datetime import datetime

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_s3_connection():
    """Testa conexão e permissões do S3"""
    
    try:
        from config import Config, setup_logging
        
        # Valida configurações
        Config.validate()
        
        # Setup de logging
        logger = setup_logging()
        logger.info("=== TESTE DE CONEXÃO S3 ===")
        
        # Cria cliente S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
        
        logger.info(f"Testando bucket: {Config.S3_BUCKET_NAME}")
        logger.info(f"Região: {Config.AWS_REGION}")
        
        # Teste 1: Verificar se o bucket existe
        logger.info("1. Verificando se bucket existe...")
        try:
            s3_client.head_bucket(Bucket=Config.S3_BUCKET_NAME)
            logger.info("✅ Bucket existe e está acessível")
        except Exception as e:
            logger.error(f"❌ Erro ao acessar bucket: {e}")
            return False
        
        # Teste 2: Listar objetos (permissão ListBucket)
        logger.info("2. Testando permissão de listagem...")
        try:
            response = s3_client.list_objects_v2(
                Bucket=Config.S3_BUCKET_NAME,
                MaxKeys=1
            )
            logger.info("✅ Permissão de listagem OK")
        except Exception as e:
            logger.error(f"❌ Erro na listagem: {e}")
            return False
        
        # Teste 3: Upload de arquivo teste (permissão PutObject)
        logger.info("3. Testando upload...")
        test_key = f"test/backup_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        test_content = f"Teste de backup - {datetime.now()}"
        
        try:
            s3_client.put_object(
                Bucket=Config.S3_BUCKET_NAME,
                Key=test_key,
                Body=test_content.encode(),
                ServerSideEncryption='AES256'
            )
            logger.info("✅ Upload de teste OK")
        except Exception as e:
            logger.error(f"❌ Erro no upload: {e}")
            return False
        
        # Teste 4: Download do arquivo (permissão GetObject)
        logger.info("4. Testando download...")
        try:
            response = s3_client.get_object(
                Bucket=Config.S3_BUCKET_NAME,
                Key=test_key
            )
            content = response['Body'].read().decode()
            logger.info("✅ Download de teste OK")
        except Exception as e:
            logger.error(f"❌ Erro no download: {e}")
            return False
        
        # Teste 5: Deletar arquivo teste (permissão DeleteObject)
        logger.info("5. Testando remoção...")
        try:
            s3_client.delete_object(
                Bucket=Config.S3_BUCKET_NAME,
                Key=test_key
            )
            logger.info("✅ Remoção de teste OK")
        except Exception as e:
            logger.error(f"❌ Erro na remoção: {e}")
            return False
        
        logger.info("🎉 TODOS OS TESTES S3 PASSARAM!")
        logger.info("O sistema está pronto para fazer backups!")
        
        return True
        
    except ValueError as e:
        print(f"❌ Erro de configuração: {e}")
        print("Verifique o arquivo .env e configure as credenciais AWS")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False

def show_s3_setup_guide():
    """Mostra guia de configuração do S3"""
    
    print("\n" + "="*50)
    print("   GUIA DE CONFIGURAÇÃO AWS S3")
    print("="*50)
    
    print("\n1. CRIAR BUCKET S3:")
    print("   • Acesse: https://console.aws.amazon.com/s3/")
    print("   • Clique 'Create bucket'")
    print("   • Nome: backup-postgres-SEU-NOME")
    print("   • Região: us-east-1 (recomendado)")
    
    print("\n2. CRIAR USUÁRIO IAM:")
    print("   • Acesse: https://console.aws.amazon.com/iam/")
    print("   • Users → Create user")
    print("   • Nome: backup-postgres-user")
    print("   • Attach policy: Use aws-iam-policy.json")
    
    print("\n3. GERAR ACCESS KEYS:")
    print("   • No usuário criado → Security credentials")
    print("   • Create access key → Application outside AWS")
    print("   • ⚠️  ANOTE as chaves (só aparecem uma vez!)")
    
    print("\n4. CONFIGURAR .env:")
    print("   AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX")
    print("   AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    print("   AWS_REGION=us-east-1")
    print("   S3_BUCKET_NAME=backup-postgres-SEU-NOME")
    
    print("\n5. TESTAR:")
    print("   python3 test_s3_connection.py")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--guide":
        show_s3_setup_guide()
    else:
        success = test_s3_connection()
        if not success:
            print("\n💡 Para ver o guia completo: python3 test_s3_connection.py --guide")
        sys.exit(0 if success else 1)