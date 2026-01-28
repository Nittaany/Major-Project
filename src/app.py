# import eel
# import os
# from queue import Queue

# class ChatBot:

#     started = False
#     userinputQueue = Queue()

#     def isUserInput():
#         return not ChatBot.userinputQueue.empty()

#     def popUserInput():
#         return ChatBot.userinputQueue.get()

#     def close_callback(route, websockets):
#         exit()

#     @eel.expose
#     def getUserInput(msg):
#         ChatBot.userinputQueue.put(msg)
#         print(msg)
    
#     def close():
#         ChatBot.started = False
    
#     def addUserMsg(msg):
#         eel.addUserMsg(msg)
    
#     def addAppMsg(msg):
#         eel.addAppMsg(msg)

#     def start():
#         path = os.path.dirname(os.path.abspath(__file__))
#         eel.init(path + r'/web', allowed_extensions=['.js', '.html'])
        
#         # Define the launch options common to both modes
#         launch_options = {
#             'host': 'localhost',
#             'port': 27005,
#             'block': False,
#             'size': (350, 480),
#             'position': (10, 100),
#             'disable_cache': True,
#             'close_callback': ChatBot.close_callback
#         }

#         try:
#             print("Attempting to launch Firefox...")
#             # TRY 1: Open in Firefox
#             eel.start('index.html', mode='firefox', **launch_options)
#             ChatBot.started = True
#         except Exception as e:
#             print(f"Firefox failed ({e}). Falling back to Default Browser.")
#             try:
#                 # TRY 2: Fallback to Default (Safari/System Default)
#                 eel.start('index.html', mode='default', **launch_options)
#                 ChatBot.started = True
#             except Exception as e2:
#                 print(f"FATAL: Could not launch any browser. {e2}")
#                 ChatBot.started = False

#         # Keep the main thread alive while the GUI is running
#         while ChatBot.started:
#             try:
#                 eel.sleep(1.0)
#             except:
#                 break


#! modulation

import cv2
import numpy as np
import multiprocessing as mp
from multiprocessing import shared_memory
import time
import platform
import sys

# Import Controllers
from controllers.HCI_Controller import run_hci
from controllers.ISL_Controller import run_isl

def main():
    WIDTH, HEIGHT = 1280, 720
    CHANNELS = 3
    FRAME_SHAPE = (HEIGHT, WIDTH, CHANNELS)
    FRAME_SIZE = int(np.prod(FRAME_SHAPE))
    DTYPE = np.uint8

    print(f"[SYSTEM] Initializing Phase 3 Modular System...")

    # 1. SHARED MEMORY
    try:
        shm = shared_memory.SharedMemory(create=True, size=FRAME_SIZE)
    except FileExistsError:
        print("[ERROR] Memory exists. Unlinking...")
        # Emergency cleanup if previous run crashed
        temp = shared_memory.SharedMemory(name=None, size=FRAME_SIZE) # Try to find it? No, just warn.
        print("Please run this command in terminal: rm /dev/shm/*") 
        return

    # 2. SYNC
    frame_ready = mp.Event()
    stop_event = mp.Event()
    isl_result_queue = mp.Queue()

    # 3. SPAWN PROCESSES
    p_hci = mp.Process(target=run_hci, args=(shm.name, FRAME_SHAPE, frame_ready, stop_event))
    p_isl = mp.Process(target=run_isl, args=(shm.name, FRAME_SHAPE, frame_ready, stop_event, isl_result_queue))

    p_hci.start()
    p_isl.start()

    # 4. CAMERA LOOP
    cap = cv2.VideoCapture(0)
    # Mac Camera Fix
    if not cap.isOpened():
        cap = cv2.VideoCapture(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    shared_frame = np.ndarray(FRAME_SHAPE, dtype=DTYPE, buffer=shm.buf)

    print("[SYSTEM] Running. Press 'q' to exit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)

            # Write to Shared Memory
            np.copyto(shared_frame, frame)
            
            # Signal Children
            frame_ready.set() 
            # We DO NOT clear() immediately. This fixes the deadlock.
            
            # UI Feedback
            cv2.imshow("Jarvis Master Feed", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # FPS Control (Crucial for Sync)
            time.sleep(0.01) 
            frame_ready.clear() # Clear after sleep ensures children had time to see it.

    except KeyboardInterrupt:
        print("[SYSTEM] Interrupt")

    finally:
        print("[SYSTEM] Stopping...")
        stop_event.set()
        p_hci.join()
        p_isl.join()
        cap.release()
        cv2.destroyAllWindows()
        shm.close()
        shm.unlink()
        print("[SYSTEM] Cleanup Done.")

if __name__ == "__main__":
    mp.set_start_method('spawn', force=True)
    main()