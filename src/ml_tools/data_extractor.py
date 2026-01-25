import cv2
import numpy as np
import os
import mediapipe as mp
from tqdm import tqdm

# --- CONFIGURATION ---
# Pointing to your new CLEAN dataset
DATA_PATH = "data/raw/INCLUDE50" 
OUTPUT_PATH = "data/processed"
TARGET_FRAMES = 30

mp_holistic = mp.solutions.holistic

def extract_keypoints(results):
    # 1. Pose (0-23)
    if results.pose_landmarks:
        pose = np.array([[res.x, res.y, res.z] for res in results.pose_landmarks.landmark[:24]]).flatten()
    else:
        pose = np.zeros(24 * 3)
    
    # 2. Left Hand
    if results.left_hand_landmarks:
        lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten()
    else:
        lh = np.zeros(21 * 3)
        
    # 3. Right Hand
    if results.right_hand_landmarks:
        rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten()
    else:
        rh = np.zeros(21 * 3)
        
    return np.concatenate([pose, lh, rh])

def resize_sequence(sequence, target_length):
    sequence = np.array(sequence)
    if sequence.shape[0] == 0: return np.zeros((target_length, sequence.shape[1]))
    res = np.zeros((target_length, sequence.shape[1]))
    for j in range(sequence.shape[1]):
        res[:, j] = np.interp(np.linspace(0, sequence.shape[0], target_length), np.arange(sequence.shape[0]), sequence[:, j])
    return res

def clean_folder_name(folder_name):
    """
    Converts '1. loud' -> 'loud', '10. Mean' -> 'mean'
    """
    if '.' in folder_name:
        name = folder_name.split('.', 1)[-1].strip()
    else:
        name = folder_name
    return name.lower()

def process_videos():
    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] Path not found: {DATA_PATH}")
        return
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    sequences = []
    labels = []
    classes_found = set()
    
    print(f"[INFO] Scanning {DATA_PATH}...")
    
    # 1. First Pass: Identify all Unique Classes
    for root, dirs, files in os.walk(DATA_PATH):
        for d in dirs:
            # We assume the leaf folders (containing videos) are the classes
            # But the structure is Category/1. Word.
            # So we check if the folder starts with a digit like "1. " or just look at all lowest level folders
            pass 

    # We will build the label map dynamically as we process
    label_map = {}
    current_label_id = 0

    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        
        # Deep walk
        for root, dirs, files in os.walk(DATA_PATH):
            video_files = [f for f in files if f.lower().endswith(('.mov', '.mp4'))]
            
            if not video_files:
                continue

            # If we found videos, this folder is a Class
            folder_name = os.path.basename(root)
            clean_name = clean_folder_name(folder_name)
            
            # Add to label map if new
            if clean_name not in label_map:
                label_map[clean_name] = current_label_id
                current_label_id += 1
                tqdm.write(f"[NEW CLASS] Found '{clean_name}' (ID: {label_map[clean_name]})")

            # Process Videos
            for video_file in tqdm(video_files, desc=f"Processing {clean_name}", leave=False):
                video_path = os.path.join(root, video_file)
                cap = cv2.VideoCapture(video_path)
                temp_sequence = []
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret: break
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = holistic.process(image)
                    temp_sequence.append(extract_keypoints(results))
                cap.release()
                
                if len(temp_sequence) > 10:
                    sequences.append(resize_sequence(temp_sequence, TARGET_FRAMES))
                    labels.append(label_map[clean_name])

    print("\n[INFO] Finalizing...")
    X = np.array(sequences)
    y = np.array(labels)
    
    if X.shape[0] == 0:
        print("[ERROR] No data extracted.")
    else:
        print(f"SUCCESS! Extracted {X.shape[0]} videos.")
        print(f"Classes Found: {len(label_map)}")
        print(f"X Shape: {X.shape}") 
        print(f"y Shape: {y.shape}")
        
        # Save
        np.save(os.path.join(OUTPUT_PATH, "X.npy"), X)
        np.save(os.path.join(OUTPUT_PATH, "y.npy"), y)
        np.save(os.path.join(OUTPUT_PATH, "labels.npy"), label_map)
        print(f"Data saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    process_videos()