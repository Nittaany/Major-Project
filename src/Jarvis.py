#* 2.5/3.3 Hardened Core
import sys
import os
import subprocess
import time
import datetime
import threading
import platform
import queue

# ═══════════════════════════════════════════════════════════════════════════
# SAFE AUDIO IMPORTS
# ═══════════════════════════════════════════════════════════════════════════
AUDIO_AVAILABLE = False
try:
    import pyttsx3
    import speech_recognition as sr
    engine = pyttsx3.init()
    if platform.system() == "Darwin":
        engine.setProperty('rate', 190)
    AUDIO_AVAILABLE = True
except Exception:
    pass

# ═══════════════════════════════════════════════════════════════════════════
# GUI IMPORT & PATHS
# ═══════════════════════════════════════════════════════════════════════════
try:
    import app
except ImportError:
    sys.exit(1)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISL_BRIDGE_PATH = os.path.join(PROJECT_ROOT, "data", "isl_live.txt")
VISION_BACKEND_PATH = os.path.join(PROJECT_ROOT, "src", "vision_backend.py") # <--- SECURE PATH

# ═══════════════════════════════════════════════════════════════════════════
# STATE & QUEUES
# ═══════════════════════════════════════════════════════════════════════════
vision_process = None
is_awake = True
running_flag = True # <--- GRACEFUL SHUTDOWN FLAG
voice_failure_count = 0  

isl_message_queue = queue.Queue() 
voice_command_queue = queue.Queue()

def reply(text):
    print(f"[JARVIS] {text}")
    try: app.ChatBot.addAppMsg(text)
    except: pass
    if AUDIO_AVAILABLE:
        try:
            spoken_text = text.replace("<b>", "").replace("</b>", "").replace("<br>", " ")
            engine.say(spoken_text)
            engine.runAndWait()
        except: pass

def listen():
    global voice_failure_count
    if not AUDIO_AVAILABLE: return None
    
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.pause_threshold = 0.8
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, phrase_time_limit=5)
            query = r.recognize_google(audio, language='en-in')
            
            if voice_failure_count > 0: voice_failure_count = 0
            return query.lower()
            
    except (sr.UnknownValueError, sr.RequestError):
        voice_failure_count += 1
        if voice_failure_count >= 3:
            voice_failure_count = 0 
            return "_SYSTEM_TEXT_FALLBACK_"
        return None
    except Exception:
        return None

# ═══════════════════════════════════════════════════════════════════════════
# BACKGROUND THREADS
# ═══════════════════════════════════════════════════════════════════════════
def voice_worker():
    while running_flag: # <--- SAFE LOOP
        if AUDIO_AVAILABLE and is_awake:
            query = listen()
            if query:
                voice_command_queue.put(query)
        else:
            time.sleep(0.5)

def watch_isl_bridge():
    last_isl_mod_time = 0
    if os.path.exists(ISL_BRIDGE_PATH):
        last_isl_mod_time = os.path.getmtime(ISL_BRIDGE_PATH)
    
    while running_flag: # <--- SAFE LOOP
        try:
            if os.path.exists(ISL_BRIDGE_PATH):
                current_mod_time = os.path.getmtime(ISL_BRIDGE_PATH)
                if current_mod_time > last_isl_mod_time:
                    last_isl_mod_time = current_mod_time
                    with open(ISL_BRIDGE_PATH, 'r') as f:
                        isl_word = f.read().strip()
                    
                    if isl_word and isl_word.lower() not in ["idle", "unknown"]:
                        isl_message_queue.put(isl_word)
        except Exception:
            pass
        time.sleep(0.1)

# ═══════════════════════════════════════════════════════════════════════════
# COMMAND PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════
def process_command(query):
    global vision_process, is_awake, running_flag
    query = query.lower().strip()
    
    if "start" in query or "launch" in query:
        if vision_process is None:
            vision_process = subprocess.Popen([sys.executable, VISION_BACKEND_PATH]) # <--- SECURE LAUNCH
            reply("Vision System Active.")
        else:
            reply("Already running.")

    elif "stop" in query or "terminate" in query:
        if vision_process:
            vision_process.terminate()
            vision_process = None
        if platform.system() == "Darwin":
            os.system("pkill -f vision_backend.py")
        reply("System Stopped.")

    elif "time" in query:
        current_time = datetime.datetime.now().strftime("%I:%M %p")
        reply(f"It is {current_time}")
    
    elif "date" in query:
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        reply(f"Today is {current_date}")

    elif "sleep" in query or "standby" in query:
        is_awake = False
        reply("Standing by. Say 'wake up' to resume.")
        
    elif "wake up" in query:
        is_awake = True
        reply("Online and ready.")

    elif "exit" in query or "bye" in query:
        running_flag = False # <--- TRIGGER CLEAN SHUTDOWN
        if vision_process: vision_process.terminate()
        if platform.system() == "Darwin": os.system("pkill -f vision_backend.py")
        reply("Shutting down. Goodbye.")
        time.sleep(1) # Let UI update
        os._exit(0)

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EVENT LOOP
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    gui_thread = threading.Thread(target=app.ChatBot.start)
    gui_thread.daemon = True
    gui_thread.start()
    
    while not app.ChatBot.started:
        time.sleep(0.5)
    
    reply("System Initialized. I am Jarvis, how may I help you?")
    
    # Auto-launch vision with secure path
    vision_process = subprocess.Popen([sys.executable, VISION_BACKEND_PATH])
    
    watcher_thread = threading.Thread(target=watch_isl_bridge)
    watcher_thread.daemon = True
    watcher_thread.start()
    
    if AUDIO_AVAILABLE:
        voice_thread = threading.Thread(target=voice_worker)
        voice_thread.daemon = True
        voice_thread.start()
    
    while running_flag: # <--- SAFE LOOP
        while not isl_message_queue.empty():
            word = isl_message_queue.get()
            reply(f"ISL Translation: <b>{word.upper()}</b>")
            
        if app.ChatBot.isUserInput():
            query = app.ChatBot.popUserInput()
            app.ChatBot.addUserMsg(query)
            voice_failure_count = 0 
            process_command(query)
            
        while not voice_command_queue.empty():
            query = voice_command_queue.get()
            if query == "_SYSTEM_TEXT_FALLBACK_":
                try: app.eel.toggleInput(True)
                except: pass
                reply("Voice unreliable. Text mode enabled.")
            else:
                app.ChatBot.addUserMsg(query)
                process_command(query)
        
        time.sleep(0.1)
