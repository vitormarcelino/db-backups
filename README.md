# Sistema de Backup Automático PostgreSQL para S3 / GCS

Sistema completo para backup automático de bancos de dados PostgreSQL com upload para AWS S3 ou Google Cloud Storage (GCS) e gerenciamento de retenção.

**🎯 Arquitetura Simples:**
- **`setup.sh`** - Instala tudo automaticamente (execute uma vez)
- **`run.sh`** - Executa backups (use diariamente)

## Funcionalidades

- ✅ Backup automático de múltiplos databases PostgreSQL
- ✅ Compressão dos backups (gzip)
- ✅ Upload seguro para AWS S3 ou Google Cloud Storage com criptografia
- ✅ Provider selecionável via `STORAGE_PROVIDER` (`s3` ou `gcs`)
- ✅ Organização por servidor (diretórios separados no bucket)
- ✅ Gerenciamento automático de retenção (15 dias configurável)
- ✅ Logs detalhados de todo o processo
- ✅ Execução via cron
- ✅ Tratamento robusto de erros

## Organização dos Backups no Bucket

Os backups são organizados por servidor no bucket (S3 ou GCS), criando uma estrutura hierárquica:

```
seu-bucket-backup/
├── server1/
│   ├── database1_20251103_140001.sql.gz
│   ├── database2_20251103_140002.sql.gz
│   └── database3_20251103_140003.sql.gz
├── server2/
│   ├── database1_20251103_140001.sql.gz
│   └── database2_20251103_140002.sql.gz
└── server3/
    └── database1_20251103_140001.sql.gz
```

O nome do servidor é determinado por:
1. Variável `SERVER_NAME` no arquivo `.env` (se especificada)
2. Hostname do sistema (se `SERVER_NAME` não estiver definida)

## Seleção de Databases

O sistema oferece duas formas de determinar quais databases fazer backup:

### 1. Lista Específica (Configuração Manual)
```env
DB_NAMES=database1,database2,database3
```

### 2. Backup Automático de Todos os Databases
```env
# DB_NAMES não especificado ou comentado
# O sistema automaticamente fará backup de todos os databases disponíveis
```

**Observações:**
- Databases de sistema (`postgres`, `template0`, `template1`) são automaticamente excluídos
- O usuário PostgreSQL deve ter permissão de leitura em todos os databases
- Útil para ambientes dinâmicos onde novos databases são criados frequentemente

## Estrutura do Projeto

```
db-backup/
├── setup.sh                    # 🔧 Script de instalação e configuração
├── run.sh                      # 🚀 Script de execução (logs em ./logs/)
├── run_sudo.sh                 # 🚀 Script de execução com sudo (logs em /var/log/)
├── main.py                     # Script principal Python
├── backup.py                   # Módulo de backup
├── retention.py                # Módulo de retenção
├── config.py                   # Configurações
├── storage.py                  # Camada de storage (S3 / GCS)
├── requirements.txt            # Dependências Python
├── .env.example               # Exemplo de configuração
├── test_dependencies.py        # Teste de dependências
├── test_backup_dry_run.py      # Teste sem PostgreSQL
├── test_s3_connection.py       # Teste de conexão S3
├── test_gcs_connection.py      # Teste de conexão GCS
├── status.sh                   # Script de verificação de status
└── README.md                  # Esta documentação
```

## Instalação

### Instalação Automática (Recomendada)

```bash
# Execute apenas um comando para instalar tudo
./setup.sh
```

O script irá:
- ✅ Verificar e instalar Python 3 e python3-venv
- ✅ Verificar e instalar PostgreSQL client tools
- ✅ Criar ambiente virtual Python
- ✅ Instalar todas as dependências (boto3, google-cloud-storage, psycopg2, python-dotenv)
- ✅ Criar arquivo .env de exemplo
- ✅ Configurar diretórios e permissões
- ✅ Executar testes de validação
- ✅ Mostrar próximos passos

### Instalação Manual

1. **Clone ou copie os arquivos para o servidor**

