# import mediapipe as mp
# import numpy as np
# import time
# from multiprocessing import shared_memory
# import collections
# import cv2
# import os
# import sys
# import traceback

# # --- 1. EMBEDDED NORMALIZATION ---
# def normalize_features(results):
#     if results.pose_landmarks:
#         pose = np.array([[res.x, res.y, res.z] for res in results.pose_landmarks.landmark[:25]])
#     else:
#         pose = np.zeros((25, 3))
    
#     if results.left_hand_landmarks:
#         lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark])
#     else:
#         lh = np.zeros((21, 3))

#     if results.right_hand_landmarks:
#         rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark])
#     else:
#         rh = np.zeros((21, 3))
    
#     left_shoulder = pose[11]
#     right_shoulder = pose[12]
#     chest_center = (left_shoulder + right_shoulder) / 2.0
#     shoulder_width = np.linalg.norm(left_shoulder - right_shoulder)
#     if shoulder_width < 0.01: shoulder_width = 1.0

#     def standardize(landmarks):
#         return (landmarks - chest_center) / shoulder_width

#     return np.concatenate([
#         standardize(pose).flatten(), 
#         standardize(lh).flatten(), 
#         standardize(rh).flatten()
#     ])

# # --- 2. TFLITE SETUP ---
# try:
#     import tensorflow as tf
#     Interpreter = tf.lite.Interpreter
# except:
#     from tflite_runtime.interpreter import Interpreter

# def run_isl(shm_name, shape, frame_ready_event, stop_event, result_queue, mode_flag):
#     print("\033[96m[ISL] Process Launching...\033[0m")
    
#     try:
#         # PATH RESOLUTION
#         current_dir = os.path.dirname(os.path.abspath(__file__))
#         project_root = os.path.abspath(os.path.join(current_dir, '../../'))
#         MODEL_PATH = os.path.join(project_root, "models", "ISL_Model.tflite")
#         LABEL_PATH = os.path.join(project_root, "data", "processed", "labels.npy")
#         # BRIDGE FILE (For GUI Communication)
#         BRIDGE_PATH = os.path.join(project_root, "data", "isl_live.txt")

#         # SHARED MEMORY
#         shm = shared_memory.SharedMemory(name=shm_name)
#         frame_buffer = np.ndarray(shape, dtype=np.uint8, buffer=shm.buf)

#         # MODEL LOAD
#         mp_holistic = mp.solutions.holistic
#         holistic = mp_holistic.Holistic(
#             min_detection_confidence=0.5, 
#             min_tracking_confidence=0.5,
#             model_complexity=1
#         )

#         interpreter = Interpreter(model_path=MODEL_PATH)
#         interpreter.allocate_tensors()
#         input_details = interpreter.get_input_details()
#         output_details = interpreter.get_output_details()
        
#         labels_map = np.load(LABEL_PATH, allow_pickle=True).item()
#         id_to_label = {v: k for k, v in labels_map.items()}
#         print(f"\033[92m[ISL] System Ready. Vocab: {len(id_to_label)}\033[0m")

#         # LOGIC VARS
#         sequence = collections.deque(maxlen=30)
#         prediction_buffer = collections.deque(maxlen=5) 
        
#         # --- FILTERS ---
#         CONFIDENCE_THRESHOLD = 0.85  # Stricter!
#         last_word_time = 0
#         COOLDOWN_SECONDS = 2.0       # Don't repeat word for 2s
#         last_detected_word = ""

#         while not stop_event.is_set():
#             if not frame_ready_event.wait(timeout=1.0): continue
#             if mode_flag.value != 1:
#                 sequence.clear()
#                 prediction_buffer.clear()
#                 continue

#             current_frame = frame_buffer.copy()
#             image = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
#             results = holistic.process(image)
            
#             if results.pose_landmarks:
#                 keypoints = normalize_features(results)
#                 sequence.append(keypoints)
                
#                 if len(sequence) == 30:
#                     input_data = np.expand_dims(sequence, axis=0).astype(np.float32)
#                     interpreter.set_tensor(input_details[0]['index'], input_data)
#                     interpreter.invoke()
#                     output = interpreter.get_tensor(output_details[0]['index'])
                    
#                     pred_id = np.argmax(output)
#                     confidence = np.max(output)
#                     word = id_to_label.get(pred_id, "Unknown")

#                     if confidence > CONFIDENCE_THRESHOLD: 
#                         prediction_buffer.append(pred_id)
                        
