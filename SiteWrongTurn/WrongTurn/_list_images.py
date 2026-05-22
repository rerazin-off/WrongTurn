from pathlib import Path

root = Path(r'c:\Pracktik02\ProjectCode\SiteWrongTurn')
for f in root.rglob('*'):
    if f.is_file() and f.suffix.lower() in {'.jpg', '.png', '.jpeg'}:
        print(f.relative_to(root))
