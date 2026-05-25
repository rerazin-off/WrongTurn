from pathlib import Path
import shutil

src_dir = Path(r'c:\Pracktik02\ProjectCode\SiteWrongTurn\WrongTurn\media\questions')
dst_dir = Path(r'c:\Pracktik02\ProjectCode\SiteWrongTurn\WrongTurn\media\covers_card')
dst_dir.mkdir(parents=True, exist_ok=True)

mapping = {
    'экзамен.jpg': 'exam.jpg',
    'обычный.jpg': 'normal.jpg',
    'марафон.png': 'marathon.png',
    'игра.png': 'game.png',
}

for src_name, dst_name in mapping.items():
    src = src_dir / src_name
    if src.exists():
        shutil.copy2(src, dst_dir / dst_name)
        print(f'OK: {src_name} -> covers_card/{dst_name}')
    else:
        print(f'MISSING: {src_name}')

print('--- existing in questions ---')
for f in sorted(src_dir.iterdir()):
    if f.suffix.lower() in {'.jpg', '.png', '.jpeg'} and f.name != '.gitkeep':
        print(f.name, f.suffix)