#                         if prediction_buffer.count(pred_id) == 5:
#                             # --- DEBOUNCE LOGIC ---
#                             current_time = time.time()
#                             is_new_word = word != last_detected_word
#                             is_cooldown_over = (current_time - last_word_time) > COOLDOWN_SECONDS
                            
#                             if word.lower() != "idle" and word != "Unknown":
#                                 if is_new_word or is_cooldown_over:
#                                     # 1. Console Output
#                                     print(f"\033[92m[ISL] >>> RECOGNIZED: {word.upper()} ({confidence:.2f})\033[0m")
                                    
#                                     # 2. Send to Queue (for Vision Backend)
#                                     if result_queue.empty(): result_queue.put(word)
                                    
#                                     # 3. Write to Bridge File (for GUI)
#                                     try:
#                                         with open(BRIDGE_PATH, "w") as f:
#                                             f.write(word)
#                                     except: pass

#                                     last_word_time = current_time
#                                     last_detected_word = word
#                                     prediction_buffer.clear()
#                     else:
#                         prediction_buffer.append(-1)

#     except Exception as e:
#         traceback.print_exc()
#     finally:
#         try: shm.close()
#         except: pass
#         print("[ISL] Stopped")

#* phase 3

"""
═══════════════════════════════════════════════════════════════════════════════
ISL_Controller.py - PRODUCTION GRADE CSLR
Robust Continuous Sign Language Recognition with Temporal Intelligence

Author: Jarvis-EcoSign Team
Date: April 2026
Architecture: Multiprocessing (Shared Memory + Queue Communication)
═══════════════════════════════════════════════════════════════════════════════

CRITICAL IMPROVEMENTS (FINAL VERSION):
✅ Leaky Prediction Buffer (prevents aggressive clearing)
✅ Post-Word Stability Window (prevents premature finalization)
✅ Word Hold Protection (blocks finalization during confirmation)
✅ Improved Prediction Smoothing (natural decay instead of clearing)
✅ Dynamic Timeout with Extension Grace
✅ Aggressive Idle Commit
✅ Enhanced Mini Grammar Engine
✅ Real-time Buffer Feedback
"""

import mediapipe as mp
import numpy as np
import time
from multiprocessing import shared_memory
import collections
import cv2
import os
import tensorflow as tf

# ═══════════════════════════════════════════════════════════════════════════
# FEATURE NORMALIZATION (Shoulder-Invariant)
# ═══════════════════════════════════════════════════════════════════════════
def normalize_features(results):
    """
    Normalize MediaPipe Holistic landmarks to be scale and position invariant.
    Uses shoulder width as the scale factor and chest center as the origin.
    
    This ensures the LSTM model receives consistent input regardless of:
    - Distance from camera
    - User height/build
    - Camera positioning
    
    Args:
        results: MediaPipe Holistic results object
        
    Returns:
        np.ndarray: Flattened normalized features (201 values)
    """
    # Extract pose landmarks (first 25 only - upper body)
    if results.pose_landmarks:
        pose = np.array([[res.x, res.y, res.z] for res in results.pose_landmarks.landmark[:25]])
    else: 
        pose = np.zeros((25, 3))
    
    # Extract hand landmarks
    if results.left_hand_landmarks:
        lh = np.array([[res.x, res.y, res.z] for res in results.left_hand_landmarks.landmark])
    else: 
        lh = np.zeros((21, 3))

    if results.right_hand_landmarks:
        rh = np.array([[res.x, res.y, res.z] for res in results.right_hand_landmarks.landmark])
    else: 
        rh = np.zeros((21, 3))
    
    # Calculate normalization anchor and scale
    left_shoulder = pose[11]
    right_shoulder = pose[12]
    chest_center = (left_shoulder + right_shoulder) / 2.0
    shoulder_width = np.linalg.norm(left_shoulder - right_shoulder)
    
    # Prevent division by zero
    if shoulder_width < 0.01: 
        shoulder_width = 1.0

    def standardize(landmarks): 
        """Center and scale landmarks"""
        return (landmarks - chest_center) / shoulder_width

    # Flatten and concatenate: 25*3 + 21*3 + 21*3 = 201 features
    return np.concatenate([
        standardize(pose).flatten(), 
        standardize(lh).flatten(), 
        standardize(rh).flatten()
    ])


# ═══════════════════════════════════════════════════════════════════════════
# TFLITE INTERPRETER SETUP
# ═══════════════════════════════════════════════════════════════════════════
try: 
    Interpreter = tf.lite.Interpreter
