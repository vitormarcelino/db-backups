#!/usr/bin/env python3
import os
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_gcs_connection():
    try:
        from config import Config, setup_logging

        Config.STORAGE_PROVIDER = 'gcs'
        Config.validate()

        from storage import GCSStorage

        logger = setup_logging()
        logger.info("=== TESTE DE CONEXÃO GCS ===")
        logger.info(f"Bucket: {Config.GCS_BUCKET_NAME}")
        logger.info(f"Projeto: {Config.GCS_PROJECT_ID or '(padrão das credenciais)'}")
        logger.info(f"Credenciais: {Config.GCS_CREDENTIALS_FILE or 'Application Default Credentials'}")

        storage = GCSStorage()
        key = f"test/backup_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        content = f"Teste de backup - {datetime.now()}"

        logger.info("1. Verificando acesso ao bucket (list)...")
        try:
            storage.list('test/')
            logger.info("✅ OK")
        except Exception as e:
            logger.error(f"❌ Falha ao listar objetos: {e}")
            return False

        logger.info("2. Testando upload...")
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            logger.info(f"✅ OK: {storage.upload(tmp_path, key)}")
        except Exception as e:
            logger.error(f"❌ Falha no upload: {e}")
            return False
        finally:
            os.remove(tmp_path)

        logger.info("3. Testando download...")
        try:
            downloaded = storage.bucket.blob(key).download_as_text()
            if downloaded != content:
                logger.error("❌ Conteúdo baixado difere do enviado")
                return False
            logger.info("✅ OK")
        except Exception as e:
            logger.error(f"❌ Falha no download: {e}")
            return False

        logger.info("4. Testando exclusão...")
        try:
            storage.delete(key)
            logger.info("✅ OK")
        except Exception as e:
            logger.error(f"❌ Falha na exclusão: {e}")
            return False

        logger.info("🎉 TODOS OS TESTES PASSARAM!")
        return True

    except ValueError as e:
        print(f"❌ Erro de configuração: {e}")
        print("Verifique o arquivo .env e configure as variáveis GCS_*")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def show_gcs_setup_guide():
    print("\n" + "=" * 50)
    print("   GUIA DE CONFIGURAÇÃO GOOGLE CLOUD STORAGE")
    print("=" * 50)
    print("\n1. CRIAR BUCKET:")
    print("   gcloud storage buckets create gs://backup-postgres-SEU-NOME \\")
    print("     --location=southamerica-east1 --default-storage-class=NEARLINE \\")
    print("     --uniform-bucket-level-access")
    print("\n2. CRIAR SERVICE ACCOUNT:")
    print("   gcloud iam service-accounts create backup-postgres")
    print("\n3. CONCEDER PERMISSÃO NO BUCKET:")
    print("   gcloud storage buckets add-iam-policy-binding gs://backup-postgres-SEU-NOME \\")
    print("     --member=serviceAccount:backup-postgres@PROJETO.iam.gserviceaccount.com \\")
    print("     --role=roles/storage.objectAdmin")
    print("\n4. CREDENCIAIS (escolha uma):")
    print("   a) Em VM do GCE: anexe a service account à VM (sem arquivo de chave)")
    print("   b) Fora do GCP: gere uma chave JSON")
    print("      gcloud iam service-accounts keys create service-account.json \\")
    print("        --iam-account=backup-postgres@PROJETO.iam.gserviceaccount.com")
    print("\n5. CONFIGURAR .env:")
    print("   STORAGE_PROVIDER=gcs")
    print("   GCS_BUCKET_NAME=backup-postgres-SEU-NOME")
    print("   GCS_PROJECT_ID=PROJETO")
    print("   GCS_CREDENTIALS_FILE=/caminho/para/service-account.json")
    print("\n6. TESTAR:")
    print("   python3 test_gcs_connection.py")
    print("\n" + "=" * 50)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--guide":
        show_gcs_setup_guide()
        sys.exit(0)

    success = test_gcs_connection()
    if not success:
        print("\nPara ver o guia de configuração: python3 test_gcs_connection.py --guide")
    sys.exit(0 if success else 1)
