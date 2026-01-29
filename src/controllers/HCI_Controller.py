import mediapipe as mp
import pyautogui
import numpy as np
import time
import math
import cv2
from multiprocessing import shared_memory
from enum import Enum, auto

# ═══════════════════════════════════════════════════════════════════
# 1. CONFIGURATION
# ═══════════════════════════════════════════════════════════════════
pyautogui.FAILSAFE = False
SCREEN_W, SCREEN_H = pyautogui.size()

# Sensitivity
FRAME_REDUCTION = 100    # Pixels from camera edge to ignore (The "Comfort Zone")
CLICK_THRESHOLD = 0.04   # How close thumb/finger need to be to click
SMOOTHING = 5.0          # OneEuroFilter Beta (Higher = Less Lag, Lower = Smoother)

# ═══════════════════════════════════════════════════════════════════
# 2. HELPER: OneEuroFilter (Embedded for Stability)
# ═══════════════════════════════════════════════════════════════════
class OneEuroFilter:
    def __init__(self, min_cutoff=0.1, beta=4.0, d_cutoff=1.0):
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
        
        # Jitter reduction
        dx = (x - self.x_prev) / t_e
        a_d = 2 * math.pi * self.d_cutoff * t_e / (2 * math.pi * self.d_cutoff * t_e + 1)
        dx_hat = self.exponential_smoothing(a_d, dx, self.dx_prev)
        
        # Lag reduction
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)
        a = 2 * math.pi * cutoff * t_e / (2 * math.pi * cutoff * t_e + 1)
        x_hat = self.exponential_smoothing(a, x, self.x_prev)
        
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t
        return x_hat

# ═══════════════════════════════════════════════════════════════════
# 3. GESTURE ENGINE (New & Robust)
# ═══════════════════════════════════════════════════════════════════
class Gesture(Enum):
    NEUTRAL = auto()
    MOVE = auto()        # Index Up OR V-Sign
    CLICK_LEFT = auto()  # Pinch Index
    CLICK_RIGHT = auto() # Pinch Middle
    DRAG = auto()        # Fist
    SCREENSHOT = auto()  # Pinky Only
    APP_SWITCH = auto()  # 3 Fingers

class GestureRecognizer:
    def __init__(self):
        self.lm = None
    
    def calculate_distance(self, p1_idx, p2_idx):
        x1, y1 = self.lm[p1_idx].x, self.lm[p1_idx].y
        x2, y2 = self.lm[p2_idx].x, self.lm[p2_idx].y
        return math.hypot(x2 - x1, y2 - y1)

    def is_finger_up(self, tip_idx, pip_idx):
        # Y coordinates increase downwards
        return self.lm[tip_idx].y < self.lm[pip_idx].y

    def detect(self, hand_landmarks):
        self.lm = hand_landmarks.landmark
        
        # 1. Check which fingers are up
        thumb_out = self.lm[4].x < self.lm[3].x # Rough check for right hand
        index_up = self.is_finger_up(8, 6)
        mid_up   = self.is_finger_up(12, 10)
        ring_up  = self.is_finger_up(16, 14)
        pinky_up = self.is_finger_up(20, 18)

        # 2. Check Pinches (Distance between Tip and Thumb)
        pinch_index = self.calculate_distance(8, 4)
        pinch_mid   = self.calculate_distance(12, 4)

        # --- LOGIC TREE ---

        # A. DRAG (Fist: All fingers down)
        if not (index_up or mid_up or ring_up or pinky_up):
            return Gesture.DRAG

        # B. CLICKS (Priority over movement)
        if pinch_index < CLICK_THRESHOLD:
            return Gesture.CLICK_LEFT
        
        if pinch_mid < CLICK_THRESHOLD:
            return Gesture.CLICK_RIGHT

        # C. SYSTEM SHORTCUTS
        # Pinky Only = Screenshot
        if pinky_up and not (index_up or mid_up or ring_up):
            return Gesture.SCREENSHOT
        
        # 3 Fingers (No Pinky, No Index Pinch) = App Switch
        if index_up and mid_up and ring_up and not pinky_up:
            return Gesture.APP_SWITCH

        # D. MOVEMENT (Default if Index is up)
        if index_up:
            return Gesture.MOVE

        return Gesture.NEUTRAL

