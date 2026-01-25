"""
Gesture Controller - Phase 2.2 Enhanced
Dual-Mode: Mouse Control + ISL Recognition
Platform: macOS Silicon (M1/M2/M3)
"""

import cv2
import mediapipe as mp
import pyautogui
import math
import platform
import os
import subprocess
import time
import numpy as np
import collections
from enum import IntEnum

# --- ML DEPENDENCIES (for Phase 2) ---
try:
    import tensorflow as tf
    Interpreter = tf.lite.Interpreter
except ImportError:
    from tflite_runtime.interpreter import Interpreter

# ═══════════════════════════════════════════════════════════════
# CONFIGURATION SECTION
# ═══════════════════════════════════════════════════════════════

# --- PHASE 1: MOUSE CONTROL SETTINGS ---
PRIMARY_HAND = "Left"           # "Left" = physical right hand (mirror mode)
SMOOTHING_FACTOR = 0.35         # 0.1 (heavy) to 0.5 (light) - OPTIMIZED
FRAME_REDUCTION = 80            # Active zone padding - ENLARGED
DEAD_ZONE_RADIUS = 5            # Ignore movements smaller than this (pixels)
CLICK_DEBOUNCE_TIME = 0.25      # Minimum time between clicks (seconds)
PINCH_THRESHOLD = 0.045         # Distance for pinch detection (0-1 scale)
GESTURE_HOLD_FRAMES = 2         # Frames to confirm gesture (was 4)

# --- PHASE 2: ISL RECOGNITION SETTINGS ---
CONFIDENCE_THRESHOLD = 0.70     # Minimum confidence to accept prediction
PREDICTION_STABILITY = 10       # Number of frames for consensus
DISPLAY_TIME = 3.0              # How long to show detected word (seconds)
PREDICTION_COOLDOWN = 1.5       # Wait time before next detection (seconds)
MODEL_PATH = "models/production/ISL_Model.tflite"
LABELS_PATH = "data/processed/labels.npy"

# --- SYSTEM SETTINGS ---
DEBUG_MODE = True               # Show FPS and debug info
IS_MACOS = platform.system() == "Darwin"

pyautogui.FAILSAFE = False
mp_drawing = mp.solutions.drawing_utils
mp_holistic = mp.solutions.holistic

# ═══════════════════════════════════════════════════════════════
# GESTURE RECOGNITION CLASSES
# ═══════════════════════════════════════════════════════════════

class Gest(IntEnum):
    """Gesture enumeration using binary encoding"""
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
    PINCH_MAJOR = 35      # Left Click
    PINCH_MINOR = 36      # Right Click

class HLabel(IntEnum):
    """Hand labels"""
    MINOR = 0
    MAJOR = 1

# ═══════════════════════════════════════════════════════════════
# HAND RECOGNITION CLASS
# ═══════════════════════════════════════════════════════════════

