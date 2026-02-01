# import cv2
# import numpy as np
# import os
# import mediapipe as mp
# import sys

# # Add project root to path so we can import utils
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# from src.utils.normalization import normalize_features

# # --- CONFIGURATION ---
# OUTPUT_PATH = "data/processed"
# # We add "Idle" to your list of target words
# CLASSES_TO_RECORD = ["Idle", "hello", "thank you", "good", "happy", "i", "you"] 
# SAMPLES_PER_CLASS = 20  # 20 solid samples per class is enough for fine-tuning
# FRAMES_PER_SAMPLE = 30  # 1 second

# mp_holistic = mp.solutions.holistic

# def record_class(class_name, start_id, holistic, cap):
#     print(f"\n[RECORDING] Class: '{class_name}'")
#     print(f"Goal: {SAMPLES_PER_CLASS} samples.")
#     print("Press 'S' to start recording ONE sample.")
#     print("Press 'Q' to skip/quit.")
    
#     sequences = []
#     labels = []
    
#     while len(sequences) < SAMPLES_PER_CLASS:
#         ret, frame = cap.read()
#         if not ret: break
        
#         # 1. MIRROR FLIP (Match the HCI Controller logic)
#         frame = cv2.flip(frame, 1)
        
#         # UI Overlay
#         cv2.putText(frame, f"TARGET: {class_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
#         cv2.putText(frame, f"Saved: {len(sequences)}/{SAMPLES_PER_CLASS}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
#         cv2.imshow('Data Recorder', frame)
        
#         key = cv2.waitKey(1)
#         if key == ord('q'): return None, None
        
#         if key == ord('s'):
#             # Record 30 Frames
#             temp_seq = []
#             print(f"Recording {class_name}...")
            
#             for _ in range(FRAMES_PER_SAMPLE):
#                 ret, frame = cap.read()
#                 if not ret: break
                
#                 # FLIP BEFORE PROCESSING
#                 frame = cv2.flip(frame, 1)
                
#                 image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#                 results = holistic.process(image)
                
#                 # USE THE NEW NORMALIZATION
#                 keypoints = normalize_features(results)
#                 temp_seq.append(keypoints)
                
#                 # Visual Feedback (Red Dot)
#                 cv2.circle(frame, (30, 30), 20, (0, 0, 255), -1)
#                 cv2.imshow('Data Recorder', frame)
#                 cv2.waitKey(1)
            
#             sequences.append(temp_seq)
#             labels.append(start_id)
#             print(f" -> Sample {len(sequences)} Saved.")
            
#     return sequences, labels

# def main():
#     if not os.path.exists(OUTPUT_PATH):
#         os.makedirs(OUTPUT_PATH)
    
#     cap = cv2.VideoCapture(0) # Or 1 if on Mac external cam
    
#     all_sequences = []
#     all_labels = []
#     label_map = {}
    
#     with mp_holistic.Holistic(min_detection_confidence=0.5, min_tracking_confidence=0.5) as holistic:
#         for idx, class_name in enumerate(CLASSES_TO_RECORD):
#             label_map[class_name] = idx
            
#             # Allow user to prepare
#             print(f"\nPREPARING FOR: {class_name}")
            
#             seqs, lbls = record_class(class_name, idx, holistic, cap)
#             if seqs is None: 
#                 print("Recording stopped.")
#                 break
                
#             all_sequences.extend(seqs)
#             all_labels.extend(lbls)
            
#     cap.release()
#     cv2.destroyAllWindows()
    
#     # Merge with existing data if possible, or save new
#     X = np.array(all_sequences)
#     y = np.array(all_labels)
    
#     print(f"\n[COMPLETED] Recorded Shape: {X.shape}")
#     np.save(f"{OUTPUT_PATH}/X_custom.npy", X)
#     np.save(f"{OUTPUT_PATH}/y_custom.npy", y)
#     np.save(f"{OUTPUT_PATH}/labels_custom.npy", label_map)
#     print("Custom Data Saved. Next Step: Merge with INCLUDE-50.")

# if __name__ == "__main__":
#     main()

import cv2
import os
import time

# --- CONFIGURATION ---
# We save directly into the raw data folder
DATASET_ROOT = "data/raw/INCLUDE50" 

# Add the classes you want to "Inject" into the dataset
# 'Idle' is the critical one. Add others like 'Hello', 'Help', etc.
CLASSES_TO_RECORD = ["Idle", "Hello", "Help", "Thanks", "Good", "Bad"]
VIDEOS_PER_CLASS = 20
DURATION_SEC = 2  # 2 seconds per clip

def record_class(class_name):
    save_dir = os.path.join(DATASET_ROOT, class_name)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    cap = cv2.VideoCapture(0) # Change to 1 if using external cam
    
    print(f"\n[RECORDING] Class: {class_name}")
    print(f"Saving to: {save_dir}")
    print("Press 'S' to start recording a 2-second clip.")
    print("Press 'Q' to skip this class.")
    
    count = len([n for n in os.listdir(save_dir) if n.endswith(".mp4")])
    
    while count < VIDEOS_PER_CLASS:
        ret, frame = cap.read()
        if not ret: break
        
        # Mirror for display only
        show_frame = cv2.flip(frame, 1)
        cv2.putText(show_frame, f"Class: {class_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(show_frame, f"Recorded: {count}/{VIDEOS_PER_CLASS}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.imshow("Recorder", show_frame)
        
        key = cv2.waitKey(1)
        if key == ord('q'): break
        
        if key == ord('s'):
            # Start Recording
            filename = os.path.join(save_dir, f"custom_{int(time.time())}.mp4")
            # Define codec
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(filename, fourcc, 30.0, (640, 480))
            
            start_time = time.time()
            while (time.time() - start_time) < DURATION_SEC:
                ret, frame = cap.read()
                if ret:
                    # Note: We do NOT flip the saved video. 
                    # The dataset expects raw camera feed.
                    # We will flip it in the extractor if needed.
                    out.write(frame)
                    
                    # Show "Recording" UI
                    show_frame = cv2.flip(frame, 1)
                    cv2.circle(show_frame, (30, 30), 20, (0, 0, 255), -1)
                    cv2.imshow("Recorder", show_frame)
                    cv2.waitKey(1)
            
            out.release()
            count += 1
            print(f"Saved {filename}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    for cls in CLASSES_TO_RECORD:
        record_class(cls)