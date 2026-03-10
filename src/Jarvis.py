# 2.5
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
# GUI IMPORT
# ═══════════════════════════════════════════════════════════════════════════
try:
    import app
except ImportError:
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# STATE
# ═══════════════════════════════════════════════════════════════════════════
vision_process = None
is_awake = True
voice_failure_count = 0  # To track failed listen attempts

def reply(text):
    print(f"[JARVIS] {text}")
    try: app.ChatBot.addAppMsg(text)
    except: pass
    if AUDIO_AVAILABLE:
        try:
            engine.say(text)
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
            print("[LISTENING]...")
            audio = r.listen(source, phrase_time_limit=5)
            query = r.recognize_google(audio, language='en-in')
            
            # Success! Reset failure count
            if voice_failure_count > 0:
                voice_failure_count = 0
            return query.lower()
            
    except (sr.UnknownValueError, sr.RequestError):
        # Voice Failed
        voice_failure_count += 1
        print(f"[VOICE] Failure Count: {voice_failure_count}")
        
        # TRIGGER TEXT MODE FALLBACK
        if voice_failure_count >= 3:
            print("[SYSTEM] Switching to TEXT MODE due to audio failures.")
            try:
                # Call JS function to show input box
                app.eel.toggleInput(True)
                reply("Voice unreliable. Text mode enabled.")
                voice_failure_count = 0 # Reset so we don't spam
            except: pass
        return None
    except Exception:
        return None

def process_command(query):
    global vision_process, is_awake
    query = query.lower().strip()
    
    if "start" in query or "launch" in query:
        # Manual start if needed, but we auto-start now
        if vision_process is None:
            vision_process = subprocess.Popen([sys.executable, 'src/vision_backend.py'])
            reply("Vision System Active.")
        else:
            reply("Already running.")

    elif "stop" in query:
        if vision_process:
            vision_process.terminate()
            vision_process = None
        if platform.system() == "Darwin":
            os.system("pkill -f vision_backend.py")
        reply("System Stopped.")

    elif "exit" in query:
        if vision_process: vision_process.terminate()
        if platform.system() == "Darwin": os.system("pkill -f vision_backend.py")
        os._exit(0)

    else:
        # Pass other commands (time/date) here
        pass

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # 1. Start GUI
    gui_thread = threading.Thread(target=app.ChatBot.start)
    gui_thread.daemon = True
    gui_thread.start()
    
    # 2. Wait for GUI
    while not app.ChatBot.started:
        time.sleep(0.5)
    
    # 3. AUTO-LAUNCH VISION BACKEND (The Fix)
    reply("Jarvis Online. Initializing Vision...")
    vision_process = subprocess.Popen([sys.executable, 'src/vision_backend.py'])
    
    # 4. Command Loop
    while True:
        query = None
        
        # Check Text Input
        if app.ChatBot.isUserInput():
            query = app.ChatBot.popUserInput()
            app.ChatBot.addUserMsg(query)
            # Reset failure count if user types successfully
            voice_failure_count = 0 
        
        # Check Voice Input
        elif AUDIO_AVAILABLE and is_awake:
            query = listen()
            if query: app.ChatBot.addUserMsg(query)
        
        if query: process_command(query)
        time.sleep(0.1)



# #!updated phase 2.4 jarvis
# #!/usr/bin/env python3
# """
# ═══════════════════════════════════════════════════════════════════════════
# JARVIS - MODULAR VOICE & GESTURE ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════════════════

# PURPOSE:
# This is the MAIN ENTRY POINT for the Jarvis-EcoSign system. It acts as the
# "Command Center" that:
# 1. Launches the GUI (using eel)
# 2. Listens for voice or text input
# 3. Launches/stops the vision system (vision_backend.py)

# ARCHITECTURE:
#     User Input (Voice/Text)
#            ↓
#     Jarvis.py (This File)
#            ↓
#     subprocess.Popen('vision_backend.py')
#            ↓
#     Multiprocessing Hub
#     ├─ HCI_Controller.py (Mouse)
#     └─ ISL_Controller.py (Sign Language)

# SAFE IMPORTS:
# All audio-related imports are wrapped in try/except blocks. If PyAudio or
# pyttsx3 fails to load, the system falls back to "TEXT MODE" where you can
# type commands instead of speaking them.

# AUTHOR: Nittaany (Satyam C)
# PLATFORM: macOS Silicon (M1/M2)
# PHASE: 2.3 (Modularization Complete)
# ═══════════════════════════════════════════════════════════════════════════
# """

# import sys
# import os
# import subprocess
# import time
# import datetime
# import threading
# import platform

# # ═══════════════════════════════════════════════════════════════════════════
# # SAFE AUDIO IMPORTS (Won't crash if drivers are broken)
# # ═══════════════════════════════════════════════════════════════════════════
# AUDIO_AVAILABLE = False

# try:
#     import pyttsx3
#     import speech_recognition as sr
    
#     # Initialize Text-to-Speech Engine
#     engine = pyttsx3.init()
    
