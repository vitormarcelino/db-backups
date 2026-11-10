from datetime import timezone
from config import Config


class S3Storage:
    def __init__(self):
        import boto3
        self.bucket = Config.S3_BUCKET_NAME
        self.client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )

    def uri(self, key):
        return f"s3://{self.bucket}/{key}"

    def upload(self, local_path, key):
        self.client.upload_file(
            local_path,
            self.bucket,
            key,
            ExtraArgs={
                'ServerSideEncryption': 'AES256',
                'StorageClass': 'STANDARD_IA'
            }
        )
        return self.uri(key)

    def list(self, prefix):
        objects = []
        paginator = self.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                objects.append({
                    'Key': obj['Key'],
                    'LastModified': obj['LastModified'].astimezone(timezone.utc).replace(tzinfo=None),
                    'Size': obj['Size']
                })
        return objects

    def delete(self, key):
        self.client.delete_object(Bucket=self.bucket, Key=key)


class GCSStorage:
    def __init__(self):
        from google.cloud import storage
        if Config.GCS_CREDENTIALS_FILE:
            client = storage.Client.from_service_account_json(
                Config.GCS_CREDENTIALS_FILE,
                project=Config.GCS_PROJECT_ID
            )
        else:
            client = storage.Client(project=Config.GCS_PROJECT_ID)
        self.client = client
        self.bucket_name = Config.GCS_BUCKET_NAME
        self.bucket = client.bucket(self.bucket_name)

    def uri(self, key):
        return f"gs://{self.bucket_name}/{key}"

    def upload(self, local_path, key):
        blob = self.bucket.blob(key)
        if Config.GCS_STORAGE_CLASS:
            blob.storage_class = Config.GCS_STORAGE_CLASS
        blob.upload_from_filename(local_path, content_type='application/gzip')
        return self.uri(key)

    def list(self, prefix):
        objects = []
        for blob in self.client.list_blobs(self.bucket_name, prefix=prefix):
            objects.append({
                'Key': blob.name,
                'LastModified': blob.updated.astimezone(timezone.utc).replace(tzinfo=None),
                'Size': blob.size or 0
            })
        return objects

    def delete(self, key):
        self.bucket.blob(key).delete()


def get_storage():
    provider = Config.STORAGE_PROVIDER
    if provider == 's3':
        return S3Storage()
    if provider == 'gcs':
        return GCSStorage()
    raise ValueError(f"STORAGE_PROVIDER inválido: {provider} (use 's3' ou 'gcs')")
