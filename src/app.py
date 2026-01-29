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
from controllers.HCI_Controller import run_hci
from controllers.ISL_Controller import run_isl

def main():
    WIDTH, HEIGHT = 1280, 720
    CHANNELS = 3
    FRAME_SHAPE = (HEIGHT, WIDTH, CHANNELS)
    FRAME_SIZE = int(np.prod(FRAME_SHAPE))
    FRAME_REDUCTION = 100 # Match this with HCI Controller

    print(f"[SYSTEM] Initializing Phase 3 Modular System...")

    try:
        shm = shared_memory.SharedMemory(create=True, size=FRAME_SIZE)
    except FileExistsError:
        temp = shared_memory.SharedMemory(name=None, size=FRAME_SIZE) 
        temp.unlink()
        shm = shared_memory.SharedMemory(create=True, size=FRAME_SIZE)

    frame_ready = mp.Event()
    stop_event = mp.Event()
    isl_result_queue = mp.Queue()
    mode_flag = mp.Value('i', 0) 

    p_hci = mp.Process(target=run_hci, args=(shm.name, FRAME_SHAPE, frame_ready, stop_event, mode_flag))
    p_isl = mp.Process(target=run_isl, args=(shm.name, FRAME_SHAPE, frame_ready, stop_event, isl_result_queue, mode_flag))

    p_hci.start()
    p_isl.start()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened(): cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    shared_frame = np.ndarray(FRAME_SHAPE, dtype=np.uint8, buffer=shm.buf)
    
    current_mode_text = "MOUSE MODE"

    try:
        while True:
            ret, frame = cap.read()
            if not ret: continue
            frame = cv2.flip(frame, 1)

            # Write to Shared Memory
            np.copyto(shared_frame, frame)
            frame_ready.set()
            
            # --- UI VISUALS ---
            color = (0, 255, 0) if mode_flag.value == 0 else (0, 0, 255)
            
            # 1. Mode Text
            cv2.putText(frame, f"MODE: {current_mode_text} (Press Q)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # 2. Active Zone Box (Only in Mouse Mode)
            if mode_flag.value == 0:
                cv2.rectangle(frame, (FRAME_REDUCTION, FRAME_REDUCTION), 
                              (WIDTH - FRAME_REDUCTION, HEIGHT - FRAME_REDUCTION), 
                              (255, 0, 255), 2)

            # 3. ISL Text
            if not isl_result_queue.empty():
                word = isl_result_queue.get()
                cv2.putText(frame, f"ISL: {word}", (10, 650), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)

            cv2.imshow("Jarvis Master Feed", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                with mode_flag.get_lock():
                    mode_flag.value = 1 - mode_flag.value
                    current_mode_text = "ISL MODE" if mode_flag.value == 1 else "MOUSE MODE"
                    print(f"[SYSTEM] Switched to {current_mode_text}")
            
            if key == 27: break
            
            time.sleep(0.01) 
            frame_ready.clear()

    except KeyboardInterrupt: pass
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