except: 
    from tflite_runtime.interpreter import Interpreter


# ═══════════════════════════════════════════════════════════════════════════
# LINGUISTIC INTELLIGENCE LAYER
# ═══════════════════════════════════════════════════════════════════════════

def normalize_gloss_order(words):
    """
    Sort glosses by grammatical priority for better fallback readability.
    
    ISL typically follows SOV (Subject-Object-Verb) order, but can be flexible.
    This provides a reasonable canonical ordering for unmatched sequences.
    
    Priority hierarchy:
    0. Subject pronouns (I, YOU)
    1. Object pronouns / nouns (TEACHER, FATHER)
    2. Time/Location markers (TIME, WORK)
    3. Descriptors (GOOD, HAPPY)
    4. Social/Greetings (HELLO, THANK YOU)
    
    Args:
        words (list): List of glosses in detection order
        
    Returns:
        list: Sorted list of glosses
    """
    priority = {
        "I": 0, "YOU": 1, "YOU (PLURAL)": 1, 
        "TEACHER": 2, "FATHER": 2, "MOTHER": 2,
        "TIME": 3, "WORK": 3,
        "GOOD": 4, "HAPPY": 4, "SAD": 4,
        "HELLO": 5, "THANK YOU": 5, "GOOD MORNING": 5
    }
    return sorted(words, key=lambda w: priority.get(w, 99))


def calculate_dynamic_timeout(sentence_buffer):
    """
    Calculate timeout duration based on linguistic context.
    
    RULES:
    - Empty buffer → 3s (short, waiting for first word)
    - Single pronoun/subject → 6s (user likely continuing: "I ...")
    - Subject + building → 5s (mid-sentence construction)
    - Complete greeting → 3.5s (might be done)
    - Default → 4s
    
    This prevents cutting off users who are still thinking/signing while
    allowing quick finalization of complete thoughts.
    
    Args:
        sentence_buffer (list): Current accumulated glosses
        
    Returns:
        float: Timeout duration in seconds
    """
    if len(sentence_buffer) == 0:
        return 3.0  # Short timeout for empty buffer
    
    # Indicators that more content is likely coming
    continuation_words = {"I", "YOU", "YOU (PLURAL)", "TEACHER", "FATHER", "MOTHER"}
    has_subject = any(word in continuation_words for word in sentence_buffer)
    
    # Indicators of potentially complete thoughts
    complete_indicators = {"THANK YOU", "GOOD MORNING", "HELLO"}
    has_greeting = any(phrase in " ".join(sentence_buffer) for phrase in complete_indicators)
    
    if has_subject and len(sentence_buffer) == 1:
        return 6.0  # Long: single subject word suggests continuation
    elif has_subject and len(sentence_buffer) < 3:
        return 5.0  # Medium-long: building a sentence
    elif has_greeting:
        return 3.5  # Medium: greeting might be complete
    else:
        return 4.0  # Default fallback