# 2.5
# import sys
# import os
# import subprocess
# import time
# import datetime
# import threading
# import platform
# import queue

# # ═══════════════════════════════════════════════════════════════════════════
# # SAFE AUDIO IMPORTS
# # ═══════════════════════════════════════════════════════════════════════════
# AUDIO_AVAILABLE = False
# try:
#     import pyttsx3
#     import speech_recognition as sr
#     engine = pyttsx3.init()
#     if platform.system() == "Darwin":
#         engine.setProperty('rate', 190)
#     AUDIO_AVAILABLE = True
# except Exception:
#     pass

# # ═══════════════════════════════════════════════════════════════════════════
# # GUI IMPORT
# # ═══════════════════════════════════════════════════════════════════════════
# try:
#     import app
# except ImportError:
#     sys.exit(1)

# # ═══════════════════════════════════════════════════════════════════════════
# # STATE
# # ═══════════════════════════════════════════════════════════════════════════
# vision_process = None
# is_awake = True
# voice_failure_count = 0  # To track failed listen attempts

# def reply(text):
#     print(f"[JARVIS] {text}")
#     try: app.ChatBot.addAppMsg(text)
#     except: pass
#     if AUDIO_AVAILABLE:
#         try:
#             engine.say(text)
#             engine.runAndWait()
#         except: pass

# def listen():
#     global voice_failure_count
#     if not AUDIO_AVAILABLE: return None
    
#     try:
#         r = sr.Recognizer()
#         with sr.Microphone() as source:
#             r.pause_threshold = 0.8
#             r.adjust_for_ambient_noise(source, duration=0.5)
#             print("[LISTENING]...")
#             audio = r.listen(source, phrase_time_limit=5)
#             query = r.recognize_google(audio, language='en-in')
            
#             # Success! Reset failure count
#             if voice_failure_count > 0:
#                 voice_failure_count = 0
#             return query.lower()
            
#     except (sr.UnknownValueError, sr.RequestError):
#         # Voice Failed
#         voice_failure_count += 1
#         print(f"[VOICE] Failure Count: {voice_failure_count}")
        
#         # TRIGGER TEXT MODE FALLBACK
#         if voice_failure_count >= 3:
#             print("[SYSTEM] Switching to TEXT MODE due to audio failures.")
#             try:
#                 # Call JS function to show input box
#                 app.eel.toggleInput(True)
#                 reply("Voice unreliable. Text mode enabled.")
#                 voice_failure_count = 0 # Reset so we don't spam
#             except: pass
#         return None
#     except Exception:
#         return None

# def process_command(query):
#     global vision_process, is_awake
#     query = query.lower().strip()
    
#     if "start" in query or "launch" in query:
#         # Manual start if needed, but we auto-start now
#         if vision_process is None:
#             vision_process = subprocess.Popen([sys.executable, 'src/vision_backend.py'])
#             reply("Vision System Active.")
#         else:
#             reply("Already running.")

#     elif "stop" in query:
#         if vision_process:
#             vision_process.terminate()
#             vision_process = None
#         if platform.system() == "Darwin":
#             os.system("pkill -f vision_backend.py")
#         reply("System Stopped.")

#     elif "exit" in query:
#         if vision_process: vision_process.terminate()
#         if platform.system() == "Darwin": os.system("pkill -f vision_backend.py")
#         os._exit(0)

#     else:
#         # Pass other commands (time/date) here
#         pass

# # ═══════════════════════════════════════════════════════════════════════════
# # MAIN
# # ═══════════════════════════════════════════════════════════════════════════
# if __name__ == "__main__":
#     # 1. Start GUI
#     gui_thread = threading.Thread(target=app.ChatBot.start)
#     gui_thread.daemon = True
#     gui_thread.start()
    
#     # 2. Wait for GUI
#     while not app.ChatBot.started:
#         time.sleep(0.5)
    
#     # 3. AUTO-LAUNCH VISION BACKEND (The Fix)
#     reply("Jarvis Online. Initializing Vision...")
#     vision_process = subprocess.Popen([sys.executable, 'src/vision_backend.py'])
    
#     # 4. Command Loop
#     while True:
#         query = None
        
#         # Check Text Input
#         if app.ChatBot.isUserInput():
#             query = app.ChatBot.popUserInput()
#             app.ChatBot.addUserMsg(query)
#             # Reset failure count if user types successfully
#             voice_failure_count = 0 
        
#         # Check Voice Input
#         elif AUDIO_AVAILABLE and is_awake:
#             query = listen()
#             if query: app.ChatBot.addUserMsg(query)
        
#         if query: process_command(query)
#         time.sleep(0.1)



