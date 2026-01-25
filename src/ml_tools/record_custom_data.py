import cv2
import numpy as np
import os
import mediapipe as mp
import time

# --- CONFIGURATION ---
OUTPUT_PATH = "data/processed" 
TARGET_CLASS = "Idle"       # We are recording the 'Idle' class
SAMPLES_TO_RECORD = 50      # 50 samples is plenty
FRAMES_PER_SAMPLE = 30      # 1 second per sample

mp_holistic = mp.solutions.holistic

def extract_features(results):
    # Same extraction logic as your main app
    if results.pose_landmarks:
        pose = np.array([[res.x, res.y, res.z] for res in results.pose_landmarks.landmark[:24]]).flatten()
    else: pose = np.zeros(24 * 3)
    if results.left_hand_landmarks:
        lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark]).flatten()
    else: lh = np.zeros(21 * 3)
    if results.right_hand_landmarks:
        rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark]).flatten()
    else: rh = np.zeros(21 * 3)
    return np.concatenate([pose, lh, rh])

def record():
    # Load existing data to append to it
    try:
        X = np.load(f"{OUTPUT_PATH}/X.npy")
        y = np.load(f"{OUTPUT_PATH}/y.npy")
        labels_map = np.load(f"{OUTPUT_PATH}/labels.npy", allow_pickle=True).item()
        print(f"[INFO] Loaded existing data: {X.shape}")
    except:
        print("[ERROR] Could not load X.npy. Run this ONLY after you have your main dataset ready.")
        return

    # Add 'Idle' to the label map if not there
    if TARGET_CLASS not in labels_map:
        new_id = len(labels_map)
        labels_map[TARGET_CLASS] = new_id
        print(f"[NEW CLASS] Added '{TARGET_CLASS}' with ID {new_id}")
    else:
        print(f"[INFO] Appending to existing class '{TARGET_CLASS}'")
    
    target_id = labels_map[TARGET_CLASS]
    cap = cv2.VideoCapture(0)
    
    new_sequences = []
    new_labels = []

    with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
        print(f"--- PREPARE TO RECORD '{TARGET_CLASS}' ---")
        print("Press 's' to start recording a sequence.")
        print("Press 'q' to quit.")
        
        while len(new_sequences) < SAMPLES_TO_RECORD:
            ret, frame = cap.read()
            if not ret: break
            
            cv2.putText(frame, f"Recorded: {len(new_sequences)}/{SAMPLES_TO_RECORD}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow('Recorder', frame)
            
            key = cv2.waitKey(1)
            if key == ord('q'): break
            if key == ord('s'):
                # Record one 30-frame sequence
                temp_seq = []
                for _ in range(FRAMES_PER_SAMPLE):
                    ret, frame = cap.read()
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    results = holistic.process(image)
                    temp_seq.append(extract_features(results))
                    
                    cv2.putText(frame, "RECORDING...", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    cv2.imshow('Recorder', frame)
                    cv2.waitKey(1)
                
                new_sequences.append(temp_seq)
                new_labels.append(target_id)
                print(f"Saved Sample {len(new_sequences)}")

    cap.release()
    cv2.destroyAllWindows()
    
    # Merge and Save
    if len(new_sequences) > 0:
        X_new = np.concatenate([X, np.array(new_sequences)])
        y_new = np.concatenate([y, np.array(new_labels)])
        
        np.save(f"{OUTPUT_PATH}/X.npy", X_new)
        np.save(f"{OUTPUT_PATH}/y.npy", y_new)
        np.save(f"{OUTPUT_PATH}/labels.npy", labels_map)
        print("[SUCCESS] Data Saved & Merged!")

if __name__ == "__main__":
    record()