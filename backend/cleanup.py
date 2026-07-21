import os
import shutil
from pathlib import Path

BASE_DIR = Path(r"c:\Users\slimc\Desktop\POS\backend\Ai models")

DIRS = {
    "data_processed": BASE_DIR / "data" / "processed",
    "data_final": BASE_DIR / "data" / "final",
    "models": BASE_DIR / "models",
    "notebooks": BASE_DIR / "notebooks"
}

for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

def move_all(mod_dir, num):
    if not mod_dir.exists():
        return
    for root, _, files in os.walk(mod_dir):
        for f in files:
            src = Path(root) / f
            ext = src.suffix.lower()
            
            if ext in ['.ckpt', '.yaml', '.yml', '.h5', '.pt', '.pth']:
                dst_dir = DIRS['models'] / f'Module {num}' / Path(root).name
            elif ext in ['.md', '.txt']:
                dst_dir = DIRS['notebooks'] / f'Module {num}'
            elif ext in ['.csv', '.json']:
                dst_dir = DIRS['data_final'] / f'Module {num}'
            else:
                dst_dir = DIRS['data_processed'] / f'Module {num}'
                
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / f
            if dst.exists():
                dst.unlink()
            shutil.move(str(src), str(dst))
            print(f'Moved {f} to {dst_dir}')

for i in range(1, 5):
    move_all(BASE_DIR / f'Module {i}', i)
    shutil.rmtree(BASE_DIR / f'Module {i}', ignore_errors=True)
    
print("Cleanup complete!")