2. **Configure as variáveis de ambiente**:
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **Configure as variáveis no arquivo .env**:
   ```env
   # Configurações do PostgreSQL
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=postgres
   DB_PASSWORD=sua_senha
   # DB_NAMES=database1,database2,database3  # Opcional: se não especificado, faz backup de todos os databases

   # Provider de storage: s3 (padrão) ou gcs
   STORAGE_PROVIDER=s3

   # Configurações AWS S3 (STORAGE_PROVIDER=s3)
   AWS_ACCESS_KEY_ID=sua_access_key
   AWS_SECRET_ACCESS_KEY=sua_secret_key
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=seu-bucket-backup

   # Configurações GCS (STORAGE_PROVIDER=gcs)
   # GCS_BUCKET_NAME=seu-bucket-backup
   # GCS_PROJECT_ID=seu-projeto-gcp
   # GCS_CREDENTIALS_FILE=/caminho/para/service-account.json
   # GCS_STORAGE_CLASS=NEARLINE

   # Configurações de retenção
   BACKUP_RETENTION_DAYS=15
   LOG_LEVEL=INFO

   # Nome do servidor (opcional - usa hostname se não especificado)
   SERVER_NAME=server1
   ```

4. **Instale as dependências**:

   **Opção 1: Automática (recomendada)**
   ```bash
   ./run.sh  # Instala automaticamente no primeiro uso
   ```

   **Opção 2: Manual**
   ```bash
   # Instalar python3-venv se necessário (Ubuntu/Debian)
   sudo apt install python3-venv -y

   # Criar ambiente virtual e instalar dependências
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

   **Testar instalação:**
   ```bash
   # Teste básico de dependências
   python3 test_dependencies.py

   # Teste completo sem PostgreSQL real
   python3 test_backup_dry_run.py
   ```

## Uso

### Execução Manual

```bash
# Processo completo (backup + retenção)
./run.sh                    # Logs em ./logs/
sudo ./run_sudo.sh          # Logs em /var/log/

# Apenas backup
./run.sh --backup-only      # Logs em ./logs/
sudo ./run_sudo.sh --backup-only  # Logs em /var/log/

# Apenas retenção
./run.sh --retention-only   # Logs em ./logs/
sudo ./run_sudo.sh --retention-only  # Logs em /var/log/
```

### Configuração no Cron

Para execução automática diária às 2h da manhã:

```bash
# Editar crontab como root
sudo crontab -e

# Adicionar linha (com logs em /var/log):
0 2 * * * /caminho/para/db-backup/run_sudo.sh >/dev/null 2>&1

# Ou com log de cron adicional:
0 2 * * * /caminho/para/db-backup/run_sudo.sh >> /var/log/db-backup-cron.log 2>&1
```

**Alternativa sem sudo (logs em ./logs/):**
```bash
# Editar crontab do usuário
crontab -e

# Adicionar linha:
0 2 * * * /caminho/para/db-backup/run.sh >/dev/null 2>&1
```

**Importante:** Use caminhos absolutos no cron e certifique-se de que `./setup.sh` foi executado primeiro.

## Pré-requisitos

### Sistema
- Python 3.6+
- PostgreSQL client tools (`pg_dump`)
- Acesso de rede ao PostgreSQL e ao storage (AWS S3 ou GCS)

### Permissões AWS S3
O usuário AWS precisa das seguintes permissões:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::seu-bucket-backup",
                "arn:aws:s3:::seu-bucket-backup/*"
            ]
        }
    ]
}
```

### Google Cloud Storage

Defina `STORAGE_PROVIDER=gcs` e `GCS_BUCKET_NAME`. Autenticação:

- **`GCS_CREDENTIALS_FILE`**: caminho para a chave JSON de uma service account
- **Sem `GCS_CREDENTIALS_FILE`**: usa Application Default Credentials (service account anexada à VM no GCE/GKE, `GOOGLE_APPLICATION_CREDENTIALS` ou `gcloud auth application-default login`)

A service account precisa de `roles/storage.objectAdmin` no bucket (ou das permissões `storage.objects.create`, `storage.objects.get`, `storage.objects.list` e `storage.objects.delete`):

```bash
gcloud storage buckets create gs://seu-bucket-backup \
  --location=southamerica-east1 --default-storage-class=NEARLINE --uniform-bucket-level-access

gcloud iam service-accounts create backup-postgres

gcloud storage buckets add-iam-policy-binding gs://seu-bucket-backup \
  --member=serviceAccount:backup-postgres@SEU-PROJETO.iam.gserviceaccount.com \
  --role=roles/storage.objectAdmin
```

