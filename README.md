# Sistema de Backup Automático PostgreSQL para S3

Sistema completo para backup automático de bancos de dados PostgreSQL com upload para AWS S3 e gerenciamento de retenção.

## Funcionalidades

- ✅ Backup automático de múltiplos databases PostgreSQL
- ✅ Compressão dos backups (gzip)
- ✅ Upload seguro para AWS S3 com criptografia
- ✅ Organização por servidor (diretórios separados no S3)
- ✅ Gerenciamento automático de retenção (15 dias configurável)
- ✅ Logs detalhados de todo o processo
- ✅ Execução via cron
- ✅ Tratamento robusto de erros

## Organização dos Backups no S3

Os backups são organizados por servidor no S3, criando uma estrutura hierárquica:

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
├── main.py              # Script principal
├── backup.py            # Módulo de backup
├── retention.py         # Módulo de retenção
├── config.py           # Configurações
├── run.sh              # Script de execução
├── requirements.txt    # Dependências Python
├── .env.example       # Exemplo de configuração
└── README.md          # Esta documentação
```

## Instalação

### Instalação Rápida (Recomendada)

```bash
# Execute o script de setup automático
./setup.sh
```

O script irá:
- ✅ Verificar dependências do sistema
- ✅ Instalar python3-venv se necessário
- ✅ Criar ambiente virtual Python
- ✅ Instalar todas as dependências
- ✅ Criar arquivo .env de exemplo
- ✅ Testar a instalação

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

   # Configurações AWS S3
   AWS_ACCESS_KEY_ID=sua_access_key
   AWS_SECRET_ACCESS_KEY=sua_secret_key
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=seu-bucket-backup

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
# Executa backup e retenção (processo completo) com logs em /var/log
sudo ./run_sudo.sh

# Executa apenas backup
sudo ./run_sudo.sh --backup-only

# Executa apenas retenção
sudo ./run_sudo.sh --retention-only

# Alternativa sem sudo (logs em ./logs/)
./run.sh --backup-only
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

## Pré-requisitos

### Sistema
- Python 3.6+
- PostgreSQL client tools (`pg_dump`)
- Acesso de rede ao PostgreSQL e AWS S3

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
No arquivo `backup.py`, método `upload_to_s3`:
```python
'StorageClass': 'GLACIER'  # ou 'DEEP_ARCHIVE'
```

### Personalizar formato do nome do arquivo
No arquivo `backup.py`, método `create_pg_dump`:
```python
backup_filename = f"{database_name}_{timestamp}_custom.sql"
```