class HandRecog:
    """
    Converts MediaPipe landmarks to gesture classifications
    Enhanced with better pinch detection and faster response
    """
    
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
        """Calculate signed Euclidean distance between two landmarks"""
        if self.hand_result is None:
            return 0
        sign = -1
        if self.hand_result.landmark[point[0]].y < self.hand_result.landmark[point[1]].y:
            sign = 1
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        return math.sqrt(dist) * sign
    
    def get_dist(self, point):
        """Calculate Euclidean distance between two landmarks"""
        if self.hand_result is None:
            return 0
        dist = (self.hand_result.landmark[point[0]].x - self.hand_result.landmark[point[1]].x)**2
        dist += (self.hand_result.landmark[point[0]].y - self.hand_result.landmark[point[1]].y)**2
        return math.sqrt(dist)
    
    def get_dz(self, point):
        """Calculate Z-axis distance (depth)"""
        if self.hand_result is None:
            return 0
        return abs(self.hand_result.landmark[point[0]].z - self.hand_result.landmark[point[1]].z)
    
    def set_finger_state(self):
        """Determine which fingers are extended using geometric ratios"""
        if self.hand_result is None:
            return
        
        # Check each finger: Index(8), Middle(12), Ring(16), Pinky(20)
        points = [[8,5,0], [12,9,0], [16,13,0], [20,17,0]]
        self.finger = 0
        
        for idx, point in enumerate(points):
            dist = self.get_signed_dist(point[:2])
            dist2 = self.get_signed_dist(point[1:])
            
            try:
                ratio = round(dist/dist2, 1)
            except:
                ratio = round(dist/0.01, 1)
            
            self.finger = self.finger << 1
            if ratio > 0.5:
                self.finger = self.finger | 1
    
    def get_gesture(self):
        """
        Classify current hand pose into a gesture
        IMPROVED: Better pinch detection and faster response
        """
        if self.hand_result is None:
            return Gest.PALM
        
        current_gesture = Gest.PALM
        
        # ✅ IMPROVED: Distance-based pinch detection (more reliable)
        index_thumb_dist = self.get_dist([8, 4])  # Index tip to thumb tip
        middle_thumb_dist = self.get_dist([12, 4])  # Middle tip to thumb tip
        
        # Left Click: Index + Thumb pinch
        if index_thumb_dist < PINCH_THRESHOLD:
            current_gesture = Gest.PINCH_MAJOR
        
        # Right Click: Middle + Thumb pinch
        elif middle_thumb_dist < PINCH_THRESHOLD:
            current_gesture = Gest.PINCH_MINOR
        
        # V-Gesture (Peace sign) for movement
        elif Gest.FIRST2 == self.finger:
            point = [[8,12], [5,9]]
            dist1 = self.get_dist(point[0])
            dist2 = self.get_dist(point[1])
            ratio = dist1/dist2 if dist2 != 0 else 0
            
            if ratio > 1.7:
                current_gesture = Gest.V_GEST
            else:
                if self.get_dz([8,12]) < 0.1:
                    current_gesture = Gest.TWO_FINGER_CLOSED
                else:
                    current_gesture = Gest.MID
        
        # Fist for drag
        elif self.finger == Gest.FIST:
            current_gesture = Gest.FIST
        
        # Default to finger state
        else:
            current_gesture = self.finger
        
        # ✅ IMPROVED: Faster gesture confirmation (2 frames instead of 4)
        if current_gesture == self.prev_gesture:
            self.frame_count += 1
        else:
            self.frame_count = 0
        
        self.prev_gesture = current_gesture
        
        if self.frame_count > GESTURE_HOLD_FRAMES:
            self.ori_gesture = current_gesture
        
        return self.ori_gesture

# ═══════════════════════════════════════════════════════════════
# CONTROLLER CLASS (Mouse & System Control)
# ═══════════════════════════════════════════════════════════════

