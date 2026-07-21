import os
import shutil
from pathlib import Path

BASE_DIR = Path(r"c:\Users\slimc\Desktop\POS\backend\Ai models")

# New structure
DIRS = {
    "data_raw": BASE_DIR / "data" / "raw",
    "data_processed": BASE_DIR / "data" / "processed",
    "data_final": BASE_DIR / "data" / "final",
    "models": BASE_DIR / "models",
    "notebooks": BASE_DIR / "notebooks",
    "src": BASE_DIR / "src",
}

for d in DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

# Helper for safe move
def safe_move(src, dst_dir):
    src = Path(src)
    dst_dir = Path(dst_dir)
    if not src.exists():
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    
    # Handle conflicts
    if dst.exists():
        if src.is_dir():
            # Merge directories
            for item in src.iterdir():
                safe_move(item, dst)
            shutil.rmtree(src)
            return
        else:
            # Overwrite file if it's the same, or rename
            dst.unlink()
            
    print(f"Moving {src.name} -> {dst_dir.relative_to(BASE_DIR)}")
    shutil.move(str(src), str(dst))

# 1. Datasets -> data/raw
if (BASE_DIR / "datasets").exists():
    for f in (BASE_DIR / "datasets").iterdir():
        if f.is_file():
            # Depending on name, raw vs processed
            if "feature" in f.name.lower() or "encoded" in f.name.lower() or "weekly" in f.name.lower() and "demand" not in f.name.lower():
                safe_move(f, DIRS["data_processed"])
            else:
                safe_move(f, DIRS["data_raw"])
    shutil.rmtree(BASE_DIR / "datasets", ignore_errors=True)

# 2. Data generation scripts -> src
if (BASE_DIR / "dataset_generation").exists():
    safe_move(BASE_DIR / "dataset_generation", DIRS["src"])

# 3. Data Understanding -> notebooks/Data Understanding
if (BASE_DIR / "Data Understanding").exists():
    safe_move(BASE_DIR / "Data Understanding", DIRS["notebooks"])

# Process Modules 1-4
for module_num in range(1, 5):
    mod_dir = BASE_DIR / f"Module {module_num}"
    if not mod_dir.exists():
        continue
        
    print(f"\nProcessing Module {module_num}...")
    
    # Walk through the module directory
    for root, dirs, files in os.walk(mod_dir):
        root_path = Path(root)
        
        # Don't process if we're already inside a destination folder (shouldn't happen here)
        
        for file in files:
            fpath = root_path / file
            
            # Determine destination based on extension and contents
            if file.endswith(".ipynb"):
                safe_move(fpath, DIRS["notebooks"] / f"Module {module_num}")
            elif file.endswith(".pkl") or file.endswith(".npz") or file == "model.txt":
                # For LightGBM, model.txt was in a lightgbm folder. Preserve parent name if it's a generic model file
                if file == "model.txt":
                    safe_move(fpath, DIRS["models"] / f"Module {module_num}" / root_path.name)
                else:
                    safe_move(fpath, DIRS["models"] / f"Module {module_num}")
            elif file.endswith(".csv") or file.endswith(".json"):
                # Manifests and evaluation results go to data/final
                if "manifest" in file.lower() or "metric" in file.lower() or "comparison" in file.lower() or "summary" in file.lower() or "eval" in file.lower() or "rule" in file.lower() or "matrix" in file.lower() or "results" in file.lower() or "predict" in file.lower() or "importance" in file.lower():
                    # Preserve model folder name for manifest
                    if "manifest" in file.lower():
                        safe_move(fpath, DIRS["models"] / f"Module {module_num}" / root_path.name)
                    else:
                        safe_move(fpath, DIRS["data_final"] / f"Module {module_num}")
                else:
                    # Generic CSV in a module goes to data/processed
                    safe_move(fpath, DIRS["data_processed"] / f"Module {module_num}")
            elif file.endswith(".png") or file.endswith(".jpg") or file.endswith(".jpeg"):
                # Figures go to notebooks or data/final (let's put them in data/final)
                safe_move(fpath, DIRS["data_final"] / f"Module {module_num}" / "figures")

# Clean up empty module folders
for module_num in range(1, 5):
    mod_dir = BASE_DIR / f"Module {module_num}"
    if mod_dir.exists():
        try:
            # os.removedirs removes all empty parents up to the tree
            # we just want to remove the mod_dir if it's empty, and its subdirs
            for root, dirs, files in os.walk(mod_dir, topdown=False):
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except OSError:
                        pass
            os.rmdir(mod_dir)
            print(f"Cleaned up {mod_dir.name}")
        except OSError:
            print(f"Warning: {mod_dir.name} not empty, skipping delete.")

print("\nRestructuring complete!")