def parse_intent(buffer, user_name="Nitant"):
    """
    Enhanced slot-based intent parser with robust pattern matching.
    
    Design Philosophy:
    - Uses BOTH order-independent sets (for flexibility) and ordered sequences
    - Phrase detection for multi-word expressions
    - Graceful fallback with grammatical normalization
    
    The parser is deterministic and rule-based - no ML/LLM required.
    This keeps latency low and behavior predictable.
    
    Args:
        buffer (list): List of detected glosses in temporal order
        user_name (str): User's name for personalization
        
    Returns:
        str: Natural English sentence with proper grammar and punctuation
    """
    # Preserve original temporal order
    words_ordered = list(buffer)
    
    # For order-independent matching (handles signing variance)
    words_set = set(buffer)
    
    # For phrase detection (multi-word units like "GOOD MORNING")
    raw_joined = " ".join(buffer)
    
    # ════════════════════════════════════════════════════════════════
    # TIER 1: IDENTITY & SELF-REFERENCE
    # Priority: Personal statements about self
    # ════════════════════════════════════════════════════════════════
    if "I" in words_set:
        if "HAPPY" in words_set:
            return f"I am {user_name} and I am feeling very happy."
        if "SAD" in words_set:
            return f"I am {user_name} and I am feeling sad."
        if "GOOD" in words_set and "TIME" not in words_set:
            return f"I am {user_name} and I am doing well."
        if "TEACHER" in words_set:
            return f"I am {user_name}, and I am a teacher."
        if "FATHER" in words_set:
            if "GOOD" in words_set:
                return f"My father is doing well."
            else:
                return f"This is about my father."
        if "MOTHER" in words_set:
            if "GOOD" in words_set:
                return f"My mother is doing well."
            else:
                return f"This is about my mother."
        if len(words_set) == 1:
            # Single "I" - simple identity statement
            return f"I am {user_name}."
    
    # ════════════════════════════════════════════════════════════════
    # TIER 2: QUESTIONS & REQUESTS
    # Priority: Interrogative patterns
    # ════════════════════════════════════════════════════════════════
    if "TIME" in words_set:
        if "YOU" in words_set or "YOU (PLURAL)" in words_set:
            return "Could you please tell me the current time?"
        if "GOOD" in words_set:
            return "Is this a good time?"
        return "What is the time?"
    
    if "YOU" in words_set:
        if "HAPPY" in words_set:
            return "Are you happy?"
        if "GOOD" in words_set:
            return "Are you doing well?"
        if "TEACHER" in words_set and len(words_set) == 2:
            return "You are the teacher."
    
    # ════════════════════════════════════════════════════════════════
    # TIER 3: GREETINGS & SOCIAL EXPRESSIONS
    # Priority: Multi-word social phrases
    # ════════════════════════════════════════════════════════════════
    if "THANK YOU" in raw_joined:
        if "TEACHER" in words_set:
            return "Thank you very much, respected teacher."
        return "Thank you so much."
    
    if "GOOD MORNING" in raw_joined:
        if "TEACHER" in words_set:
            return "Good morning, respected panel members."
        return "Good morning to everyone."
    
    if "HELLO" in words_set:
        if "TEACHER" in words_set:
            return "Hello, honorable teacher."
        if "GOOD" in words_set:
            return "Hello, and good to see you."
        return "Hello everyone."
    
    # ════════════════════════════════════════════════════════════════
    # TIER 4: NORMALIZED FALLBACK
    # For unmatched patterns - provide grammatical output
    # ════════════════════════════════════════════════════════════════
    normalized = normalize_gloss_order(words_ordered)
    capitalized = " ".join(normalized).capitalize()
    
    # Smart punctuation based on content
    if any(q in words_set for q in ["TIME", "YOU"]) and "THANK" not in raw_joined:
        return capitalized + "?"
    else:
        return capitalized + "."


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ISL RECOGNITION LOOP
# ═══════════════════════════════════════════════════════════════════════════