class Controller:
    """
    Handles OS-level interactions: mouse, keyboard, system controls
    ENHANCED: Dead zone filtering, better smoothing, click debouncing
    """
    
    # State variables
    flag = False                # True when in movement mode (V-gesture)
    grabflag = False           # True when dragging (fist)
    pinchmajorflag = False     # True when left click held
    pinchminorflag = False     # True when right click held
    prev_hand = None           # Previous hand position for smoothing
    dead_zone_center = None    # Center of dead zone for jitter reduction
    last_click_time = 0        # Last click timestamp
    
    # Pinch control (for volume/brightness)
    pinchmajorflag_system = False
    pinchminorflag_system = False
    pinchstartxcoord = None
    pinchstartycoord = None
    pinchdirectionflag = None
    prevpinchlv = 0
    pinchlv = 0
    framecount = 0
    pinch_threshold = 0.3
    
    @staticmethod
    def apply_dead_zone(x, y):
        """
        Prevents micro-jitter by ignoring small movements
        Creates a "dead zone" around the current position
        """
        if Controller.dead_zone_center is None:
            Controller.dead_zone_center = (x, y)
            return x, y
        
        dx = x - Controller.dead_zone_center[0]
        dy = y - Controller.dead_zone_center[1]
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist < DEAD_ZONE_RADIUS:
            # Movement too small, stay at center
            return Controller.dead_zone_center
        else:
            # Significant movement, update center
            Controller.dead_zone_center = (x, y)
            return x, y
    
    @staticmethod
    def get_position(hand_result):
        """
        Convert hand landmark to screen coordinates
        ENHANCED: Dead zone + exponential smoothing + acceleration curve
        """
        point = 9  # Middle of hand (wrist base)
        raw_x = hand_result.landmark[point].x
        raw_y = hand_result.landmark[point].y
        
        # Get dimensions
        wCam, hCam = int(GestureController.CAM_WIDTH), int(GestureController.CAM_HEIGHT)
        wScr, hScr = pyautogui.size()
        
        # Convert normalized coords to camera pixels
        x1 = raw_x * wCam
        y1 = raw_y * hCam
        
        # ✅ STEP 1: Amplification (map reduced frame to full screen)
        x3 = np.interp(x1, (FRAME_REDUCTION, wCam - FRAME_REDUCTION), (0, wScr))
        y3 = np.interp(y1, (FRAME_REDUCTION, hCam - FRAME_REDUCTION), (0, hScr))
        
        # ✅ STEP 2: Apply dead zone (removes jitter)
        x3, y3 = Controller.apply_dead_zone(int(x3), int(y3))
        
        # ✅ STEP 3: Exponential smoothing (prevents jerky movement)
        if Controller.prev_hand is None:
            Controller.prev_hand = [x3, y3]
            return (int(x3), int(y3))
        
        curr_x = Controller.prev_hand[0] + (x3 - Controller.prev_hand[0]) * SMOOTHING_FACTOR
        curr_y = Controller.prev_hand[1] + (y3 - Controller.prev_hand[1]) * SMOOTHING_FACTOR
        
        Controller.prev_hand = [curr_x, curr_y]
        return (int(curr_x), int(curr_y))
    
    @staticmethod
    def handle_controls(gesture, hand_result):
        """
        Map gestures to OS actions
        IMPROVED: Better state management and click debouncing
        """
        x, y = None, None
        if gesture != Gest.PALM:
            x, y = Controller.get_position(hand_result)
        
        # ═══ STATE MANAGEMENT ═══
        
        # Release drag if not in fist
        if gesture != Gest.FIST and Controller.grabflag:
            Controller.grabflag = False
            pyautogui.mouseUp(button="left")
            if DEBUG_MODE:
                print("[MOUSE] Drag released")
        
        # Release clicks if not pinching
        if gesture != Gest.PINCH_MAJOR and Controller.pinchmajorflag:
            Controller.pinchmajorflag = False
        
        if gesture != Gest.PINCH_MINOR and Controller.pinchminorflag:
            Controller.pinchminorflag = False
        
        # ═══ GESTURE ACTIONS ═══
        
        # 1. MOVE: V-Gesture (Peace sign ✌️)
        if gesture == Gest.V_GEST:
            Controller.flag = True
            pyautogui.moveTo(x, y, duration=0)
            Controller.dead_zone_center = None  # Reset dead zone when moving
        
        # 2. LEFT CLICK: Index + Thumb pinch
        elif gesture == Gest.PINCH_MAJOR:
            if not Controller.pinchmajorflag:
                current_time = time.time()
                # Debounce: prevent accidental double-clicks
                if current_time - Controller.last_click_time > CLICK_DEBOUNCE_TIME:
                    Controller.pinchmajorflag = True
                    pyautogui.click(button='left')
                    Controller.last_click_time = current_time
                    if DEBUG_MODE:
                        print("[MOUSE] Left Click")
        
        # 3. RIGHT CLICK: Middle + Thumb pinch
        elif gesture == Gest.PINCH_MINOR:
            if not Controller.pinchminorflag:
                current_time = time.time()
                if current_time - Controller.last_click_time > CLICK_DEBOUNCE_TIME:
                    Controller.pinchminorflag = True
                    pyautogui.click(button='right')
                    Controller.last_click_time = current_time
                    if DEBUG_MODE:
                        print("[MOUSE] Right Click")
        
        # 4. DRAG: Fist (closed hand)
        elif gesture == Gest.FIST:
            if not Controller.grabflag:
                Controller.grabflag = True
                pyautogui.mouseDown(button="left")
                if DEBUG_MODE:
                    print("[MOUSE] Drag started")
            pyautogui.moveTo(x, y, duration=0)
        
        # 5. DOUBLE CLICK: Two fingers closed
        elif gesture == Gest.TWO_FINGER_CLOSED and Controller.flag:
            pyautogui.doubleClick()
            Controller.flag = False
            if DEBUG_MODE:
                print("[MOUSE] Double Click")
        
        # IDLE: Palm open (no action)
        elif gesture == Gest.PALM:
            Controller.flag = False

