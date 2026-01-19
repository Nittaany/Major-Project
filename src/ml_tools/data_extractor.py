import cv2
import numpy as np
import os
import mediapipe as mp
from tqdm import tqdm

# --- CONFIGURATION ---
DATA_PATH = "data/raw/ProcessedData_vivit" 
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

def find_video_files(directory):
    """Recursively find all video files in a directory (Case Insensitive)"""
    video_extensions = ('.mov', '.mp4', '.avi', '.mkv', '.webm')
    found_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(video_extensions):
                found_files.append(os.path.join(root, file))
    return found_files

def process_videos():
    if not os.path.exists(DATA_PATH):
        print(f"[ERROR] Path not found: {DATA_PATH}")
        return
    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    # Get Classes
    actions = [d for d in os.listdir(DATA_PATH) if os.path.isdir(os.path.join(DATA_PATH, d)) and not d.startswith('.')]
    actions.sort()
    
    sequences = []
    labels = []
    label_map = {label: num for num, label in enumerate(actions)}
    
    print(f"[INFO] Found {len(actions)} classes. Starting Deep Scan...")

    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        
        # Loop over actions
        for action in tqdm(actions, desc="Processing"):
            class_path = os.path.join(DATA_PATH, action)
            
            # UPGRADE: Recursive search for videos
            video_paths = find_video_files(class_path)
            
            # DEBUG: Print warning if a class is empty
            if not video_paths:
                # tqdm.write(f"[WARNING] No videos found in {action}!") 
                continue

            for video_path in video_paths:
                cap = cv2.VideoCapture(video_path)
                temp_sequence = []
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret: break
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = holistic.process(image)
                    temp_sequence.append(extract_keypoints(results))
                cap.release()
                
                if len(temp_sequence) > 5:
                    sequences.append(resize_sequence(temp_sequence, TARGET_FRAMES))
                    labels.append(label_map[action])

    print("\n[INFO] Finalizing...")
    X = np.array(sequences)
    y = np.array(labels)
    
    if X.shape[0] == 0:
        print("\n[FATAL ERROR] Still found 0 videos. Please check your folder structure manually.")
        print(f"Script looked inside: {DATA_PATH}/[class_name]/")
        print("And looked for: .mov, .mp4, .avi (case insensitive)")
    else:
        print(f"SUCCESS! Extracted {X.shape[0]} videos.")
        print(f"X Shape: {X.shape}") 
        print(f"y Shape: {y.shape}")
        np.save(os.path.join(OUTPUT_PATH, "X.npy"), X)
        np.save(os.path.join(OUTPUT_PATH, "y.npy"), y)
        np.save(os.path.join(OUTPUT_PATH, "labels.npy"), label_map)

if __name__ == "__main__":
    process_videos()