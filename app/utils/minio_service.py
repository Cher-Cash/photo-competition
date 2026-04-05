from app.utils.config import MinIOConfig
import io

# Импортируем наш модуль логирования
from logger_setup import setup_logger

# Создаем логгер для этого модуля
logger = setup_logger('artwork_storage')


class ArtworkStorage:
    def __init__(self):
        self.client = MinIOConfig.get_client()
        self.bucket = MinIOConfig.BUCKET_NAME
        logger.debug("Инициализация MinIO клиента... Бакет: %s", self.bucket)

        # Проверяем подключение
        self._check_connection()

    def _check_connection(self):
        """Проверяет подключение к MinIO"""
        try:
            # Пробуем получить список бакетов
            buckets = self.client.list_buckets()
            # Проверяем существует ли нужный бакет
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)

        except Exception as e:
            logger.error("Ошибка подключения к MinIO: %s", e)
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
            logger.debug("Начало загрузки файла: %s", filename)

            file_size = len(file_data)
            logger.debug("Размер файла: %s байт", file_size)

            # Метаданные файла
            metadata = {
                'Content-Type': content_type,
                'Cache-Control': 'max-age=31536000',
            }


            # Загрузка файла в MinIO
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=filename,
                data=io.BytesIO(file_data),
                length=file_size,
                content_type=content_type,
                metadata=metadata
            )

            logger.debug("Файл %s успешно загружен", filename)

            # Генерация URL
            public_url = f"{MinIOConfig.PUBLIC_URL}/{filename}"

            # Используем self.get_presigned_url
            signed_url = self.get_presigned_url(filename)

            logger.debug("Публичный URL: %s", public_url)

            return {
                'success': True,
                'filename': filename,
                'url': public_url,
                'signed_url': signed_url,
                'bucket': self.bucket
            }

        except Exception as e:
            logger.error("Ошибка при загрузке: %s", e)
            return {
                'success': False,
                'error': f"MinIO error: {str(e)}"
            }

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
            logger.error("Ошибка генерации подписанного URL: %s", e)
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
            logger.debug("Расширение файла не найдено, установлено значение по умолчанию: %s", file_extension)

    # Генерируем UUID для файла
    file_uuid = str(uuid.uuid4())

    # Текущая дата для организации
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')

    # Структура ключа
    s3_key = f"competitions/{competition_id}/nominations/{nomination_id}/users/{user_id}/{year}/{month}/{file_uuid}.{file_extension}"

    return s3_key