# ═══════════════════════════════════════════════════════════════
# ISL ENGINE (Phase 2 - Sign Language Recognition)
# ═══════════════════════════════════════════════════════════════

class ISLEngine:
    """
    TensorFlow Lite inference engine for ISL recognition
    Loads model and performs predictions on landmark sequences
    """
    
    def __init__(self, model_path, labels_path):
        print(f"[ISL] Loading model from {model_path}...")
        self.is_loaded = False
        
        try:
            # Load TFLite model
            self.interpreter = Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            # Load label mapping
            self.labels_map = np.load(labels_path, allow_pickle=True).item()
            self.id_to_label = {v: k for k, v in self.labels_map.items()}
            
            print(f"[ISL] ✅ Model loaded: {len(self.labels_map)} classes")
            self.is_loaded = True
            
        except Exception as e:
            print(f"[ISL] ❌ ERROR: Could not load model - {e}")
            print("[ISL] Sign language mode will be disabled")
    
    def extract_features(self, results):
        """
        Extract 198 keypoints from MediaPipe Holistic results
        Format: [Pose(24*3), Left_Hand(21*3), Right_Hand(21*3)] = 198
        """
        # Pose (upper body only, 24 landmarks)
        if results.pose_landmarks:
            pose = np.array([[res.x, res.y, res.z] 
                           for res in results.pose_landmarks.landmark[:24]]).flatten()
        else:
            pose = np.zeros(24 * 3)
        
        # Left hand (21 landmarks)
        if results.left_hand_landmarks:
            lh = np.array([[res.x, res.y, res.z] 
                         for res in results.left_hand_landmarks.landmark]).flatten()
        else:
            lh = np.zeros(21 * 3)
        
        # Right hand (21 landmarks)
        if results.right_hand_landmarks:
            rh = np.array([[res.x, res.y, res.z] 
                         for res in results.right_hand_landmarks.landmark]).flatten()
        else:
            rh = np.zeros(21 * 3)
        
        return np.concatenate([pose, lh, rh])
    
    def predict(self, sequence_buffer):
        """
        Run inference on 30-frame sequence
        Returns: (predicted_word, confidence)
        """
        if not self.is_loaded:
            return "Model Error", 0.0
        
        try:
            # Prepare input (batch_size=1, frames=30, features=198)
            input_data = np.expand_dims(sequence_buffer, axis=0).astype(np.float32)
            
            # Run inference
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            self.interpreter.invoke()
            output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
            
            # Get prediction
            prediction_id = np.argmax(output_data)
            confidence = np.max(output_data)
            predicted_word = self.id_to_label.get(prediction_id, "Unknown")
            
            return predicted_word, confidence
            
        except Exception as e:
            print(f"[ISL] Prediction error: {e}")
            return "Error", 0.0

# ═══════════════════════════════════════════════════════════════
# MAIN GESTURE CONTROLLER
# ═══════════════════════════════════════════════════════════════

