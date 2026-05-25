"""Сохранение изображений вопросов в media/questions/"""

import base64
import re
import uuid
from pathlib import Path

from django.conf import settings

# Папка: WrongTurn/media/questions/
QUESTION_IMAGES_DIR = 'questions'


def ensure_questions_media_dir():
    folder = Path(settings.MEDIA_ROOT) / QUESTION_IMAGES_DIR
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def get_image_url(image_ref):
    """Путь из БД -> URL для шаблона."""
    if not image_ref:
        return ''
    ref = str(image_ref).strip()
    if ref.startswith(('http://', 'https://', '/media/', 'data:')):
        return ref
    return f'{settings.MEDIA_URL}{ref.lstrip("/")}'


def process_image_input(image_value, old_path=None):
    """
    Принимает data:image/... base64, относительный путь questions/... или пустую строку.
    Возвращает относительный путь для хранения в JSON (questions/имя_файла.ext).
    """
    if not image_value:
        return old_path or ''

    value = str(image_value).strip()

    if value.startswith('questions/'):
        return value

    if value.startswith('/media/'):
        return value.replace(settings.MEDIA_URL, '').lstrip('/')

    if value.startswith('data:image'):
        return _save_base64_image(value)

    if value.startswith('http'):
        return old_path or ''

    return value


def _save_base64_image(data_url):
    match = re.match(r'data:image/(\w+);base64,(.+)', data_url, re.DOTALL)
    if not match:
        raise ValueError('Некорректный формат изображения')

    ext = match.group(1).lower()
    if ext == 'jpeg':
        ext = 'jpg'
    if ext not in ('jpg', 'png', 'gif', 'webp', 'bmp'):
        ext = 'jpg'

    raw = base64.b64decode(match.group(2))
    folder = ensure_questions_media_dir()
    filename = f'{uuid.uuid4().hex}.{ext}'
    filepath = folder / filename
    filepath.write_bytes(raw)
    return f'{QUESTION_IMAGES_DIR}/{filename}'


def delete_image_file(relative_path):
    if not relative_path or not str(relative_path).startswith(f'{QUESTION_IMAGES_DIR}/'):
        return
    filepath = Path(settings.MEDIA_ROOT) / relative_path
    if filepath.is_file():
        filepath.unlink(missing_ok=True)
