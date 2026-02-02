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
        # PATH RESOLUTION
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '../../'))
        MODEL_PATH = os.path.join(project_root, "models", "ISL_Model.tflite")
        LABEL_PATH = os.path.join(project_root, "data", "processed", "labels.npy")
        # BRIDGE FILE (For GUI Communication)
        BRIDGE_PATH = os.path.join(project_root, "data", "isl_live.txt")

        # SHARED MEMORY
        shm = shared_memory.SharedMemory(name=shm_name)
        frame_buffer = np.ndarray(shape, dtype=np.uint8, buffer=shm.buf)

        # MODEL LOAD
        mp_holistic = mp.solutions.holistic
        holistic = mp_holistic.Holistic(
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5,
            model_complexity=1
        )

        interpreter = Interpreter(model_path=MODEL_PATH)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        labels_map = np.load(LABEL_PATH, allow_pickle=True).item()
        id_to_label = {v: k for k, v in labels_map.items()}
        print(f"\033[92m[ISL] System Ready. Vocab: {len(id_to_label)}\033[0m")

        # LOGIC VARS
        sequence = collections.deque(maxlen=30)
        prediction_buffer = collections.deque(maxlen=5) 
        
        # --- FILTERS ---
        CONFIDENCE_THRESHOLD = 0.85  # Stricter!
        last_word_time = 0
        COOLDOWN_SECONDS = 2.0       # Don't repeat word for 2s
        last_detected_word = ""

        while not stop_event.is_set():
            if not frame_ready_event.wait(timeout=1.0): continue
            if mode_flag.value != 1:
                sequence.clear()
                prediction_buffer.clear()
                continue

            current_frame = frame_buffer.copy()
            image = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
            results = holistic.process(image)
            
            if results.pose_landmarks:
                keypoints = normalize_features(results)
                sequence.append(keypoints)
                
                if len(sequence) == 30:
                    input_data = np.expand_dims(sequence, axis=0).astype(np.float32)
                    interpreter.set_tensor(input_details[0]['index'], input_data)
                    interpreter.invoke()
                    output = interpreter.get_tensor(output_details[0]['index'])
                    
                    pred_id = np.argmax(output)
                    confidence = np.max(output)
                    word = id_to_label.get(pred_id, "Unknown")

                    if confidence > CONFIDENCE_THRESHOLD: 
                        prediction_buffer.append(pred_id)
                        
                        if prediction_buffer.count(pred_id) == 5:
                            # --- DEBOUNCE LOGIC ---
                            current_time = time.time()
                            is_new_word = word != last_detected_word
                            is_cooldown_over = (current_time - last_word_time) > COOLDOWN_SECONDS
                            
                            if word.lower() != "idle" and word != "Unknown":
                                if is_new_word or is_cooldown_over:
                                    # 1. Console Output
                                    print(f"\033[92m[ISL] >>> RECOGNIZED: {word.upper()} ({confidence:.2f})\033[0m")
                                    
                                    # 2. Send to Queue (for Vision Backend)
                                    if result_queue.empty(): result_queue.put(word)
                                    
                                    # 3. Write to Bridge File (for GUI)
                                    try:
                                        with open(BRIDGE_PATH, "w") as f:
                                            f.write(word)
                                    except: pass

                                    last_word_time = current_time
                                    last_detected_word = word
                                    prediction_buffer.clear()
                    else:
                        prediction_buffer.append(-1)

    except Exception as e:
        traceback.print_exc()
    finally:
        try: shm.close()
        except: pass
        print("[ISL] Stopped")