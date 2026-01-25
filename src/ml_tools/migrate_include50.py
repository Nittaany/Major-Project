import os
import shutil
from tqdm import tqdm

# --- CONFIGURATION ---
# 1. Your SSD Path (Where the INCLUDE DATABASE is)
SOURCE_ROOT = "/Volumes/NIT/MAJOR-PROJECT/archive" 

# 2. Your Mac Path (Where we want the clean data)
DEST_ROOT = "data/raw/INCLUDE50"

# 3. The Map Files (You just saved these)
TRAIN_LIST = "src/ml_tools/include50_train.txt"
TEST_LIST = "src/ml_tools/include50_test.txt"

def read_file_list(path):
    with open(path, 'r') as f:
        # Strip newlines and spaces
        return [line.strip() for line in f.readlines() if line.strip()]

def migrate():
    if not os.path.exists(SOURCE_ROOT):
        print(f"[ERROR] SSD not found at: {SOURCE_ROOT}")
        return

    # Load paths
    files_to_copy = []
    try:
        files_to_copy += read_file_list(TRAIN_LIST)
        files_to_copy += read_file_list(TEST_LIST)
        print(f"[INFO] Found {len(files_to_copy)} files in the official lists.")
    except FileNotFoundError:
        print("[ERROR] Map files not found. Did you save include50_train.txt in src/ml_tools/?")
        return

    # Destination
    if not os.path.exists(DEST_ROOT):
        os.makedirs(DEST_ROOT)

    success = 0
    missing = 0

    print("[INFO] Starting Migration...")
    for rel_path in tqdm(files_to_copy):
        # Fix path separators if needed (Windows uses \, Mac uses /)
        rel_path = rel_path.replace("\\", "/")
        
        src_path = os.path.join(SOURCE_ROOT, rel_path)
        dest_path = os.path.join(DEST_ROOT, rel_path)

        if os.path.exists(src_path):
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(src_path, dest_path)
            success += 1
        else:
            # Try finding it without the parent folder? 
            # Sometimes lists say "Adjectives/1. loud/..." but folders are "Adjectives_1of8/Adjectives/..."
            # For now, let's just log it.
            missing += 1

    print("\n--- DONE ---")
    print(f"Copied: {success}")
    print(f"Missing: {missing}")
    
    if missing > 100:
        print("[WARNING] High missing count. Check if your SSD folder structure matches the text file paths.")

if __name__ == "__main__":
    migrate()