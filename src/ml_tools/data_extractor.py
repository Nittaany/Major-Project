import cv2
import numpy as np
import os
import mediapipe as mp
import sys
from tqdm import tqdm

# Add project root to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.utils.normalization import normalize_features

# --- CONFIGURATION ---
DATA_PATH = "data/raw/INCLUDE50" 
OUTPUT_PATH = "data/processed"
TARGET_FRAMES = 30

# --- THE GOLD STANDARD WHITELIST ---
# The script will ONLY process folders that match these endings.
WHITELIST_DIRS = [
    "behaviour/idle",
    "Greetings/48. Hello",
    "Greetings/55. Thank you",
    "Greetings/51. Good Morning",
    "Adjectives/94. good",
    "Adjectives/3. happy",
    "Days_and_Time/86. Time",
    "People/61. Father",
    "Pronouns/40. I",
    "Pronouns/46. you (plural)",
    "Jobs/84. Teacher"
]

mp_holistic = mp.solutions.holistic

def resize_sequence(sequence, target_length):
    """Interpolate sequence to fixed length (30 frames)"""
    sequence = np.array(sequence)
    if sequence.shape[0] == 0: return np.zeros((target_length, sequence.shape[1]))
    res = np.zeros((target_length, sequence.shape[1]))
    for j in range(sequence.shape[1]):
        res[:, j] = np.interp(np.linspace(0, sequence.shape[0], target_length), np.arange(sequence.shape[0]), sequence[:, j])
    return res

def clean_folder_name(folder_name):
    # Handles "48. Hello" -> "hello"
    if '.' in folder_name:
        name = folder_name.split('.', 1)[-1].strip()
    else:
        name = folder_name
    return name.lower()

def is_whitelisted(root_path):
    # Check if the current folder path ends with any of our whitelist items
    # Normalize slashes for Windows/Mac compatibility
    norm_path = root_path.replace('\\', '/')
    for target in WHITELIST_DIRS:
        if norm_path.endswith(target):
            return True
    return False

def process_videos():
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    sequences = []
    labels = []
    label_map = {}
    current_label_id = 0
    
    print(f"[INFO] Extraction Engine Started.")
    print(f"[INFO] Mode: TARGETED EXTRACTION (11 Classes Only)")

    with mp_holistic.Holistic(
        min_detection_confidence=0.5, 
        min_tracking_confidence=0.5, 
        model_complexity=1) as holistic:
        
        # Walk through all folders
        for root, dirs, files in os.walk(DATA_PATH):
            
            # 1. WHITELIST CHECK
            if not is_whitelisted(root):
                continue

            # 2. FILE FILTER
            video_files = [f for f in files if f.lower().endswith(('.mov', '.mp4')) and not f.startswith('.')]
            if not video_files: continue

            # 3. GET CLASS NAME
            folder_name = os.path.basename(root)
            class_name = clean_folder_name(folder_name)
            
            # Map "46. you (plural)" -> "you (plural)"
            # Handle duplicates if any
            if class_name not in label_map:
                label_map[class_name] = current_label_id
                current_label_id += 1
                tqdm.write(f"[ACCEPTED] {class_name} (ID: {label_map[class_name]})")

            # 4. PROCESS
            for video_file in tqdm(video_files, desc=f"Processing {class_name}", leave=False):
                video_path = os.path.join(root, video_file)
                cap = cv2.VideoCapture(video_path)
                temp_sequence = []
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret: break
                    
                    # No Flip (Standard)
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = holistic.process(image)
                    
                    keypoints = normalize_features(results)
                    temp_sequence.append(keypoints)
                
                cap.release()
                
                if len(temp_sequence) > 5:
                    sequences.append(resize_sequence(temp_sequence, TARGET_FRAMES))
                    labels.append(label_map[class_name])

    print("\n[INFO] Saving Arrays...")
    X = np.array(sequences)
    y = np.array(labels)
    
    if X.shape[0] == 0:
        print("[ERROR] No data found! Check WHITELIST_DIRS paths.")
    else:
        np.save(os.path.join(OUTPUT_PATH, "X.npy"), X)
        np.save(os.path.join(OUTPUT_PATH, "y.npy"), y)
        np.save(os.path.join(OUTPUT_PATH, "labels.npy"), label_map)
        print(f"[SUCCESS] Extracted {len(X)} high-quality sequences.")
        print(f"Shape: {X.shape}")
        print(f"Classes: {list(label_map.keys())}")

if __name__ == "__main__":
    process_videos()