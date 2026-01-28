import mediapipe as mp
import pyautogui
import numpy as np
import time
import cv2
import math
from enum import IntEnum
from multiprocessing import shared_memory
from utils.math_utils import SigmoidController

# --- CONFIGURATION ---
pyautogui.FAILSAFE = False # Prevent crash at corners
SMOOTHING = 0.5            # 0.0 to 1.0 (Higher = Smoother but laggier)
CLICK_THRESHOLD = 0.05     # Distance to trigger click

# --- ENUMS (Restored from your original code) ---
class Gest(IntEnum):
    FIST = 0
    PINKY = 1
    RING = 2
    MID = 4
    LAST3 = 7
    INDEX = 8
    FIRST2 = 12
    THREE_FINGER = 14
    LAST4 = 15
    THUMB = 16    
    PALM = 31
    V_GEST = 33
    TWO_FINGER_CLOSED = 34
    PINCH_MAJOR = 35
    PINCH_MINOR = 36

class HLabel(IntEnum):
    MINOR = 0
    MAJOR = 1

# --- HAND RECOGNITION LOGIC (Restored) ---
class HandRecog:
    def __init__(self, hand_label):
        self.finger = 0
        self.ori_gesture = Gest.PALM
        self.prev_gesture = Gest.PALM
        self.frame_count = 0
        self.hand_result = None
        self.hand_label = hand_label
    
    def update_hand_result(self, hand_result):
        self.hand_result = hand_result

    def get_signed_dist(self, point):
        sign = -1
        if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
            sign = 1
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        return math.sqrt(dist) * sign
    
    def get_dist(self, point):
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        return math.sqrt(dist)
    
    def get_dz(self, point):
        return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)
    
    def set_finger_state(self):
        if self.hand_result == None: return
        points = [[8,5,0],[12,9,0],[16,13,0],[20,17,0]]
        self.finger = 0
        for idx, point in enumerate(points):
            dist = self.get_signed_dist(point[:2])
            dist2 = self.get_signed_dist(point[1:])
            try: ratio = round(dist/dist2,1)
            except: ratio = round(dist/0.01,1)
            self.finger = self.finger << 1
            if ratio > 0.5 : self.finger = self.finger | 1
    
    def get_gesture(self):
        if self.hand_result == None: return Gest.PALM
        current_gesture = Gest.PALM
        
        # Pinch Logic
        if self.finger in [Gest.LAST3, Gest.LAST4] and self.get_dist([8,4]) < CLICK_THRESHOLD:
            if self.hand_label == HLabel.MINOR: current_gesture = Gest.PINCH_MINOR
            else: current_gesture = Gest.PINCH_MAJOR
        
        elif Gest.FIRST2 == self.finger:
            point = [[8,12],[5,9]]
            dist1 = self.get_dist(point[0]); dist2 = self.get_dist(point[1])
            ratio = dist1/dist2
            if ratio > 1.7: current_gesture = Gest.V_GEST
            else:
                if self.get_dz([8,12]) < 0.1: current_gesture = Gest.TWO_FINGER_CLOSED
                else: current_gesture = Gest.MID
        else:
            current_gesture = self.finger
        
        if current_gesture == self.prev_gesture: self.frame_count += 1
        else: self.frame_count = 0
        self.prev_gesture = current_gesture
        
        if self.frame_count > 4: self.ori_gesture = current_gesture
        return self.ori_gesture

# --- MAIN PROCESS ---
def run_hci(shm_name, shape, frame_ready_event, stop_event):
    print("[HCI] Process Started. Waiting for frames...")
    
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
        frame_buffer = np.ndarray(shape, dtype=np.uint8, buffer=shm.buf)
    except FileNotFoundError:
        print("[HCI] Error: Shared Memory not found.")
        return

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        model_complexity=0
    )

    physics = SigmoidController(min_gain=1.5, max_gain=15.0, v_inf=30, k=0.15)
    recog = HandRecog(HLabel.MAJOR)
    
    # State Variables
    prev_x, prev_y = 0, 0
    grab_flag = False
    last_click_time = 0
    screen_w, screen_h = pyautogui.size()
    
    try:
        while not stop_event.is_set():
            if not frame_ready_event.wait(timeout=2.0): continue 
            
            # 1. Get Frame
            current_frame = frame_buffer.copy()
            rgb_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                recog.update_hand_result(hand_landmarks)
                recog.set_finger_state()
                gesture = recog.get_gesture()
                
                # --- COORDINATE MAPPING (FIXED STICKING) ---
                # Get Tip of Index Finger
                lm = hand_landmarks.landmark[8] 
                h, w, _ = shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                
                # Calculate Ballistics
                velocity = np.sqrt((cx - prev_x)**2 + (cy - prev_y)**2)
                gain = physics.get_gain(velocity)
                
                dx = (cx - prev_x) * gain
                dy = (cy - prev_y) * gain
                
                # --- GESTURE HANDLING ---
                
                # 1. MOVE (V-Gesture)
                if gesture == Gest.V_GEST:
                    try:
                        # Move Relative, but check bounds? 
                        # Actually, pyautogui.moveRel handles bounds better than moveTo if failsafe is False
                        pyautogui.moveRel(dx, dy, _pause=False)
                    except: pass

                # 2. LEFT CLICK (Pinch Index/Major)
                elif gesture == Gest.PINCH_MAJOR:
                    if time.time() - last_click_time > 0.5:
                        pyautogui.click()
                        last_click_time = time.time()
                        print("[HCI] Left Click")

                # 3. DRAG (Fist)
                elif gesture == Gest.FIST:
                    if not grab_flag:
                        grab_flag = True
                        pyautogui.mouseDown()
                        print("[HCI] Drag Start")
                    pyautogui.moveRel(dx, dy, _pause=False)
                
                # Release Drag if not Fist
                if gesture != Gest.FIST and grab_flag:
                    grab_flag = False
                    pyautogui.mouseUp()
                    print("[HCI] Drag Drop")

                # 4. RIGHT CLICK (Middle Finger / Pinch Minor)
                elif gesture == Gest.MID:
                    if time.time() - last_click_time > 1.0:
                        pyautogui.rightClick()
                        last_click_time = time.time()
                        print("[HCI] Right Click")
                        
                # 5. SCREENSHOT (Pinky)
                elif gesture == Gest.PINKY:
                    if time.time() - last_click_time > 2.0:
                        pyautogui.hotkey('command', 'shift', '3')
                        last_click_time = time.time()
                        print("[HCI] Screenshot")

                # 6. APP SWITCH (Three Fingers)
                elif gesture == Gest.THREE_FINGER:
                     if time.time() - last_click_time > 2.0:
                        pyautogui.hotkey('command', 'tab')
                        last_click_time = time.time()
                        print("[HCI] App Switch")

                # Update State
                prev_x, prev_y = cx, cy
            
    except Exception as e:
        print(f"[HCI] Crash: {e}")
    finally:
        shm.close()
        print("[HCI] Process Stopped")