def run_isl(shm_name, shape, frame_ready_event, stop_event, result_queue, mode_flag, buffer_queue=None):
    """
    Main ISL recognition process with robust temporal intelligence.
    
    This function runs in a separate process and continuously:
    1. Reads frames from shared memory
    2. Extracts normalized features via MediaPipe
    3. Feeds 30-frame windows to LSTM model
    4. Smooths predictions via temporal buffer
    5. Accumulates words into sentences
    6. Finalizes sentences using intelligent timing logic
    
    Args:
        shm_name (str): Shared memory block name
        shape (tuple): Frame shape (H, W, C)
        frame_ready_event (Event): Signal that new frame is available
        stop_event (Event): Signal to terminate process
        result_queue (Queue): Output queue for finalized sentences
        mode_flag (Value): Shared integer (0=HCI, 1=ISL)
        buffer_queue (Queue, optional): Output queue for live buffer updates (UI feedback)
    """
    print("\033[96m[ISL] ═══════════════════════════════════════════════\033[0m")
    print("\033[96m[ISL] PRODUCTION CSLR ENGINE STARTING\033[0m")
    print("\033[96m[ISL] Version: 3.5 (Temporal Intelligence)\033[0m")
    print("\033[96m[ISL] ═══════════════════════════════════════════════\033[0m\n")
    
    # ═══════════════════════════════════════════════════════════════
    # PATH RESOLUTION
    # ═══════════════════════════════════════════════════════════════
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '../../'))
    MODEL_PATH = os.path.join(project_root, "models", "ISL_Model.tflite")
    LABEL_PATH = os.path.join(project_root, "data", "processed", "labels.npy")
    BRIDGE_PATH = os.path.join(project_root, "data", "isl_live.txt")
    
    print(f"\033[90m[ISL] Model: {MODEL_PATH}\033[0m")
    print(f"\033[90m[ISL] Labels: {LABEL_PATH}\033[0m")
    print(f"\033[90m[ISL] Bridge: {BRIDGE_PATH}\033[0m\n")

    # ═══════════════════════════════════════════════════════════════
    # SHARED MEMORY SETUP
    # ═══════════════════════════════════════════════════════════════
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
        frame_buffer = np.ndarray(shape, dtype=np.uint8, buffer=shm.buf)
        print(f"\033[92m[ISL] ✓ Shared memory attached: {shm_name}\033[0m")
    except Exception as e:
        print(f"\033[91m[ISL] ✗ Failed to attach shared memory: {e}\033[0m")
        return

    # ═══════════════════════════════════════════════════════════════
    # MEDIAPIPE INITIALIZATION
    # ═══════════════════════════════════════════════════════════════
    mp_holistic = mp.solutions.holistic
    holistic = mp_holistic.Holistic(
        min_detection_confidence=0.5, 
        min_tracking_confidence=0.5, 
        model_complexity=1  # Balance between accuracy and speed
    )
    print(f"\033[92m[ISL] ✓ MediaPipe Holistic initialized\033[0m")

    # ═══════════════════════════════════════════════════════════════
    # TFLITE MODEL INITIALIZATION
    # ═══════════════════════════════════════════════════════════════
    interpreter = Interpreter(model_path=MODEL_PATH)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    labels_map = np.load(LABEL_PATH, allow_pickle=True).item()

    id_to_label = {v: k.strip().upper() for k, v in labels_map.items()}
    
    print(f"\033[92m[ISL] ✓ TFLite model loaded\033[0m")
    print(f"\033[92m[ISL] ✓ Vocabulary: {len(id_to_label)} signs\033[0m")
    print(f"\033[92m[ISL] ✓ Input shape: {input_details[0]['shape']}\033[0m\n")

    # ═══════════════════════════════════════════════════════════════
    # STATE VARIABLES - TEMPORAL TRACKING
    # ═══════════════════════════════════════════════════════════════
    
    # Sliding window for LSTM (30 frames @ 30fps = 1 second of video)
    sequence = collections.deque(maxlen=30)
    
    # Prediction smoothing buffer (5 consecutive predictions)
    # CRITICAL: This is now a LEAKY buffer - we remove oldest, not clear all
    prediction_buffer = collections.deque(maxlen=5)
    
    # Sentence accumulator - the core output buffer
    sentence_buffer = []
    
    # Timing trackers
    last_word_time = 0              # Timestamp when last word was added to sentence
    last_valid_time = time.time()   # Last time ANY valid activity occurred
    
    # Word state tracking
    last_detected_word = ""         # Previous word (for cooldown anti-spam)
    
    # ═══════════════════════════════════════════════════════════════
    # STATE VARIABLES - TEMPORAL INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════
    
    # Idle detection
    idle_counter = 0
    IDLE_COMMIT_FRAMES = 10          # 10 frames @ 30fps ≈ 0.33s of continuous idle
    
    # Word hold confirmation system
    # A word must be STABLE for this duration before adding
    word_hold_start = 0
    word_hold_candidate = ""
    WORD_HOLD_DURATION = 0.5        # Seconds - prevents flickering
    
    # Post-word stability protection
    # CRITICAL FIX: After adding a word, block finalization briefly
    # This prevents cutting off sentences right after a word appears
    POST_WORD_STABILITY = 0.8       # Seconds - grace period after word addition
    
    # Timeout management with extension grace
    timeout_armed = False
    timeout_start_time = 0
    BUFFER_EXTENSION_GRACE = 1    # Seconds - if new word comes, extend instead of finalize
    
    # Cooldown anti-spam
    COOLDOWN = 2.0                  # Seconds - prevent immediate re-detection of same word
    
    print("\033[96m[ISL] ═══════════════════════════════════════════════\033[0m")
    print("\033[96m[ISL] RECOGNITION LOOP ACTIVE\033[0m")
    print("\033[96m[ISL] Waiting for frames in ISL mode...\033[0m")
    print("\033[96m[ISL] ═══════════════════════════════════════════════\033[0m\n")

    # ═══════════════════════════════════════════════════════════════
    # MAIN RECOGNITION LOOP
    # ═══════════════════════════════════════════════════════════════
    
    while not stop_event.is_set():
        # ───────────────────────────────────────────────────────────
        # WAIT FOR NEW FRAME
        # ───────────────────────────────────────────────────────────
        if not frame_ready_event.wait(timeout=1.0): 
            continue
        
        # ───────────────────────────────────────────────────────────
        # MODE CHECK - Only process in ISL mode
        # ───────────────────────────────────────────────────────────
        if mode_flag.value != 1:
            # In HCI mode - clear all buffers to prevent stale state
            if len(sequence) > 0 or len(sentence_buffer) > 0:
                sequence.clear()
                prediction_buffer.clear()
                sentence_buffer.clear()
                idle_counter = 0
                timeout_armed = False
                word_hold_candidate = ""
                print("\033[90m[ISL] Mode switched to HCI - buffers cleared\033[0m")
            continue

        # ───────────────────────────────────────────────────────────
        # FRAME ACQUISITION & FEATURE EXTRACTION
        # ───────────────────────────────────────────────────────────
        current_time = time.time()
        current_frame = frame_buffer.copy()
        image = cv2.cvtColor(current_frame, cv2.COLOR_BGR2RGB)
        results = holistic.process(image)
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 1: SENTENCE FINALIZATION LOGIC
        # 
        # This runs BEFORE prediction to decide if current buffer
        # should be finalized into a complete sentence.
        # ═══════════════════════════════════════════════════════════
        
        time_since_last_word = current_time - last_valid_time
        dynamic_timeout = calculate_dynamic_timeout(sentence_buffer)
        
        # ───────────────────────────────────────────────────────────
        # FINALIZATION CONDITION 1: Aggressive Idle Commit
        # If user has been idle for 8+ frames, prepare to finalize
        # ───────────────────────────────────────────────────────────
        idle_triggered = idle_counter >= IDLE_COMMIT_FRAMES
        
        # ───────────────────────────────────────────────────────────
        # FINALIZATION CONDITION 2: Dynamic Timeout with Extension
        # If timeout expires, arm countdown. If still no word after
        # grace period, trigger finalization.
        # ───────────────────────────────────────────────────────────
        timeout_triggered = False
        if time_since_last_word > dynamic_timeout:
            if not timeout_armed:
                # First time crossing threshold - arm timeout
                timeout_armed = True
                timeout_start_time = current_time
                print(f"\033[93m[ISL] ⏰ Timeout armed ({dynamic_timeout:.1f}s expired, {BUFFER_EXTENSION_GRACE}s grace active)\033[0m")
            else:
                # Timeout was already armed - check if grace period expired
                time_since_armed = current_time - timeout_start_time
                if time_since_armed > BUFFER_EXTENSION_GRACE:
                    timeout_triggered = True
        
        # ───────────────────────────────────────────────────────────
        # FINALIZATION CONDITION 3: Post-Word Stability Protection
        # CRITICAL: Do NOT finalize immediately after adding a word
        # This prevents cutting off sentences mid-thought
        # ───────────────────────────────────────────────────────────
        time_since_word_added = current_time - last_word_time
        in_post_word_stability = time_since_word_added < POST_WORD_STABILITY
        
        # ───────────────────────────────────────────────────────────
        # FINALIZATION CONDITION 4: Word Hold Protection
        # CRITICAL: Do NOT finalize while confirming a new word
        # This prevents cutting off sentences during transitions
        # ───────────────────────────────────────────────────────────
        word_hold_in_progress = (word_hold_candidate != "")
        
        # ───────────────────────────────────────────────────────────
        # FINALIZATION CONDITION 5: Minimum Buffer Check
        # Only finalize if buffer has meaningful content
        # ───────────────────────────────────────────────────────────
        min_buffer_met = len(sentence_buffer) >= 2 or (
            len(sentence_buffer) == 1 and sentence_buffer[0] in ["I", "HELLO", "THANK YOU"]
        )
        
        # ───────────────────────────────────────────────────────────
        # FINALIZATION DECISION TREE
        # All conditions must align for safe finalization
        # ───────────────────────────────────────────────────────────
        should_finalize = (
            len(sentence_buffer) > 0 and              # Have content
            (idle_triggered or timeout_triggered) and # Trigger condition met
            min_buffer_met and                        # Enough words
            not in_post_word_stability and           # NOT right after word addition
            not word_hold_in_progress                # NOT during word confirmation
        )
        
        if should_finalize:
            # ───────────────────────────────────────────────────────
            # EXECUTE FINALIZATION
            # ───────────────────────────────────────────────────────
            
            # Use enhanced grammar engine
            final_sentence = parse_intent(sentence_buffer)
            
            trigger_reason = "Idle Detection" if idle_triggered else f"Timeout ({dynamic_timeout:.1f}s)"
            
            print(f"\n\033[93m╔═══════════════════════════════════════════════════════╗\033[0m")
            print(f"\033[93m║  SENTENCE COMPLETE                                     ║\033[0m")
            print(f"\033[93m╠═══════════════════════════════════════════════════════╣\033[0m")
            print(f"\033[92m║  Output: {final_sentence[:45]:<45} ║\033[0m")
            print(f"\033[90m║  Buffer: {str(sentence_buffer)[:45]:<45} ║\033[0m")
            print(f"\033[90m║  Trigger: {trigger_reason[:44]:<44} ║\033[0m")
            print(f"\033[93m╚═══════════════════════════════════════════════════════╝\033[0m\n")
            
            # Send to Jarvis orchestrator via queue
            result_queue.put(final_sentence)
            
            # Write to bridge file for GUI
            try:
                with open(BRIDGE_PATH, "w") as f:
                    f.write(final_sentence)
            except Exception as e:
                print(f"\033[91m[ISL] Bridge write error: {e}\033[0m")
            
            # Reset all sentence-level state
            sentence_buffer.clear()
            last_detected_word = ""
            idle_counter = 0
            timeout_armed = False
            timeout_start_time = 0
            word_hold_candidate = ""
            word_hold_start = 0
            
            # Update buffer feedback queue (clear it)
            if buffer_queue is not None:
                try:
                    while not buffer_queue.empty():
                        buffer_queue.get_nowait()
                    buffer_queue.put_nowait("")
                except:
                    pass
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 2: FEATURE EXTRACTION & NORMALIZATION
        # ═══════════════════════════════════════════════════════════
        
        keypoints = normalize_features(results)
        sequence.append(keypoints)
        
        # Need full window for LSTM
        if len(sequence) < 30:
            continue
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 3: LSTM INFERENCE
        # ═══════════════════════════════════════════════════════════
        
        input_data = np.expand_dims(list(sequence), axis=0).astype(np.float32)
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])[0]
        
        pred_id = int(np.argmax(output_data))
        confidence = float(np.max(output_data))
        word = id_to_label.get(pred_id, "Unknown")
        
        # ═══════════════════════════════════════════════════════════
        # PHASE 4: PREDICTION SMOOTHING
        # 
        # CRITICAL FIX: Leaky buffer approach
        # Instead of clearing buffer on low confidence, we let it
        # naturally decay. This preserves temporal information across
        # transitions and reduces re-stabilization delay.
        # ═══════════════════════════════════════════════════════════
        
        # ───────────────────────────────────────────────────────────
        # HYSTERESIS THRESHOLD
        # Lower confidence requirement if we're mid-sentence
        # ───────────────────────────────────────────────────────────
        if last_detected_word and last_detected_word.lower() != "idle":
            # Mid-sentence: be more lenient to handle transitions
            confidence_threshold = 0.70
        else:
            # Fresh start: be strict
            confidence_threshold = 0.80
        
        if confidence > confidence_threshold:
            # ───────────────────────────────────────────────────────
            # LEAKY BUFFER UPDATE
            # Add new prediction - oldest will auto-drop due to maxlen
            # This is fundamentally different from .clear()
            # ───────────────────────────────────────────────────────
            prediction_buffer.append((pred_id, confidence))
            
            # Calculate smoothed prediction via majority voting
            ids = [p for p, _ in prediction_buffer]
            stable_pred_id = max(set(ids), key=ids.count)
            word = id_to_label.get(stable_pred_id, "Unknown")
            
            # Calculate average confidence for this word
            word_confidences = [c for p, c in prediction_buffer if p == stable_pred_id]
            avg_conf = np.mean(word_confidences) if word_confidences else 0.0
            
            # ═══════════════════════════════════════════════════════
            # PHASE 5: WORD DETECTION & HOLD CONFIRMATION
            # ═══════════════════════════════════════════════════════
            
            if word.lower() != "idle" and word != "unknown":
                # ───────────────────────────────────────────────────
                # WORD HOLD CONFIRMATION SYSTEM
                # A word must be stable for WORD_HOLD_DURATION before
                # being added to sentence buffer. This prevents
                # flickering and ensures intentional signs.
                # ───────────────────────────────────────────────────
                
                if word != word_hold_candidate:
                    # New word detected - start hold timer
                    word_hold_candidate = word
                    word_hold_start = current_time
                    print(f"\033[94m[ISL] ⏱  Hold started: {word} (need {WORD_HOLD_DURATION}s confirmation)\033[0m")
                else:
                    # Same word held - check if duration met
                    hold_duration = current_time - word_hold_start
                    
                    if hold_duration >= WORD_HOLD_DURATION:
                        # Word confirmed - now apply filters
                        
                        # ───────────────────────────────────────────
                        # FILTER 1: Cooldown (prevent spam)
                        # ───────────────────────────────────────────
                        is_new_word = word != last_detected_word
                        is_cooldown_over = (current_time - last_word_time) > COOLDOWN
                        
                        if is_new_word or is_cooldown_over:
                            # ───────────────────────────────────────
                            # FILTER 2: Temporal memory (last 3 words)
                            # Prevent immediate repetition within phrase
                            # ───────────────────────────────────────
                            recent_window = sentence_buffer[-3:] if len(sentence_buffer) >= 3 else sentence_buffer
                            
                            if word not in recent_window:
                                # ═══════════════════════════════════
                                # ADD WORD TO SENTENCE BUFFER
                                # ═══════════════════════════════════
                                sentence_buffer.append(word)
                                
                                print(f"\033[92m[ISL] ✓ ADDED: {word.upper():<15} | Hold: {hold_duration:.2f}s | Conf: {avg_conf:.3f} | Buffer: {sentence_buffer}\033[0m")
                                
                                # Update timing trackers
                                last_word_time = current_time
                                last_valid_time = current_time
                                last_detected_word = word
                                
                                # Reset hold system
                                word_hold_candidate = ""
                                word_hold_start = 0
                                
                                # CRITICAL: Disarm timeout since new word arrived
                                # This implements buffer extension logic
                                if timeout_armed:
                                    print(f"\033[93m[ISL] ↻ Timeout disarmed - buffer extended by new word\033[0m")
                                    timeout_armed = False
                                    timeout_start_time = 0
                                
                                # ───────────────────────────────────
                                # LEAKY BUFFER: Don't clear, let decay
                                # Only remove oldest prediction
                                # ───────────────────────────────────
                                if len(prediction_buffer) == prediction_buffer.maxlen:
                                    prediction_buffer.popleft()
                                
                                # Update live buffer feedback for UI
                                if buffer_queue is not None:
                                    try:
                                        while not buffer_queue.empty():
                                            buffer_queue.get_nowait()
                                        buffer_display = " → ".join(sentence_buffer)
                                        buffer_queue.put_nowait(buffer_display)
                                    except:
                                        pass
                            else:
                                # Rejected: duplicate in recent window
                                print(f"\033[90m[ISL] ⊘ Rejected: {word} (duplicate in recent buffer: {recent_window})\033[0m")
                                last_valid_time = current_time
                                # Don't clear buffer - let it decay naturally
                        else:
                            # Rejected: still in cooldown
                            print(f"\033[90m[ISL] ⊘ Rejected: {word} (cooldown active, {COOLDOWN - (current_time - last_word_time):.1f}s remaining)\033[0m")
                            last_valid_time = current_time
            
            # ═══════════════════════════════════════════════════════
            # IDLE HANDLING
            # ═══════════════════════════════════════════════════════
            elif word.lower() == "idle":
                idle_counter += 1
                
                # Reset word hold if idle detected
                if word_hold_candidate:
                    print(f"\033[90m[ISL] ⊘ Hold cancelled: {word_hold_candidate} (idle detected)\033[0m")
                    word_hold_candidate = ""
                    word_hold_start = 0
                
                if idle_counter == IDLE_COMMIT_FRAMES:
                    print(f"\033[93m[ISL] 💤 Idle threshold reached ({IDLE_COMMIT_FRAMES} frames) - preparing finalization\033[0m")
        
        else:
            # ───────────────────────────────────────────────────────
            # LOW CONFIDENCE HANDLING
            # CRITICAL: Do NOT clear buffer - let it decay naturally
            # This preserves partial information during transitions
            # ───────────────────────────────────────────────────────
            
            # Leaky approach: oldest prediction will naturally fall off
            # when new high-confidence prediction comes in
            
            # Reset idle counter (not idle if we're getting predictions)
            idle_counter = 0
    
    # ═══════════════════════════════════════════════════════════════
    # CLEANUP ON EXIT
    # ═══════════════════════════════════════════════════════════════
    shm.close()
    print("\033[96m[ISL] Process terminated gracefully.\033[0m")