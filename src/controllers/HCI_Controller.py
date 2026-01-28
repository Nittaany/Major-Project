import mediapipe as mp
import pyautogui
import numpy as np
import time
import cv2  # <--- FIXED: Import at the top
from multiprocessing import shared_memory
from utils.math_utils import SigmoidController

# MacOS Safety Settings
pyautogui.FAILSAFE = False

def run_hci(shm_name, shape, frame_ready_event, stop_event):
    print("[HCI] Process Started. Waiting for frames...")
    
    # Connect to Shared Memory
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
        frame_buffer = np.ndarray(shape, dtype=np.uint8, buffer=shm.buf)
    except FileNotFoundError:
        print("[HCI] Error: Shared Memory not found.")
        return

    # Initialize MediaPipe Hands (Fast Model)
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.5, # Lowered for easier detection
        min_tracking_confidence=0.5,
        model_complexity=0 
    )

    physics = SigmoidController(min_gain=1.5, max_gain=15.0, v_inf=30, k=0.15)
    
    prev_x, prev_y = 0, 0
    
    try:
        while not stop_event.is_set():
            # Wait for signal from app.py
            if not frame_ready_event.wait(timeout=2.0):
                print("[HCI] Waiting for Camera...")
                continue 
            
            # Read Frame
            current_frame = frame_buffer.copy() 
            
            # Process
            rgb_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                # Get Index Finger Tip
                lm = results.multi_hand_landmarks[0].landmark[8]
                h, w, _ = shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                
                # Calculate Physics
                velocity = np.sqrt((cx - prev_x)**2 + (cy - prev_y)**2)
                gain = physics.get_gain(velocity)
                dx = (cx - prev_x) * gain
                dy = (cy - prev_y) * gain
                
                # Move Mouse
                try:
                    pyautogui.moveRel(dx, dy, _pause=False)
                    # print(f"[HCI] Moving: {dx:.2f}, {dy:.2f}") # Uncomment to debug movement
                except:
                    pass

                prev_x, prev_y = cx, cy
            
    except Exception as e:
        print(f"[HCI] Crash: {e}")
    finally:
        shm.close()
        print("[HCI] Process Stopped")