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

        profile_dst = dst_dir / 'profile.jpg'
        if not profile_dst.exists():
            for candidate in (dst_dir / 'ordinary.jpg', media_root / 'questions' / 'обычный.jpg'):
                if candidate.exists():
                    profile_dst.write_bytes(candidate.read_bytes())
                    self.stdout.write(self.style.SUCCESS(f'profile.jpg <- {candidate}'))
                    break

        required = ['exam.jpg', 'ordinary.jpg', 'marathon.png', 'game.png', 'profile.jpg']
        missing = [name for name in required if not (dst_dir / name).exists()]

        if missing:
            self.stdout.write(self.style.WARNING(
                'Положите исходники в media/questions/ (экзамен.jpg, обычный.jpg, марафон.png, игра.png) '
                'или готовые файлы в media/images_for_pages/: ' + ', '.join(missing)
            ))
        else:
            self.stdout.write(self.style.SUCCESS('Все картинки интерфейса на месте.'))

        if copied:
            self.stdout.write(self.style.SUCCESS(f'Скопировано файлов: {copied}'))
