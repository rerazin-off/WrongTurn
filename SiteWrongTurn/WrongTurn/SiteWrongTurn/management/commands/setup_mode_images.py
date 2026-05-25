from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Копирует картинки режимов в media/images_for_pages/'

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        dst_dir = media_root / 'images_for_pages'
        dst_dir.mkdir(parents=True, exist_ok=True)

        sources = [
            (media_root / 'questions', 'экзамен.jpg', 'exam.jpg'),
            (media_root / 'questions', 'обычный.jpg', 'ordinary.jpg'),
            (media_root / 'questions', 'марафон.png', 'marathon.png'),
            (media_root / 'questions', 'игра.png', 'game.png'),
            (dst_dir, 'экзамен.jpg', 'exam.jpg'),
            (dst_dir, 'обычный.jpg', 'ordinary.jpg'),
            (dst_dir, 'марафон.png', 'marathon.png'),
            (dst_dir, 'игра.png', 'game.png'),
        ]

        copied = 0
        for folder, src_name, dst_name in sources:
            src = folder / src_name
            dst = dst_dir / dst_name
            if src.exists() and not dst.exists():
                dst.write_bytes(src.read_bytes())
                self.stdout.write(self.style.SUCCESS(f'{src} -> {dst}'))
                copied += 1

        required = ['exam.jpg', 'ordinary.jpg', 'marathon.png', 'game.png']
        missing = [name for name in required if not (dst_dir / name).exists()]

        if missing:
            self.stdout.write(self.style.WARNING(
                'Положите файлы в WrongTurn/media/images_for_pages/: ' + ', '.join(missing)
            ))
        else:
            self.stdout.write(self.style.SUCCESS('Все 4 картинки на месте.'))

        if copied:
            self.stdout.write(self.style.SUCCESS(f'Скопировано файлов: {copied}'))
