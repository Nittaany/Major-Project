import cv2
import numpy as np
import multiprocessing as mp
from multiprocessing import shared_memory
import time
import sys
import os

# --- IMPORT YOUR EXISTING CONTROLLERS ---
# This uses the HCI_Controller.py you already have!
from controllers.HCI_Controller import run_hci
from controllers.ISL_Controller import run_isl

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
    mode_flag = mp.Value('i', 0)  # 0 = Mouse, 1 = ISL

    # 3. START YOUR CONTROLLERS
    p_hci = mp.Process(target=run_hci, args=('jarvis_shm', FRAME_SHAPE, frame_ready, stop_event, mode_flag))
    p_isl = mp.Process(target=run_isl, args=('jarvis_shm', FRAME_SHAPE, frame_ready, stop_event, isl_result_queue, mode_flag))
    
    p_hci.start()
    p_isl.start()

    # 4. START CAMERA
    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): cap = cv2.VideoCapture(1)
    
    shared_frame = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)
    
    print("[BACKEND] Vision System Online.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret: continue
            
            # Standardize & Write to Memory
            frame = cv2.resize(frame, (WIDTH, HEIGHT))
            frame = cv2.flip(frame, 1)
            np.copyto(shared_frame, frame)
            frame_ready.set()

            # --- PREVIEW WINDOW ---
            mode_text = "MOUSE MODE" if mode_flag.value == 0 else "ISL MODE"
            color = (0, 255, 0) if mode_flag.value == 0 else (0, 0, 255)
            
            cv2.rectangle(frame, (0,0), (640, 40), (0,0,0), -1)
            cv2.putText(frame, f"{mode_text} (Press Q)", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            # Display ISL Text if available
            if not isl_result_queue.empty():
                word = isl_result_queue.get()
                cv2.putText(frame, f"ISL: {word}", (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

            cv2.imshow("Jarvis Vision Feed", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                with mode_flag.get_lock():
                    mode_flag.value = 1 - mode_flag.value
            if key == 27: break
            
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