import mediapipe as mp
import pyautogui
import numpy as np
import time
import math
import cv2
from multiprocessing import shared_memory
from enum import Enum, auto
from collections import deque

# ═══════════════════════════════════════════════════════════════════
# 1. CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
pyautogui.FAILSAFE = False
SCREEN_W, SCREEN_H = pyautogui.size()

# TRACKPAD PHYSICS
SENSITIVITY = 1.3       
SMOOTHING = 1.0         

# GESTURE THRESHOLDS
PINCH_THRESHOLD = 0.04   # Relaxed slightly (0.03 -> 0.04) for easier clicking
FIST_THRESHOLD = 0.04    # Distance check for Fist detection

# TIMERS
CLICK_COOLDOWN = 0.3
ACTION_COOLDOWN = 1.0

# ═══════════════════════════════════════════════════════════════════
# 2. UTILS: OneEuroFilter
# ═══════════════════════════════════════════════════════════════════
class OneEuroFilter:
    def __init__(self, min_cutoff=0.05, beta=1.0, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = 0.0
        self.t_prev = None

    def exponential_smoothing(self, a, x, x_prev):
        return a * x + (1 - a) * x_prev

    def filter(self, x, t):
        if self.x_prev is None:
            self.x_prev = x
            self.t_prev = t
            return x
        t_e = t - self.t_prev
        if t_e <= 0: return self.x_prev
        
        dx = (x - self.x_prev) / t_e
        a_d = 2 * math.pi * self.d_cutoff * t_e / (2 * math.pi * self.d_cutoff * t_e + 1)
        dx_hat = self.exponential_smoothing(a_d, dx, self.dx_prev)
        
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = 2 * math.pi * cutoff * t_e / (2 * math.pi * cutoff * t_e + 1)
        x_hat = self.exponential_smoothing(a, x, self.x_prev)
        
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        return x_hat

# ═══════════════════════════════════════════════════════════════════
# 3. GESTURE ENGINE (ERGONOMIC FIX)
# ═══════════════════════════════════════════════════════════════════
class Gesture(Enum):
    NEUTRAL = auto()     
    MOVE = auto()        
    CLICK_LEFT = auto()  
    CLICK_RIGHT = auto() 
    DRAG = auto()        
    SCREENSHOT = auto()  
    APP_SWITCH = auto()  

class GestureRecognizer:
    def __init__(self):
        self.lm = None

    def get_dist(self, p1, p2):
        x1, y1 = self.lm[p1].x, self.lm[p1].y
        x2, y2 = self.lm[p2].x, self.lm[p2].y
        return math.hypot(x2 - x1, y2 - y1)

    def is_finger_down(self, tip, pip):
        # Y increases downwards. Tip > PIP means finger is curled.
        # Threshold 0.0 ensures we don't get false positives on flat hands
        return self.lm[tip].y > self.lm[pip].y

    def detect(self, hand_landmarks):
        self.lm = hand_landmarks.landmark
        
        # Pinch Distances (Thumb vs Tips)
        dist_index = self.get_dist(4, 8)
        dist_mid   = self.get_dist(4, 12)
        dist_ring  = self.get_dist(4, 16)
        dist_pinky = self.get_dist(4, 20)

        # Finger States (Curled or not)
        index_up = not self.is_finger_down(8, 6)
        mid_up   = not self.is_finger_down(12, 10)
        ring_up  = not self.is_finger_down(16, 14)
        pinky_up = not self.is_finger_down(20, 18)

        # --- LOGIC PRIORITY ---

        # 1. DRAG (Fist)
        # Check: All fingers curled AND Thumb is close to fingers (Fist tightness)
        if not index_up and not mid_up and not ring_up and not pinky_up:
            return Gesture.DRAG

        # 2. APP SWITCH (3 Fingers Up)
        if index_up and mid_up and ring_up and not pinky_up:
            return Gesture.APP_SWITCH

        # 3. SCREENSHOT (Pinky Only)
        if pinky_up and not index_up and not mid_up and not ring_up:
            return Gesture.SCREENSHOT

        # 4. CLUTCH (Neutral/Reset)
        # If hand is open, stop moving.
        if index_up and mid_up and ring_up:
            return Gesture.NEUTRAL

        # --- CLICK LOGIC (FIXED) ---
        
        # Left Click: Index Pinch
        # FIX: Removed "mid_up" requirement. 
        # Instead, we ensure Middle Finger is NOT pinching. 
        # This allows natural hand relaxation without triggering "Fist".
        if dist_index < PINCH_THRESHOLD:
            # Safety: Ensure Middle Finger is not also pinching (which would be a fist/drag)
            if dist_mid > 0.06: 
                return Gesture.CLICK_LEFT
        
        # Right Click: Middle Pinch
        if dist_mid < PINCH_THRESHOLD:
            # Safety: Ensure Index is not pinching
            if dist_index > 0.06:
                return Gesture.CLICK_RIGHT

        # 5. MOVE (Pointing)
        # Standard tracking state
        if index_up:
            return Gesture.MOVE

        return Gesture.NEUTRAL

# ═══════════════════════════════════════════════════════════════════
# 4. MAIN CONTROLLER
# ═══════════════════════════════════════════════════════════════════
def run_hci(shm_name, shape, frame_ready_event, stop_event, mode_flag):
    print("[HCI] Process Started.")
    
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
        frame_buffer = np.ndarray(shape, dtype=np.uint8, buffer=shm.buf)
    except: return

    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
    recognizer = GestureRecognizer()

    filter_x = OneEuroFilter(min_cutoff=0.01, beta=SMOOTHING)
    filter_y = OneEuroFilter(min_cutoff=0.01, beta=SMOOTHING)

    last_click_time = 0
    last_action_time = 0
    is_dragging = False
    
    prev_raw_x, prev_raw_y = 0, 0
    curr_cursor_x, curr_cursor_y = pyautogui.position()
    first_frame = True
    
    cam_h, cam_w, _ = shape

    while not stop_event.is_set():
        if not frame_ready_event.wait(timeout=1.0): continue
        if mode_flag.value != 0: continue

        current_frame = frame_buffer.copy()
        rgb = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        
        if results.multi_hand_landmarks:
            hand_lm = results.multi_hand_landmarks[0]
            gesture = recognizer.detect(hand_lm)
            
            # Use Index Knuckle (5) for stability
            lm = hand_lm.landmark[5]
            raw_x, raw_y = lm.x * cam_w, lm.y * cam_h
            
            if first_frame:
                prev_raw_x, prev_raw_y = raw_x, raw_y
                first_frame = False

            now = time.time()

            # --- 1. MOVEMENT (Relative) ---
            if gesture == Gesture.MOVE or gesture == Gesture.DRAG:
                dx = (raw_x - prev_raw_x) * SENSITIVITY
                dy = (raw_y - prev_raw_y) * SENSITIVITY
                
                curr_cursor_x += dx
                curr_cursor_y += dy
                
                curr_cursor_x = max(0, min(curr_cursor_x, SCREEN_W - 1))
                curr_cursor_y = max(0, min(curr_cursor_y, SCREEN_H - 1))
                
                smooth_x = filter_x.filter(curr_cursor_x, now)
                smooth_y = filter_y.filter(curr_cursor_y, now)
                
                try: pyautogui.moveTo(smooth_x, smooth_y, _pause=False)
                except: pass
            
            # --- 2. ACTIONS ---
            if gesture == Gesture.CLICK_LEFT:
                if now - last_click_time > CLICK_COOLDOWN:
                    pyautogui.click()
                    last_click_time = now
                    print("[HCI] Left Click")
            
            elif gesture == Gesture.CLICK_RIGHT:
                if now - last_click_time > CLICK_COOLDOWN:
                    pyautogui.rightClick()
                    last_click_time = now
                    print("[HCI] Right Click")

            elif gesture == Gesture.DRAG:
                if not is_dragging:
                    pyautogui.mouseDown()
                    is_dragging = True
                    print("[HCI] Drag Start")
            
            # Drag Release
            if gesture != Gesture.DRAG and is_dragging:
                pyautogui.mouseUp()
                is_dragging = False
                print("[HCI] Drag Drop")

            elif gesture == Gesture.SCREENSHOT:
                if now - last_action_time > ACTION_COOLDOWN:
                    pyautogui.hotkey('command', 'shift', '3')
                    last_action_time = now
                    print("[HCI] Screenshot")

            elif gesture == Gesture.APP_SWITCH:
                if now - last_action_time > ACTION_COOLDOWN:
                    pyautogui.hotkey('command', 'tab')
                    last_action_time = now
                    print("[HCI] App Switch")

            prev_raw_x, prev_raw_y = raw_x, raw_y
            
    shm.close()
    print("[HCI] Stopped")