#     # Mac-specific voice settings
#     if platform.system() == "Darwin":
#         engine.setProperty('rate', 190)  # Slower speech rate for clarity
    
#     AUDIO_AVAILABLE = True
#     print("[JARVIS] ✅ Audio drivers loaded successfully")
    
# except ImportError as e:
#     print(f"[JARVIS] ⚠️  Audio Warning: {e}")
#     print("[JARVIS] Running in TEXT MODE (type commands instead of speaking)")
    
# except Exception as e:
#     print(f"[JARVIS] ⚠️  Audio initialization failed: {e}")
#     print("[JARVIS] Running in TEXT MODE")

# # ═══════════════════════════════════════════════════════════════════════════
# # GUI MODULE IMPORT
# # ═══════════════════════════════════════════════════════════════════════════
# try:
#     import app
#     print("[JARVIS] ✅ GUI module loaded")
# except Exception as e:
#     print(f"[JARVIS] ❌ FATAL: Could not load GUI module: {e}")
#     sys.exit(1)

# # ═══════════════════════════════════════════════════════════════════════════
# # GLOBAL STATE VARIABLES
# # ═══════════════════════════════════════════════════════════════════════════
# vision_process = None  # Subprocess handle for vision_backend.py
# is_awake = True        # Bot sleep/wake state

# # ═══════════════════════════════════════════════════════════════════════════
# # HELPER FUNCTIONS
# # ═══════════════════════════════════════════════════════════════════════════

# def reply(text):
#     """
#     Output to both Console and GUI, optionally with voice.
    
#     This is your main output function. It:
#     1. Prints to console (for debugging)
#     2. Sends message to the Eel GUI (user sees it in browser)
#     3. Speaks it aloud (if audio is available)
#     """
#     print(f"[JARVIS] {text}")
    
#     # Send to GUI
#     try:
#         app.ChatBot.addAppMsg(text)
#     except:
#         pass
    
#     # Text-to-Speech (if available)
#     if AUDIO_AVAILABLE:
#         try:
#             engine.say(text)
#             engine.runAndWait()
#         except:
#             pass

# def listen():
#     """
#     Captures voice input using Google Speech Recognition.
    
#     Returns:
#         str: Recognized text (lowercase), or None if failed
    
#     Note: This requires internet connection (Google API)
#     """
#     if not AUDIO_AVAILABLE:
#         return None
    
#     try:
#         r = sr.Recognizer()
#         with sr.Microphone() as source:
#             r.pause_threshold = 0.8  # Silence duration before ending phrase
#             r.adjust_for_ambient_noise(source, duration=0.5)
            
#             print("[LISTENING]...")
#             audio = r.listen(source, phrase_time_limit=5)
            
#             # Use Google's free API
#             query = r.recognize_google(audio, language='en-in')
#             return query.lower()
            
#     except sr.UnknownValueError:
#         # Google couldn't understand the audio
#         return None
#     except sr.RequestError:
#         reply("Internet connection required for voice recognition")
#         return None
#     except Exception as e:
#         print(f"[LISTEN ERROR] {e}")
#         return None

# # ═══════════════════════════════════════════════════════════════════════════
# # COMMAND PROCESSOR
# # ═══════════════════════════════════════════════════════════════════════════

# def process_command(query):
#     """
#     Parses user input and executes the appropriate action.
    
#     This is the "brain" of Jarvis. It interprets what the user said/typed
#     and calls the appropriate system functions.
    
#     Args:
#         query (str): User's command (lowercase)
#     """
#     global vision_process, is_awake
    
#     query = query.lower().strip()
    
#     # ═══════════════════════════════════════════════════════════════
#     # CATEGORY 1: VISION SYSTEM CONTROL
#     # ═══════════════════════════════════════════════════════════════
    
#     if "start" in query or "launch" in query:
#         """Launch the modular vision system"""
#         reply("Initializing Modular Vision System...")
        
#         # Check if already running
#         if vision_process is not None and vision_process.poll() is None:
#             reply("System is already running.")
#             return
        
#         # Launch vision_backend.py as a separate process
#         try:
#             vision_process = subprocess.Popen([
#                 sys.executable, 
#                 'src/vision_backend.py'
#             ])
#             reply("Vision System Active. Press Q to switch modes.")
#         except Exception as e:
#             reply(f"Failed to launch vision system: {e}")
    
#     elif "stop" in query or "terminate" in query:
#         """Stop the vision system"""
#         reply("Stopping Vision System...")
        
#         if vision_process:
#             vision_process.terminate()
#             vision_process.wait()  # Wait for clean shutdown
#             vision_process = None
        
#         # Backup kill (macOS specific)
#         if platform.system() == "Darwin":
#             os.system("pkill -f vision_backend.py")
        
#         reply("System Offline.")
    
#     # ═══════════════════════════════════════════════════════════════
#     # CATEGORY 2: BASIC UTILITIES
#     # ═══════════════════════════════════════════════════════════════
    
#     elif "time" in query:
#         """Tell current time"""
#         current_time = datetime.datetime.now().strftime("%H:%M")
#         reply(f"It is {current_time}")
    
