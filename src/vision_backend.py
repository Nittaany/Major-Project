#!2.5
import cv2
import numpy as np
import multiprocessing as mp
from multiprocessing import shared_memory
import time
import mediapipe as mp_vision  # Renamed to avoid conflict

# --- IMPORT EXISTING CONTROLLERS ---
from controllers.HCI_Controller import run_hci
from controllers.ISL_Controller import run_isl

# --- CONFIGURATION ---
WAKE_GESTURE_TIME = 2.0       # Seconds to hold Thumbs Up to start
TOGGLE_GESTURE_TIME = 2     # Seconds to hold Open Palm to switch
ROI_SIZE = 150                # Pixel size of the "Hot Corner" (Top-Left)

def is_thumbs_up(lm):
    """
    Check if hand is in Thumbs Up pose:
    - Thumb tip is higher than other finger tips (in pixel Y, lower value is higher)
    - Fingers are curled (Tip y > PIP y)
    """
    # Thumb Tip (4) should be highest point (lowest y value)
    if lm[4].y > lm[8].y or lm[4].y > lm[12].y: return False
    
    # Fingers should be curled (Tip y > PIP y)
    # Index(8) > IndexPIP(6), Middle(12) > MiddlePIP(10), etc.
    if lm[8].y < lm[6].y: return False
    if lm[12].y < lm[10].y: return False
    
    return True

def is_open_palm(lm):
    """
    Check if hand is Open Palm:
    - All fingers extended (Tip y < PIP y)
    """
    fingers = [8, 12, 16, 20]
    pips = [6, 10, 14, 18]
    
    for f, p in zip(fingers, pips):
        if lm[f].y > lm[p].y: return False
    return True