class GestureController:
    """
    Main controller - manages camera, modes, and UI
    Dual Mode: Mouse Control (Phase 1) + ISL Recognition (Phase 2)
    """
    
    # Class variables
    gc_mode = 1
    cap = None
    is_signing_mode = False
    sequence_buffer = []
    CAM_WIDTH = 0
    CAM_HEIGHT = 0
    
    # ISL prediction tracking
    last_predictions = collections.deque(maxlen=PREDICTION_STABILITY)
    current_display_word = ""
    display_timer = 0
    last_detection_time = 0
    
    # FPS tracking
    fps = 0
    frame_count = 0
    fps_start_time = 0
    
    def __init__(self):
        print("[INIT] Initializing Gesture Controller...")
        print(f"[INIT] Platform: {'macOS' if IS_MACOS else 'Other'}")
        
        # Initialize sequence buffer
        GestureController.sequence_buffer = collections.deque(maxlen=30)
        
        # Load ISL model (Phase 2)
        if os.path.exists(MODEL_PATH) and os.path.exists(LABELS_PATH):
            self.isl_engine = ISLEngine(MODEL_PATH, LABELS_PATH)
        else:
            print("[INIT] ⚠️  ISL model not found - Sign mode will be disabled")
            print(f"[INIT] Expected: {MODEL_PATH}")
            self.isl_engine = None
        
        # Initialize camera
        GestureController.cap = cv2.VideoCapture(0)
        if not GestureController.cap.isOpened():
            print("[INIT] Camera 0 failed, trying camera 1...")
            GestureController.cap = cv2.VideoCapture(1)
        
        if not GestureController.cap.isOpened():
            print("[INIT] ❌ ERROR: Could not open camera!")
            GestureController.gc_mode = 0
            return
        
        # Set resolution for better performance
        GestureController.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        GestureController.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        GestureController.CAM_WIDTH = GestureController.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        GestureController.CAM_HEIGHT = GestureController.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        
        print(f"[INIT] ✅ Camera initialized: {int(GestureController.CAM_WIDTH)}x{int(GestureController.CAM_HEIGHT)}")
        print(f"[INIT] Primary hand: {PRIMARY_HAND}")
        print("[INIT] Ready! Press 'Q' to toggle modes, 'ESC' to exit")
    
    def toggle_mode(self):
        """Switch between Mouse Control and Sign Language modes"""
        if self.isl_engine is None or not self.isl_engine.is_loaded:
            print("[MODE] ⚠️  Sign language mode unavailable (model not loaded)")
            return
        
        GestureController.is_signing_mode = not GestureController.is_signing_mode
        mode_name = "SIGN LANGUAGE" if GestureController.is_signing_mode else "MOUSE CONTROL"
        print(f"[MODE] Switched to: {mode_name}")
        
        # Reset states
        Controller.flag = False
        Controller.grabflag = False
        Controller.prev_hand = None
        GestureController.sequence_buffer.clear()
        GestureController.last_predictions.clear()
    
    def draw_ui(self, image):
        """Draw UI overlays based on current mode"""
        h, w = image.shape[:2]
        
        if not GestureController.is_signing_mode:
            # ═══ MOUSE MODE UI ═══
            
            # Draw active zone box
            cv2.rectangle(
                image, 
                (FRAME_REDUCTION, FRAME_REDUCTION), 
                (w - FRAME_REDUCTION, h - FRAME_REDUCTION),
                (255, 0, 255), 2
            )
            
            # Mode indicator
            cv2.rectangle(image, (0, 0), (200, 40), (50, 50, 50), -1)
            cv2.putText(
                image, "MOUSE MODE", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
            )
            
            # Instructions
            cv2.putText(
                image, "V: Move | Pinch: Click | Fist: Drag", (10, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1
            )
            
        else:
            # ═══ SIGN MODE UI ═══
            
            # Header bar
            cv2.rectangle(image, (0, 0), (w, 50), (0, 0, 0), -1)
            cv2.putText(
                image, "SIGN LANGUAGE MODE", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2
            )
            
            # Show detected word with timer
            current_time = time.time()
            if current_time - self.display_timer < DISPLAY_TIME:
                remaining = int(DISPLAY_TIME - (current_time - self.display_timer))
                cv2.rectangle(image, (0, h - 80), (w, h), (0, 0, 0), -1)
                cv2.putText(
                    image, f"{self.current_display_word} ({remaining}s)", 
                    (20, h - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3
                )
            else:
                # Show "Ready" when cooldown is done
                can_predict = (current_time - self.last_detection_time) > PREDICTION_COOLDOWN
                if can_predict:
                    cv2.putText(
                        image, "Ready...", (20, h - 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2
                    )
        
        # ═══ COMMON UI ═══
        
        # FPS counter
        if DEBUG_MODE:
            cv2.putText(
                image, f"FPS: {int(self.fps)}", (w - 100, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2
            )
        
        # Mode toggle hint
        cv2.putText(
            image, "Q: Toggle Mode | ESC: Exit", (10, h - 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1
        )
        
        return image
    
    def update_fps(self):
        """Calculate and update FPS"""
        self.frame_count += 1
        if self.frame_count % 30 == 0:
            current_time = time.time()
            self.fps = 30 / (current_time - self.fps_start_time)
            self.fps_start_time = current_time
    
    def start(self):
        """Main loop - handles camera feed and gesture processing"""
        if GestureController.gc_mode == 0:
            print("[ERROR] Controller not initialized properly")
            return
        
        print("[START] Starting main loop...")
        self.fps_start_time = time.time()
        
        handmajor = HandRecog(HLabel.MAJOR)
        
        with mp_holistic.Holistic(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        ) as holistic:
            
            while GestureController.cap.isOpened():
                success, image = GestureController.cap.read()
                if not success:
                    continue
                
                # Mirror the image
                image = cv2.flip(image, 1)
                
                # Handle keyboard input
                key = cv2.waitKey(5) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    self.toggle_mode()
                elif key == 27:  # ESC
                    print("[EXIT] User requested exit")
                    break
                
                # Process with MediaPipe
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image_rgb.flags.writeable = False
                results = holistic.process(image_rgb)
                image_rgb.flags.writeable = True
                
                # ═══════════════════════════════════════════════
                # MODE 1: MOUSE CONTROL
                # ═══════════════════════════════════════════════
                
                if not GestureController.is_signing_mode:
                    
                    # Get the primary hand
                    mouse_hand = (results.left_hand_landmarks 
                                if PRIMARY_HAND == "Left" 
                                else results.right_hand_landmarks)
                    
                    if mouse_hand:
                        # Update hand state
                        handmajor.update_hand_result(mouse_hand)
                        handmajor.set_finger_state()
                        gest_name = handmajor.get_gesture()
                        
                        # Execute control
                        Controller.handle_controls(gest_name, handmajor.hand_result)
                        
                        # Draw hand landmarks
                        mp_drawing.draw_landmarks(
                            image, mouse_hand, 
                            mp_holistic.HAND_CONNECTIONS
                        )
                
                # ═══════════════════════════════════════════════
                # MODE 2: SIGN LANGUAGE RECOGNITION
                # ═══════════════════════════════════════════════
                
                else:
                    if self.isl_engine is not None and self.isl_engine.is_loaded:
                        
                        # Draw full skeleton
                        mp_drawing.draw_landmarks(
                            image, results.pose_landmarks, 
                            mp_holistic.POSE_CONNECTIONS
                        )
                        mp_drawing.draw_landmarks(
                            image, results.left_hand_landmarks, 
                            mp_holistic.HAND_CONNECTIONS
                        )
                        mp_drawing.draw_landmarks(
                            image, results.right_hand_landmarks, 
                            mp_holistic.HAND_CONNECTIONS
                        )
                        
                        # Check if we can predict (cooldown expired)
                        current_time = time.time()
                        can_predict = (current_time - self.last_detection_time) > PREDICTION_COOLDOWN
                        
                        if results.pose_landmarks and can_predict:
                            # Extract features and add to buffer
                            keypoints = self.isl_engine.extract_features(results)
                            GestureController.sequence_buffer.append(keypoints)
                            
                            # When buffer is full, predict
                            if len(GestureController.sequence_buffer) == 30:
                                word, conf = self.isl_engine.predict(
                                    GestureController.sequence_buffer
                                )
                                
                                # Stability check
                                if conf > CONFIDENCE_THRESHOLD:
                                    self.last_predictions.append(word)
                                    
                                    # Check for consensus (80% agreement)
                                    if len(self.last_predictions) == PREDICTION_STABILITY:
                                        from collections import Counter
                                        word_counts = Counter(self.last_predictions)
                                        most_common_word, count = word_counts.most_common(1)[0]
                                        
                                        # Need 80% agreement
                                        agreement_threshold = int(PREDICTION_STABILITY * 0.8)
                                        if count >= agreement_threshold:
                                            if self.current_display_word != most_common_word:
                                                self.current_display_word = most_common_word
                                                self.display_timer = current_time
                                                self.last_detection_time = current_time
                                                print(f"[DETECTED] {most_common_word} (conf: {conf:.2f})")
                                                
                                                # Clear buffer to prevent re-detection
                                                self.last_predictions.clear()
                
                # Update FPS
                self.update_fps()
                
                # Draw UI overlays
                image = self.draw_ui(image)
                
                # Display
                cv2.imshow('Gesture Controller', image)
        
        # Cleanup
        print("[STOP] Releasing resources...")
        GestureController.cap.release()
        cv2.destroyAllWindows()
        print("[STOP] Gesture Controller stopped")

# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  GESTURE CONTROLLER - Phase 1 (Mouse Control)")
    print("=" * 60)
    
    gc = GestureController()
    
    if gc.gc_mode == 1:
        gc.start()
    else:
        print("[FATAL] Initialization failed. Check camera permissions.")