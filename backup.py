import os
import shutil
import subprocess
import tempfile
import gzip
from datetime import datetime
from config import Config, setup_logging
from storage import get_storage

LIST_DATABASES_SQL = (
    "SELECT datname FROM pg_database "
    "WHERE NOT datistemplate AND datname NOT IN ('postgres', 'template0', 'template1');"
)

DOCKER_PG_SHELL = 'PGPASSWORD="$POSTGRES_PASSWORD" exec "$0" -U "${POSTGRES_USER:-postgres}" "$@"'


class DatabaseBackup:
    def __init__(self):
        self.logger = setup_logging()
        Config.validate()

        self.storage = get_storage()

        os.makedirs(Config.BACKUP_DIR, exist_ok=True)

    def _host_env(self):
        env = os.environ.copy()
        env['PGPASSWORD'] = Config.DB_PASSWORD
        return env

    def _host_command(self, binary, *args):
        return [binary, '-h', Config.DB_HOST, '-p', Config.DB_PORT, '-U', Config.DB_USER, *args]

    def _docker_command(self, container, binary, *args):
        return ['docker', 'exec', container, 'sh', '-c', DOCKER_PG_SHELL, binary, *args]

    def _run_list_databases(self, command, env, label):
        try:
            self.logger.info(f"Listando databases disponíveis em {label}...")
            result = subprocess.run(command, env=env, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Erro ao listar databases em {label}: {e}")
            self.logger.error(f"STDERR: {e.stderr}")
            raise

        databases = [db.strip() for db in result.stdout.split('\n') if db.strip()]
        if databases:
            self.logger.info(f"Databases encontrados em {label}: {', '.join(databases)}")
        else:
            self.logger.warning(f"Nenhum database disponível para backup em {label}")
        return databases

    def get_all_databases(self):
        command = self._host_command('psql', '-d', 'postgres', '-t', '-c', LIST_DATABASES_SQL)
        return self._run_list_databases(command, self._host_env(), Config.DB_HOST)

    def get_container_databases(self, container):
        command = self._docker_command(container, 'psql', '-d', 'postgres', '-At', '-c', LIST_DATABASES_SQL)
        return self._run_list_databases(command, None, f"container {container}")

    def discover_postgres_containers(self):
        result = subprocess.run(['docker', 'ps', '-q'], capture_output=True, text=True, check=True)
        ids = result.stdout.split()
        if not ids:
            return []

        result = subprocess.run(
            ['docker', 'inspect', '--format', '{{.Name}}|{{range .Config.Env}}{{.}};{{end}}', *ids],
            capture_output=True, text=True, check=True
        )

        containers = []
        for line in result.stdout.splitlines():
            name, _, env = line.partition('|')
            env_keys = {item.split('=', 1)[0] for item in env.split(';') if item}
            if 'PG_MAJOR' in env_keys or 'PG_VERSION' in env_keys:
                containers.append(name.lstrip('/'))

        return sorted(containers)

    def _dump_to_gzip(self, command, env, output_path, label):
        with tempfile.TemporaryFile() as stderr_file:
            try:
                with gzip.open(output_path, 'wb') as gz:
                    process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=stderr_file)
                    shutil.copyfileobj(process.stdout, gz, 1024 * 1024)
                    process.stdout.close()
                    returncode = process.wait()
            except Exception:
                if os.path.exists(output_path):
                    os.remove(output_path)
                raise

            if returncode != 0:
                stderr_file.seek(0)
                stderr = stderr_file.read().decode(errors='replace')
                os.remove(output_path)
                self.logger.error(f"STDERR: {stderr}")
                raise RuntimeError(f"pg_dump de {label} terminou com código {returncode}")

        self.logger.info(f"Backup criado e comprimido: {output_path}")
        return output_path

    def _backup_path(self, database_name, container=None):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        prefix = f"{container}__" if container else ''
        return os.path.join(Config.BACKUP_DIR, f"{prefix}{database_name}_{timestamp}.sql.gz")

    def create_pg_dump(self, database_name, container=None):
        output_path = self._backup_path(database_name, container)

        if container:
            label = f"{container}/{database_name}"
            command = self._docker_command(container, 'pg_dump', '-d', database_name)
            env = None
        else:
            label = database_name
            command = self._host_command('pg_dump', '-d', database_name, '--no-password')
            env = self._host_env()

        self.logger.info(f"Iniciando backup do database: {label}")
        try:
            return self._dump_to_gzip(command, env, output_path, label)
        except Exception as e:
            self.logger.error(f"Erro ao criar backup de {label}: {e}")
            raise

    def upload_backup(self, local_file_path, container=None):
        filename = os.path.basename(local_file_path)
        if container:
            filename = filename.split('__', 1)[1]
            directory = f"{Config.SERVER_NAME}/{container}"
        else:
            directory = Config.SERVER_NAME
        key = f"{directory}/{filename}"
        provider = Config.STORAGE_PROVIDER.upper()

        try:
            self.logger.info(f"Enviando {filename} para {provider} no diretório {directory}...")
            uri = self.storage.upload(local_file_path, key)
            self.logger.info(f"Upload concluído: {uri}")
            return key

        except Exception as e:
            self.logger.error(f"Erro no upload para {provider}: {e}")
            raise

    def cleanup_local_files(self, file_path):
        try:
            os.remove(file_path)
            self.logger.info(f"Arquivo local removido: {file_path}")
        except Exception as e:
            self.logger.warning(f"Erro ao remover arquivo local {file_path}: {e}")

    def backup_database(self, database_name, container=None):
        compressed_path = None
        try:
            compressed_path = self.create_pg_dump(database_name, container)
            return self.upload_backup(compressed_path, container)

        except Exception as e:
            self.logger.error(f"Falha no backup de {database_name}: {e}")
            raise

        finally:
            if compressed_path and os.path.exists(compressed_path):
                self.cleanup_local_files(compressed_path)

    def _configured_databases(self):
        return [db.strip() for db in Config.DB_NAMES if db.strip()]

    def _build_jobs(self):
        configured = self._configured_databases()

        if Config.BACKUP_MODE == 'docker':
            containers = Config.DOCKER_CONTAINERS or self.discover_postgres_containers()
            if Config.DOCKER_CONTAINERS:
                self.logger.info(f"Usando containers configurados: {', '.join(containers)}")
            else:
                self.logger.info(f"Containers PostgreSQL detectados: {', '.join(containers) or 'nenhum'}")

            jobs = []
            failed = []
            for container in containers:
                try:
                    databases = self.get_container_databases(container)
                except Exception as e:
                    failed.append((container, str(e)))
                    continue
                if configured:
                    databases = [db for db in databases if db in configured]
                jobs.extend((container, db) for db in databases)
            return jobs, failed

        if configured:
            self.logger.info(f"Usando databases configurados: {', '.join(configured)}")
            return [(None, db) for db in configured], []

        self.logger.info("DB_NAMES não configurado - fazendo backup de todos os databases")
        return [(None, db) for db in self.get_all_databases()], []

    def backup_all_databases(self):
        successful_backups = []
        jobs, failed_backups = self._build_jobs()

        if not jobs and not failed_backups:
            self.logger.warning("Nenhum database encontrado para backup")
            return [], []

        self.logger.info("Iniciando processo de backup de todos os databases")

        for container, db_name in jobs:
            label = f"{container}/{db_name}" if container else db_name
            try:
                key = self.backup_database(db_name, container)
                successful_backups.append((label, key))
                self.logger.info(f"✓ Backup de {label} concluído com sucesso")

            except Exception as e:
                failed_backups.append((label, str(e)))
                self.logger.error(f"✗ Falha no backup de {label}")

        self.logger.info(f"Processo concluído. Sucessos: {len(successful_backups)}, Falhas: {len(failed_backups)}")

        if failed_backups:
            self.logger.error("Databases com falha:")
            for label, error in failed_backups:
                self.logger.error(f"  - {label}: {error}")

        return successful_backups, failed_backups


def main():
    try:
        backup_manager = DatabaseBackup()
        successful, failed = backup_manager.backup_all_databases()
        exit(1 if failed else 0)

    except Exception as e:
        logger = setup_logging()
        logger.error(f"Erro crítico no processo de backup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
