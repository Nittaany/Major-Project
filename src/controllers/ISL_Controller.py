import mediapipe as mp
import numpy as np
import time
from multiprocessing import shared_memory
import collections
import cv2
import os
import sys
import traceback

# --- 1. EMBEDDED NORMALIZATION ---
def normalize_features(results):
    if results.pose_landmarks:
        pose = np.array([[res.x, res.y, res.z] for res in results.pose_landmarks.landmark[:25]])
    else:
        pose = np.zeros((25, 3))
    
    if results.left_hand_landmarks:
        lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark])
    else:
        lh = np.zeros((21, 3))

    if results.right_hand_landmarks:
        rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark])
    else:
        rh = np.zeros((21, 3))
    
    left_shoulder = pose[11]
    right_shoulder = pose[12]
    
    chest_center = (left_shoulder + right_shoulder) / 2.0
    shoulder_width = np.linalg.norm(left_shoulder - right_shoulder)
    if shoulder_width < 0.01: shoulder_width = 1.0

    def standardize(landmarks):
        return (landmarks - chest_center) / shoulder_width

    return np.concatenate([
        standardize(pose).flatten(), 
        standardize(lh).flatten(), 
        standardize(rh).flatten()
    ])

# --- 2. TFLITE SETUP ---
try:
    import tensorflow as tf
    Interpreter = tf.lite.Interpreter
except:
    from tflite_runtime.interpreter import Interpreter

def run_isl(shm_name, shape, frame_ready_event, stop_event, result_queue, mode_flag):
    print("\033[96m[ISL] Process Launching...\033[0m")
    
    try:
        # --- SHARED MEMORY CONNECT ---
        try:
            shm = shared_memory.SharedMemory(name=shm_name)
            frame_buffer = np.ndarray(shape, dtype=np.uint8, buffer=shm.buf)
            print("[ISL] Connected to Shared Memory.")
        except Exception as e:
            print(f"\033[91m[ISL] CRITICAL ERROR: Shared Memory Failed. {e}\033[0m")
            return

        # --- MEDIAPIPE SETUP ---
        mp_holistic = mp.solutions.holistic
        holistic = mp_holistic.Holistic(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5,
            model_complexity=1
        )

        # --- MODEL LOADING (FIXED PATHS) ---
        # Get the directory where THIS script is located (src/controllers)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up two levels to get Project Root (Major-Project)
        project_root = os.path.abspath(os.path.join(current_dir, '../../'))
        
        MODEL_PATH = os.path.join(project_root, "models", "ISL_Model.tflite")
        LABEL_PATH = os.path.join(project_root, "data", "processed", "labels.npy")
        
        print(f"[ISL DEBUG] Looking for model at: {MODEL_PATH}")
        
        model_loaded = False
        id_to_label = {}
        
        if os.path.exists(MODEL_PATH) and os.path.exists(LABEL_PATH):
            try:
                interpreter = Interpreter(model_path=MODEL_PATH)
                interpreter.allocate_tensors()
                input_details = interpreter.get_input_details()
                output_details = interpreter.get_output_details()
                
                labels_map = np.load(LABEL_PATH, allow_pickle=True).item()
                id_to_label = {v: k for k, v in labels_map.items()}
                
                model_loaded = True
                print(f"\033[92m[ISL] Model Loaded. Vocab: {len(id_to_label)} words\033[0m")
            except Exception as e:
                print(f"\033[91m[ISL] Model Corruption Error: {e}\033[0m")
        else:
            print(f"\033[93m[ISL] PATH ERROR: Files missing!\033[0m")
            print(f"   Expected Model: {MODEL_PATH}")
            print(f"   Expected Labels: {LABEL_PATH}")

        # --- BUFFERS ---
        sequence = collections.deque(maxlen=30)
        prediction_buffer = collections.deque(maxlen=5) 

        # --- MAIN LOOP ---
        print("[ISL] Loop Started. Waiting for frames...")
        
        while not stop_event.is_set():
            if not frame_ready_event.wait(timeout=1.0):
                continue

            if mode_flag.value != 1:
                if len(sequence) > 0: sequence.clear()
                if len(prediction_buffer) > 0: prediction_buffer.clear()
                continue

            # Process Frame
            current_frame = frame_buffer.copy()
            image = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(image)
            
            if results.pose_landmarks:
                keypoints = normalize_features(results)
                sequence.append(keypoints)
                
                if model_loaded and len(sequence) == 30:
                    input_data = np.expand_dims(sequence, axis=0).astype(np.float32)
                    
                    interpreter.set_tensor(input_details[0]['index'], input_data)
                    interpreter.invoke()
                    output = interpreter.get_tensor(output_details[0]['index'])
                    
                    pred_id = np.argmax(output)
                    confidence = np.max(output)
                    word = id_to_label.get(pred_id, "Unknown")

                    # Debug Print (Uncomment to debug live confidence)
                    # print(f"{word} ({confidence:.2f})")

                    if confidence > 0.60: 
                        prediction_buffer.append(pred_id)
                        
                        if prediction_buffer.count(pred_id) == 5:
                            if word.lower() != "idle" and word != "Unknown":
                                if result_queue.empty():
                                    result_queue.put(word)
                                    print(f"\033[92m[ISL] >>> OUTPUT: {word} ({confidence:.2f})\033[0m")
                                
                                prediction_buffer.clear()
                    else:
                        prediction_buffer.append(-1)

    except Exception as e:
        print(f"\033[91m[ISL] PROCESS CRASHED:\033[0m")
        traceback.print_exc()
        
    finally:
        try:
            shm.close()
        except:
            pass
        print("[ISL] Process Stopped")