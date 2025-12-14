import os
from datetime import timedelta
from typing import Optional, BinaryIO
from minio import Minio
from minio.error import S3Error
from app.utils.config import MinIOConfig
import io


class ArtworkStorage:
    def __init__(self):
        print(f"[DEBUG] Инициализация MinIO клиента...")
        self.client = MinIOConfig.get_client()
        self.bucket = MinIOConfig.BUCKET_NAME
        print(f"[DEBUG] Бакет: {self.bucket}")

        # Проверяем подключение
        self._check_connection()

    def _check_connection(self):
        """Проверяет подключение к MinIO"""
        try:
            # Пробуем получить список бакетов
            buckets = self.client.list_buckets()
            print(f"[DEBUG] Подключение успешно. Доступные бакеты: {[b.name for b in buckets]}")

            # Проверяем существует ли нужный бакет
            if not self.client.bucket_exists(self.bucket):
                print(f"[DEBUG] Бакет '{self.bucket}' не существует, создаю...")
                self.client.make_bucket(self.bucket)
                print(f"[DEBUG] Бакет '{self.bucket}' создан")
            else:
                print(f"[DEBUG] Бакет '{self.bucket}' уже существует")

        except Exception as e:
            print(f"[DEBUG] Ошибка подключения к MinIO: {e}")
            raise

    def upload_image(
            self,
            file_data: bytes,
            filename: str,
            content_type: str = "image/jpeg"
    ) -> dict:
        """
        Упрощенная загрузка без ресайза
        """
        try:
            print(f"[DEBUG] Начало загрузки файла: {filename}")

            file_size = len(file_data)
            print(f"[DEBUG] Размер файла: {file_size} байт")

            # Метаданные файла
            metadata = {
                'Content-Type': content_type,
                'Cache-Control': 'max-age=31536000',
            }

            print(f"[DEBUG] Загрузка в бакет: {self.bucket}, файл: {filename}")

            # Загрузка файла в MinIO
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=filename,
                data=io.BytesIO(file_data),
                length=file_size,
                content_type=content_type,
                metadata=metadata
            )

            print(f"[DEBUG] Файл успешно загружен")

            # Генерация URL
            public_url = f"{MinIOConfig.PUBLIC_URL}/{filename}"

            # Используем self.get_presigned_url - добавьте self.
            signed_url = self.get_presigned_url(filename)  # <-- ДОБАВЬТЕ self.

            print(f"[DEBUG] Публичный URL: {public_url}")
            print(f"[DEBUG] Подписанный URL: {signed_url}")

            return {
                'success': True,
                'filename': filename,
                'url': public_url,
                'signed_url': signed_url,
                'bucket': self.bucket
            }

        except Exception as e:
            print(f"[DEBUG] Ошибка при загрузке: {type(e).__name__}: {str(e)}")
            return {
                'success': False,
                'error': f"MinIO error: {str(e)}"
            }

    # ВАЖНО: добавьте этот метод если его нет
    def get_presigned_url(self, filename: str, expires: int = 3600) -> str:
        """
        Генерирует подписанный URL для временного доступа к файлу
        """
        from datetime import timedelta
        try:
            return self.client.presigned_get_object(
                bucket_name=self.bucket,
                object_name=filename,
                expires=timedelta(seconds=expires)
            )
        except Exception as e:
            print(f"[DEBUG] Ошибка генерации подписанного URL: {e}")
            return f"{MinIOConfig.PUBLIC_URL}/{filename}"


def generate_s3_key(competition_id, nomination_id, user_id, original_filename, file_extension=None):
    """
    Генерирует S3 ключ для хранения работы
    """
    import uuid
    from datetime import datetime

    # Получаем расширение файла
    if file_extension is None:
        if '.' in original_filename:
            file_extension = original_filename.split('.')[-1].lower()
        else:
            file_extension = 'jpg'

    # Генерируем UUID для файла
    file_uuid = str(uuid.uuid4())


    # Текущая дата для организации
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')

    # Структура ключа
    s3_key = f"competitions/{competition_id}/nominations/{nomination_id}/users/{user_id}/{year}/{month}/{file_uuid}.{file_extension}"
    return s3_key