#     elif "date" in query:
#         """Tell current date"""
#         current_date = datetime.datetime.now().strftime("%B %d, %Y")
#         reply(f"Today is {current_date}")
    
#     # ═══════════════════════════════════════════════════════════════
#     # CATEGORY 3: SYSTEM STATE CONTROL
#     # ═══════════════════════════════════════════════════════════════
    
#     elif "wake up" in query:
#         """Activate bot"""
#         is_awake = True
#         reply("Online and ready.")
    
#     elif "sleep" in query or "standby" in query:
#         """Deactivate bot (stops listening)"""
#         is_awake = False
#         reply("Standing by. Say 'wake up' to resume.")
    
#     elif "exit" in query or "bye" in query or "goodbye" in query:
#         """Shutdown entire system"""
#         reply("Shutting down. Goodbye.")
        
#         # Clean shutdown of vision system
#         if vision_process:
#             vision_process.terminate()
        
#         # Force kill any remaining processes
#         if platform.system() == "Darwin":
#             os.system("pkill -f vision_backend.py")
        
#         # Exit Python
#         os._exit(0)
    
#     # ═══════════════════════════════════════════════════════════════
#     # CATEGORY 4: HELP & INFO
#     # ═══════════════════════════════════════════════════════════════
    
#     elif "help" in query:
#         """Show available commands"""
#         help_text = """
#         Available Commands:
#         - "start" / "launch" → Activate vision system
#         - "stop" / "terminate" → Deactivate vision system
#         - "time" → Tell current time
#         - "date" → Tell current date
#         - "sleep" → Enter standby mode
#         - "wake up" → Resume from standby
#         - "exit" / "bye" → Shutdown system
#         """
#         reply(help_text)
    
#     else:
#         """Unknown command"""
#         reply("I didn't understand that. Say 'help' for available commands.")

# # ═══════════════════════════════════════════════════════════════════════════
# # MAIN EXECUTION FLOW
# # ═══════════════════════════════════════════════════════════════════════════

# if __name__ == "__main__":
#     print("═══════════════════════════════════════════════════")
#     print("   JARVIS - MODULAR ARCHITECTURE v2.3")
#     print("═══════════════════════════════════════════════════")
#     print()
    
#     # Status Report
#     if AUDIO_AVAILABLE:
#         print("✅ Voice Input: ENABLED")
#         print("✅ Text-to-Speech: ENABLED")
#     else:
#         print("⚠️  Voice Input: DISABLED (running in TEXT MODE)")
#         print("    Type your commands in the GUI instead.")
#     print()
    
#     # ═══════════════════════════════════════════════════════════════
#     # STEP 1: Launch GUI in Background Thread
#     # ═══════════════════════════════════════════════════════════════
#     gui_thread = threading.Thread(target=app.ChatBot.start)
#     gui_thread.daemon = True  # Thread dies when main process dies
#     gui_thread.start()
    
#     # ═══════════════════════════════════════════════════════════════
#     # STEP 2: Wait for GUI to Initialize
#     # ═══════════════════════════════════════════════════════════════
#     print("[INIT] Waiting for GUI to load...")
#     timeout = 30  # seconds
#     start_time = time.time()
    
#     while not app.ChatBot.started:
#         if time.time() - start_time > timeout:
#             print("[ERROR] GUI failed to start within 30 seconds")
#             sys.exit(1)
#         time.sleep(0.5)
    
#     print("[INIT] ✅ GUI loaded successfully")
#     print()
    
#     # ═══════════════════════════════════════════════════════════════
#     # STEP 3: Initial Greeting
#     # ═══════════════════════════════════════════════════════════════
#     reply("System Initialized. Ready for commands.")
#     reply("Say 'start' to launch the vision system.")
    
#     # ═══════════════════════════════════════════════════════════════
#     # STEP 4: Main Command Loop
#     # ═══════════════════════════════════════════════════════════════
#     print("[READY] Entering command loop...")
#     print("        Type in GUI or speak (if audio enabled)")
#     print()
    
#     while True:
#         query = None
        
#         # PRIORITY A: Check for GUI Text Input
#         if app.ChatBot.isUserInput():
#             query = app.ChatBot.popUserInput()
#             app.ChatBot.addUserMsg(query)  # Echo back to GUI
#             print(f"[INPUT: TEXT] {query}")
        
#         # PRIORITY B: Check for Voice Input (if awake and audio available)
#         elif AUDIO_AVAILABLE and is_awake:
#             try:
#                 query = listen()
#                 if query:
#                     app.ChatBot.addUserMsg(query)  # Show in GUI
#                     print(f"[INPUT: VOICE] {query}")
#             except Exception as e:
#                 print(f"[VOICE ERROR] {e}")
        
#         # EXECUTE COMMAND
#         if query:
#             try:
#                 process_command(query)
#             except Exception as e:
#                 print(f"[COMMAND ERROR] {e}")
#                 reply("An error occurred while processing that command.")
        
#         # Small delay to prevent CPU spinning
#         time.sleep(0.1)