# ═══════════════════════════════════════════════════════════════════
# 4. MAIN CONTROLLER
# ═══════════════════════════════════════════════════════════════════
def run_hci(shm_name, shape, frame_ready_event, stop_event, mode_flag):
    print("[HCI] Process Started.")
    
    # Shared Memory
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
        frame_buffer = np.ndarray(shape, dtype=np.uint8, buffer=shm.buf)
    except: return

    # MediaPipe
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)

    # Objects
    recognizer = GestureRecognizer()
    filter_x = OneEuroFilter(min_cutoff=0.1, beta=SMOOTHING)
    filter_y = OneEuroFilter(min_cutoff=0.1, beta=SMOOTHING)

    # State
    last_click_time = 0
    is_dragging = False
    trigger_lock = False  # Prevents spamming screenshot/app switch
    cam_h, cam_w, _ = shape

    while not stop_event.is_set():
        if not frame_ready_event.wait(timeout=1.0): continue
        if mode_flag.value != 0: continue # MOUSE MODE ONLY

        # Vision Pipeline
        current_frame = frame_buffer.copy()
        rgb = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        
        # Visual Debug Text
        debug_text = "Searching..."

        if results.multi_hand_landmarks:
            hand_lm = results.multi_hand_landmarks[0]
            
            # 1. Detect Gesture
            gesture = recognizer.detect(hand_lm)
            debug_text = gesture.name
            
            # 2. Reset Locks if Neutral
            if gesture == Gesture.NEUTRAL or gesture == Gesture.MOVE:
                trigger_lock = False
                if is_dragging:
                    pyautogui.mouseUp()
                    is_dragging = False

            # 3. Handle Actions
            now = time.time()

            if gesture == Gesture.CLICK_LEFT:
                if now - last_click_time > 0.3: # Debounce
                    pyautogui.click()
                    last_click_time = now

            elif gesture == Gesture.CLICK_RIGHT:
                 if now - last_click_time > 0.5:
                    pyautogui.rightClick()
                    last_click_time = now

            elif gesture == Gesture.DRAG:
                if not is_dragging:
                    pyautogui.mouseDown()
                    is_dragging = True
            
            elif gesture == Gesture.SCREENSHOT:
                if not trigger_lock:
                    pyautogui.hotkey('command', 'shift', '3') # Mac Screenshot
                    trigger_lock = True
            
            elif gesture == Gesture.APP_SWITCH:
                if not trigger_lock:
                    pyautogui.hotkey('command', 'tab')
                    trigger_lock = True

            # 4. Handle Movement (Only if MOVE or DRAG)
            if gesture == Gesture.MOVE or gesture == Gesture.DRAG:
                # Track Index Finger Tip
                tip = hand_lm.landmark[8]
                
                # Raw
                raw_x, raw_y = int(tip.x * cam_w), int(tip.y * cam_h)

                # Absolute Mapping (Comfort Zone)
                target_x = np.interp(raw_x, (FRAME_REDUCTION, cam_w - FRAME_REDUCTION), (0, SCREEN_W))
                target_y = np.interp(raw_y, (FRAME_REDUCTION, cam_h - FRAME_REDUCTION), (0, SCREEN_H))

                # Clamp
                target_x = np.clip(target_x, 0, SCREEN_W - 2)
                target_y = np.clip(target_y, 0, SCREEN_H - 2)

                # Filter
                smooth_x = filter_x.filter(target_x, now)
                smooth_y = filter_y.filter(target_y, now)

                try: pyautogui.moveTo(smooth_x, smooth_y, _pause=False)
                except: pass

        # Draw Debug Text onto the Frame (Directly into shared memory for App to see)
        # Note: We draw on 'current_frame' but we need to write it back? 
        # Actually, App.py reads shared memory to display. 
        # Since we are a child process reading the same memory, writing back might tear.
        # Ideally, we send the status to App.py via Queue, but for now, check the terminal.
        # OR: We just print to console for safety.
        # print(f"[HCI] {debug_text}") 

    shm.close()
    print("[HCI] Stopped")