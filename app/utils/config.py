import os
from minio import Minio
from minio.error import S3Error


class MinIOConfig:
    # Настройки подключения
    ENDPOINT = os.getenv('ENDPOINT')
    ACCESS_KEY = os.getenv('ACCESS_KEY')
    SECRET_KEY = os.getenv('SECRET_KEY')
    SECURE = False

    # Имя бакета
    BUCKET_NAME = os.getenv('BUCKET_NAME')

    # URL для доступа к файлам (если бакет публичный)
    PUBLIC_URL = f'http://{ENDPOINT}/{BUCKET_NAME}'

    @classmethod
    def get_client(cls):
        """Возвращает клиент MinIO"""
        return Minio(
            cls.ENDPOINT,
            access_key=cls.ACCESS_KEY,
            secret_key=cls.SECRET_KEY,
            secure=cls.SECURE
        )

    @classmethod
    def ensure_bucket_exists(cls):
        """Создает бакет если он не существует"""
        try:
            client = cls.get_client()
            if not client.bucket_exists(cls.BUCKET_NAME):
                client.make_bucket(cls.BUCKET_NAME)
                print(f"Bucket '{cls.BUCKET_NAME}' created successfully")
            else:
                print(f"Bucket '{cls.BUCKET_NAME}' already exists")
        except S3Error as e:
            print(f"Error creating bucket: {e}")