def main():
    # 1. SETUP SHARED MEMORY
    WIDTH, HEIGHT = 640, 480
    FRAME_SHAPE = (HEIGHT, WIDTH, 3)
    FRAME_SIZE = int(np.prod(FRAME_SHAPE))
    
    try:
        shm = shared_memory.SharedMemory(create=True, size=FRAME_SIZE, name='jarvis_shm')
    except FileExistsError:
        shm = shared_memory.SharedMemory(name='jarvis_shm')

    # 2. SETUP CONTROLS
    frame_ready = mp.Event()
    stop_event = mp.Event()
    isl_result_queue = mp.Queue()
    current_isl_text = "Waiting for signs..."
    mode_flag = mp.Value('i', 0)  # 0 = Mouse, 1 = ISL

    # 3. START CAMERA
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): cap = cv2.VideoCapture(1)

    # 4. WAKE UP SEQUENCE (The "Low Power" Loop)
    print("[BACKEND] Waiting for Wake Gesture (THUMBS UP)...")
    mp_hands = mp_vision.solutions.hands
    hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    
    wake_start_time = 0
    system_active = False

    while not system_active:
        ret, frame = cap.read()
        if not ret: continue
        
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        
        status_text = "Show THUMBS UP to Start"
        color = (0, 255, 255)

        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0].landmark
            if is_thumbs_up(lm):
                if wake_start_time == 0: wake_start_time = time.time()
                elapsed = time.time() - wake_start_time
                progress = min(elapsed / WAKE_GESTURE_TIME, 1.0)
                
                # Draw Loading Bar
                cv2.rectangle(frame, (200, 400), (int(200 + 240 * progress), 420), (0, 255, 0), -1)
                status_text = f"HOLD... {int(progress*100)}%"
                
                if elapsed >= WAKE_GESTURE_TIME:
                    system_active = True
            else:
                wake_start_time = 0
        else:
            wake_start_time = 0

        cv2.putText(frame, status_text, (180, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.imshow("Jarvis Vision Feed", frame)
        if cv2.waitKey(1) & 0xFF == 27: return

    # 5. SYSTEM START
    print("[BACKEND] Wake Gesture Confirmed. Launching Processes...")
    
    p_hci = mp.Process(target=run_hci, args=('jarvis_shm', FRAME_SHAPE, frame_ready, stop_event, mode_flag))
    p_isl = mp.Process(target=run_isl, args=('jarvis_shm', FRAME_SHAPE, frame_ready, stop_event, isl_result_queue, mode_flag))
    
    p_hci.start()
    p_isl.start()
    
    shared_frame = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)
    
    toggle_start_time = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret: continue
            
            # Standardize
            frame = cv2.resize(frame, (WIDTH, HEIGHT))
            frame = cv2.flip(frame, 1)
            
            # --- TOGGLE LOGIC (The "Long Clutch") ---
            # We run a lightweight hand check here on the main thread
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)
            
            toggle_active = False
            TOGGLE_GESTURE_TIME = 3.5  
            
            if results.multi_hand_landmarks:
                lm = results.multi_hand_landmarks[0].landmark
                
                # Check: Hand Shape (Open Palm) ANYWHERE on the screen
                if is_open_palm(lm):
                    toggle_active = True
                    if toggle_start_time == 0: toggle_start_time = time.time()
                    
                    elapsed = time.time() - toggle_start_time
                    progress = min(elapsed / TOGGLE_GESTURE_TIME, 1.0)
                    
                    # --- CENTERED LOADING RING ---
                    cx, cy = WIDTH // 2, HEIGHT // 2
                    cv2.circle(frame, (cx, cy), 60, (200, 200, 200), 2)
                    # Draw Arc/Progress starting from top (-90 degrees)
                    cv2.ellipse(frame, (cx, cy), (60, 60), 0, -90, -90 + int(360 * progress), (0, 255, 100), 5)
                    cv2.putText(frame, "SWITCHING MODE...", (cx - 75, cy + 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
                    
                    if elapsed >= TOGGLE_GESTURE_TIME:
                        with mode_flag.get_lock():
                            mode_flag.value = 1 - mode_flag.value
                        
                        new_mode = "ISL MODE" if mode_flag.value == 1 else "MOUSE MODE"
                        print(f"\n\033[93m[SYSTEM] 🔄 Mode Switched to: {new_mode}\033[0m\n")
                        toggle_start_time = 0 
                        current_isl_text = "Waiting for signs..." # Reset subtitles on switch
                        time.sleep(1.0) 
            
            if not toggle_active:
                toggle_start_time = 0

            # Write to Memory
            np.copyto(shared_frame, frame)
            frame_ready.set()

            # ═══════════════════════════════════════════════════════════════
            # SLEEK UI OVERLAY
            # ═══════════════════════════════════════════════════════════════
            overlay = frame.copy()
            is_isl = (mode_flag.value == 1)
            
            # Top Bar (Status)
            cv2.rectangle(overlay, (0, 0), (WIDTH, 45), (15, 15, 15), -1)
            
            # Bottom Bar (Subtitles - Only in ISL Mode)
            if is_isl:
                cv2.rectangle(overlay, (0, HEIGHT - 60), (WIDTH, HEIGHT), (15, 15, 15), -1)
                
            # Blend the dark bars with the camera feed (75% opacity)
            alpha = 0.75
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

            # --- MODE TEXT (Top Center) ---
            mode_text = " ISL SIGN MODE " if is_isl else " HCI MOUSE MODE "
            text_color = (200, 200, 50) if is_isl else (100, 255, 100) # Cyan for ISL, Green for HCI
            
            font = cv2.FONT_HERSHEY_SIMPLEX
            text_size = cv2.getTextSize(mode_text, font, 0.7, 2)[0]
            text_x = (WIDTH - text_size[0]) // 2
            cv2.putText(frame, mode_text, (text_x, 30), font, 0.7, text_color, 2)

            # --- SUBTITLES (Bottom Center) ---
            if not isl_result_queue.empty():
                current_isl_text = isl_result_queue.get()
                
            if is_isl and current_isl_text:
                sub_size = cv2.getTextSize(current_isl_text, font, 0.9, 2)[0]
                sub_x = (WIDTH - sub_size[0]) // 2
                cv2.putText(frame, current_isl_text, (sub_x, HEIGHT - 20), font, 0.9, (255, 255, 255), 2)

            # beautiful frame show
            cv2.imshow("Jarvis Vision Feed", frame)

            if cv2.waitKey(1) & 0xFF == 27: break # ESC to quit
            frame_ready.clear()

    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        p_hci.join()
        p_isl.join()
        cap.release()
        cv2.destroyAllWindows()
        shm.close()
        shm.unlink()

if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    main()


#!old code (2.4)
# import cv2
# import numpy as np
# import multiprocessing as mp
# from multiprocessing import shared_memory
# import time
# import mediapipe as mp_vision  # Renamed to avoid conflict

# # --- IMPORT EXISTING CONTROLLERS ---
# from controllers.HCI_Controller import run_hci
# from controllers.ISL_Controller import run_isl

# # --- CONFIGURATION ---
# WAKE_GESTURE_TIME = 2.0       # Seconds to hold Thumbs Up to start
# TOGGLE_GESTURE_TIME = 2     # Seconds to hold Open Palm to switch
# ROI_SIZE = 150                # Pixel size of the "Hot Corner" (Top-Left)

# def is_thumbs_up(lm):
#     """
#     Check if hand is in Thumbs Up pose:
#     - Thumb tip is higher than other finger tips (in pixel Y, lower value is higher)
#     - Fingers are curled (Tip y > PIP y)
#     """
#     # Thumb Tip (4) should be highest point (lowest y value)
#     if lm[4].y > lm[8].y or lm[4].y > lm[12].y: return False
    
#     # Fingers should be curled (Tip y > PIP y)
#     # Index(8) > IndexPIP(6), Middle(12) > MiddlePIP(10), etc.
#     if lm[8].y < lm[6].y: return False
#     if lm[12].y < lm[10].y: return False
    
#     return True

# def is_open_palm(lm):
#     """
#     Check if hand is Open Palm:
#     - All fingers extended (Tip y < PIP y)
#     """
#     fingers = [8, 12, 16, 20]
#     pips = [6, 10, 14, 18]
    
#     for f, p in zip(fingers, pips):
#         if lm[f].y > lm[p].y: return False
#     return True

# def main():
#     # 1. SETUP SHARED MEMORY
#     WIDTH, HEIGHT = 640, 480
#     FRAME_SHAPE = (HEIGHT, WIDTH, 3)
#     FRAME_SIZE = int(np.prod(FRAME_SHAPE))
    
#     try:
#         shm = shared_memory.SharedMemory(create=True, size=FRAME_SIZE, name='jarvis_shm')
#     except FileExistsError:
#         shm = shared_memory.SharedMemory(name='jarvis_shm')

#     # 2. SETUP CONTROLS
#     frame_ready = mp.Event()
#     stop_event = mp.Event()
#     isl_result_queue = mp.Queue()
#     mode_flag = mp.Value('i', 0)  # 0 = Mouse, 1 = ISL

#     # 3. START CAMERA
#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened(): cap = cv2.VideoCapture(1)

#     # 4. WAKE UP SEQUENCE (The "Low Power" Loop)
#     print("[BACKEND] Waiting for Wake Gesture (THUMBS UP)...")
#     mp_hands = mp_vision.solutions.hands
#     hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    
#     wake_start_time = 0
#     system_active = False

#     while not system_active:
#         ret, frame = cap.read()
#         if not ret: continue
        
#         frame = cv2.flip(frame, 1)
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = hands.process(rgb)
        
#         status_text = "Show THUMBS UP to Start"
#         color = (0, 255, 255)

#         if results.multi_hand_landmarks:
#             lm = results.multi_hand_landmarks[0].landmark
#             if is_thumbs_up(lm):
#                 if wake_start_time == 0: wake_start_time = time.time()
#                 elapsed = time.time() - wake_start_time
#                 progress = min(elapsed / WAKE_GESTURE_TIME, 1.0)
                
#                 # Draw Loading Bar
#                 cv2.rectangle(frame, (200, 400), (int(200 + 240 * progress), 420), (0, 255, 0), -1)
#                 status_text = f"HOLD... {int(progress*100)}%"
                
#                 if elapsed >= WAKE_GESTURE_TIME:
#                     system_active = True
#             else:
#                 wake_start_time = 0
#         else:
#             wake_start_time = 0

#         cv2.putText(frame, status_text, (180, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
#         cv2.imshow("Jarvis Vision Feed", frame)
#         if cv2.waitKey(1) & 0xFF == 27: return

#     # 5. SYSTEM START
#     print("[BACKEND] Wake Gesture Confirmed. Launching Processes...")
    
#     p_hci = mp.Process(target=run_hci, args=('jarvis_shm', FRAME_SHAPE, frame_ready, stop_event, mode_flag))
#     p_isl = mp.Process(target=run_isl, args=('jarvis_shm', FRAME_SHAPE, frame_ready, stop_event, isl_result_queue, mode_flag))
    
#     p_hci.start()
#     p_isl.start()
    
#     shared_frame = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)
    
#     toggle_start_time = 0

#     try:
#         while True:
#             ret, frame = cap.read()
#             if not ret: continue
            
#             # Standardize
#             frame = cv2.resize(frame, (WIDTH, HEIGHT))
#             frame = cv2.flip(frame, 1)
            
#             # --- TOGGLE LOGIC (The "Safety Lock") ---
#             # We run a lightweight hand check here on the main thread
#             # just for the toggle gesture.
#             rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#             results = hands.process(rgb)
            
#             toggle_active = False
            
#             if results.multi_hand_landmarks:
#                 lm = results.multi_hand_landmarks[0].landmark
#                 # Check 1: Location (Top-Left Corner)
#                 wrist = lm[0]
#                 hx, hy = int(wrist.x * WIDTH), int(wrist.y * HEIGHT)
                
#                 if hx < ROI_SIZE and hy < ROI_SIZE:
#                     # Check 2: Hand Shape (Open Palm)
#                     if is_open_palm(lm):
#                         toggle_active = True
#                         if toggle_start_time == 0: toggle_start_time = time.time()
                        
#                         elapsed = time.time() - toggle_start_time
#                         progress = min(elapsed / TOGGLE_GESTURE_TIME, 1.0)
                        
#                         # Visual Feedback in Corner
#                         cv2.circle(frame, (75, 75), 60, (255, 255, 255), 2)
#                         cv2.circle(frame, (75, 75), 50, (0, 255, 0), -1)
#                         # Draw Arc/Progress
#                         cv2.ellipse(frame, (75, 75), (60, 60), 0, 0, 360 * progress, (0, 255, 0), 5)
                        
#                         if elapsed >= TOGGLE_GESTURE_TIME:
#                             with mode_flag.get_lock():
#                                 mode_flag.value = 1 - mode_flag.value
#                             toggle_start_time = 0 # Reset
#                             # Visual Flash
#                             cv2.rectangle(frame, (0,0), (WIDTH, HEIGHT), (255, 255, 255), 10)
            
#             if not toggle_active:
#                 toggle_start_time = 0

#             # Write to Memory
#             np.copyto(shared_frame, frame)
#             frame_ready.set()

#             # --- UI OVERLAY ---
#             # Draw Hot Corner
#             cv2.rectangle(frame, (0,0), (ROI_SIZE, ROI_SIZE), (50, 50, 50), 2)
#             cv2.putText(frame, "SWITCH", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
#             cv2.putText(frame, "MODE", (25, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

#             mode_text = "MOUSE MODE" if mode_flag.value == 0 else "ISL MODE"
#             color = (0, 255, 0) if mode_flag.value == 0 else (0, 0, 255)
            
#             cv2.rectangle(frame, (160, 0), (640, 40), (0,0,0), -1)
#             cv2.putText(frame, f"{mode_text}", (180, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

#             if not isl_result_queue.empty():
#                 word = isl_result_queue.get()
#                 cv2.putText(frame, f"ISL: {word}", (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

#             cv2.imshow("Jarvis Vision Feed", frame)

#             if cv2.waitKey(1) & 0xFF == 27: break # ESC to quit
#             frame_ready.clear()

#     except KeyboardInterrupt:
#         pass
#     finally:
#         stop_event.set()
#         p_hci.join()
#         p_isl.join()
#         cap.release()
#         cv2.destroyAllWindows()
#         shm.close()
#         shm.unlink()

# if __name__ == "__main__":
#     mp.set_start_method('spawn', force=True)
#     main()