`GCS_STORAGE_CLASS` aceita `STANDARD`, `NEARLINE` (padrão), `COLDLINE` ou `ARCHIVE`. Os objetos são criptografados em repouso pelo GCS automaticamente. Observe que `NEARLINE`/`COLDLINE`/`ARCHIVE` têm duração mínima de armazenamento (30/90/365 dias): com retenção de 15 dias, a exclusão antecipada é cobrada como se o objeto tivesse ficado o período mínimo — use `STANDARD` se isso pesar.

Teste: `python3 test_gcs_connection.py` (guia: `python3 test_gcs_connection.py --guide`).

### PostgreSQL
- Usuário com permissão de leitura nos databases
- Configuração de autenticação (recomenda-se `.pgpass`)

## Logs

Os logs são salvos em:
- `/var/log/db_backup_YYYYMMDD_HHMMSS.log` (usando `run_sudo.sh`)
- `./logs/db_backup_YYYYMMDD_HHMMSS.log` (usando `run.sh`)

Formato do log:
```
2025-11-03 14:30:01,123 - INFO - Iniciando backup do database: meu_database
2025-11-03 14:30:15,456 - INFO - Backup criado com sucesso: /tmp/db_backups/meu_database_20251103_143001.sql
2025-11-03 14:30:20,789 - INFO - Upload concluído: s3://meu-bucket/backups/meu_database_20251103_143001.sql.gz
```

## Monitoramento

O script retorna códigos de saída apropriados:
- `0`: Sucesso
- `1`: Erro

Isso permite monitoramento via cron ou ferramentas de monitoramento.

## Segurança

- Backups são criptografados no S3 (AES256)
- Senha do PostgreSQL via variável de ambiente
- Credenciais AWS via variáveis de ambiente
- Arquivos temporários são removidos após upload

## Troubleshooting

### Erro: No module named 'dotenv'
As dependências Python não estão instaladas:
```bash
# Instalar python3-venv se necessário
sudo apt install python3-venv -y

# Recriar ambiente virtual
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Erro: Permission denied '/var/log/'
O sistema automaticamente usa `./logs/` se não tiver permissão para `/var/log/`:
```bash
# Os logs serão salvos em ./logs/ automaticamente
ls -la logs/
```

### Erro: connection to server failed
PostgreSQL não está acessível com as configurações do `.env`:
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar conectividade
psql -h localhost -p 5432 -U postgres -c "\l"

# Testar sistema sem PostgreSQL real
python3 test_backup_dry_run.py
```

### Erro: pg_dump não encontrado
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-client

# CentOS/RHEL
sudo yum install postgresql
```

### Erro: Permissão negada no PostgreSQL
1. Verifique usuário e senha no `.env`
2. Configure `.pgpass` se necessário:
   ```bash
   echo "localhost:5432:*:postgres:sua_senha" >> ~/.pgpass
   chmod 600 ~/.pgpass
   ```

### Erro: Bucket S3 não encontrado
1. Verifique se o bucket existe
2. Verifique permissões AWS
3. Verifique região configurada

### Erro: GCS 403 / credenciais não encontradas
1. Verifique `GCS_CREDENTIALS_FILE` (caminho absoluto, legível pelo usuário do cron)
2. Sem arquivo de chave, confirme que a VM tem service account anexada com escopo `cloud-platform`
3. Confirme `roles/storage.objectAdmin` da service account no bucket
4. Rode `python3 test_gcs_connection.py`

### Logs não aparecem
1. Verifique permissões da pasta `/var/log`
2. Execute manualmente para ver erros:
   ```bash
   ./run.sh --backup-only
   ```

## Customização

### Alterar diretório de backup temporário
No arquivo `config.py`:
```python
BACKUP_DIR = '/seu/diretorio/temporario'
```

### Alterar classe de storage S3
No arquivo `storage.py`, método `S3Storage.upload`:
```python
'StorageClass': 'GLACIER'  # ou 'DEEP_ARCHIVE'
```

### Personalizar formato do nome do arquivo
No arquivo `backup.py`, método `create_pg_dump`:
```python
backup_filename = f"{database_name}_{timestamp}_custom.sql"
```