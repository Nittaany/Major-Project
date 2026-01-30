# import pyttsx3
# import speech_recognition as sr
# from datetime import date
# import time
# import webbrowser
# import datetime
# from pynput.keyboard import Key, Controller
# import pyautogui
# import sys
# import os
# from os import listdir
# from os.path import isfile, join
# import smtplib
# import wikipedia
# import Gesture_Controller
# #import Gesture_Controller_Gloved as Gesture_Controller
# import app
# from threading import Thread


# # -------------Object Initialization---------------
# today = date.today()
# r = sr.Recognizer()
# keyboard = Controller()
# engine = pyttsx3.init('sapi5')
# engine = pyttsx3.init()
# voices = engine.getProperty('voices')
# engine.setProperty('voice', voices[0].id)

# # ----------------Variables------------------------
# file_exp_status = False
# files =[]
# path = ''
# is_awake = True  #Bot status

# # ------------------Functions----------------------
# def reply(audio):
#     app.ChatBot.addAppMsg(audio)

#     print(audio)
#     engine.say(audio)
#     engine.runAndWait()


# def wish():
#     hour = int(datetime.datetime.now().hour)

#     if hour>=0 and hour<12:
#         reply("Good Morning!")
#     elif hour>=12 and hour<18:
#         reply("Good Afternoon!")   
#     else:
#         reply("Good Evening!")  
        
#     reply("I am Proton, how may I help you?")

# # Set Microphone parameters
# with sr.Microphone() as source:
#         r.energy_threshold = 500 
#         r.dynamic_energy_threshold = False

# # Audio to String
# def record_audio():
#     with sr.Microphone() as source:
#         r.pause_threshold = 0.8
#         voice_data = ''
#         audio = r.listen(source, phrase_time_limit=5)

#         try:
#             voice_data = r.recognize_google(audio)
#         except sr.RequestError:
#             reply('Sorry my Service is down. Plz check your Internet connection')
#         except sr.UnknownValueError:
#             print('cant recognize')
#             pass
#         return voice_data.lower()


# # Executes Commands (input: string)
# def respond(voice_data):
#     global file_exp_status, files, is_awake, path
#     print(voice_data)
#     voice_data.replace('proton','')
#     app.eel.addUserMsg(voice_data)

#     if is_awake==False:
#         if 'wake up' in voice_data:
#             is_awake = True
#             wish()

#     # STATIC CONTROLS
#     elif 'hello' in voice_data:
#         wish()

#     elif 'what is your name' in voice_data:
#         reply('My name is Proton!')

#     elif 'date' in voice_data:
#         reply(today.strftime("%B %d, %Y"))

#     elif 'time' in voice_data:
#         reply(str(datetime.datetime.now()).split(" ")[1].split('.')[0])

#     elif 'search' in voice_data:
#         reply('Searching for ' + voice_data.split('search')[1])
#         url = 'https://google.com/search?q=' + voice_data.split('search')[1]
#         try:
#             webbrowser.get().open(url)
#             reply('This is what I found Sir')
#         except:
#             reply('Please check your Internet')

#     elif 'location' in voice_data:
#         reply('Which place are you looking for ?')
#         temp_audio = record_audio()
#         app.eel.addUserMsg(temp_audio)
#         reply('Locating...')
#         url = 'https://google.nl/maps/place/' + temp_audio + '/&amp;'
#         try:
#             webbrowser.get().open(url)
#             reply('This is what I found Sir')
#         except:
#             reply('Please check your Internet')

#     elif ('bye' in voice_data) or ('by' in voice_data):
#         reply("Good bye Sir! Have a nice day.")
#         is_awake = False

#     elif ('exit' in voice_data) or ('terminate' in voice_data):
#         if Gesture_Controller.GestureController.gc_mode:
#             Gesture_Controller.GestureController.gc_mode = 0
#         app.ChatBot.close()
#         #sys.exit() always raises SystemExit, Handle it in main loop
#         sys.exit()
        
    
#     # DYNAMIC CONTROLS
#     elif 'launch gesture recognition' in voice_data:
#         if Gesture_Controller.GestureController.gc_mode:
#             reply('Gesture recognition is already active')
#         else:
#             gc = Gesture_Controller.GestureController()
#             t = Thread(target = gc.start)
#             t.start()
#             reply('Launched Successfully')

#     elif ('stop gesture recognition' in voice_data) or ('top gesture recognition' in voice_data):
#         if Gesture_Controller.GestureController.gc_mode:
#             Gesture_Controller.GestureController.gc_mode = 0
#             reply('Gesture recognition stopped')
#         else:
#             reply('Gesture recognition is already inactive')
        
#     elif 'copy' in voice_data:
#         with keyboard.pressed(Key.ctrl):
#             keyboard.press('c')
#             keyboard.release('c')
#         reply('Copied')
          
#     elif 'page' in voice_data or 'pest'  in voice_data or 'paste' in voice_data:
#         with keyboard.pressed(Key.ctrl):
#             keyboard.press('v')
#             keyboard.release('v')
#         reply('Pasted')
        
#     # File Navigation (Default Folder set to C://)
#     elif 'list' in voice_data:
#         counter = 0
#         path = 'C://'
#         files = listdir(path)
#         filestr = ""
#         for f in files:
#             counter+=1
#             print(str(counter) + ':  ' + f)
#             filestr += str(counter) + ':  ' + f + '<br>'
#         file_exp_status = True
#         reply('These are the files in your root directory')
#         app.ChatBot.addAppMsg(filestr)
        
#     elif file_exp_status == True:
#         counter = 0   
#         if 'open' in voice_data:
#             if isfile(join(path,files[int(voice_data.split(' ')[-1])-1])):
#                 os.startfile(path + files[int(voice_data.split(' ')[-1])-1])
#                 file_exp_status = False
#             else:
#                 try:
#                     path = path + files[int(voice_data.split(' ')[-1])-1] + '//'
#                     files = listdir(path)
#                     filestr = ""
#                     for f in files:
#                         counter+=1
#                         filestr += str(counter) + ':  ' + f + '<br>'
#                         print(str(counter) + ':  ' + f)
#                     reply('Opened Successfully')
#                     app.ChatBot.addAppMsg(filestr)
                    
#                 except:
#                     reply('You do not have permission to access this folder')
                                    
#         if 'back' in voice_data:
#             filestr = ""
#             if path == 'C://':
#                 reply('Sorry, this is the root directory')
#             else:
#                 a = path.split('//')[:-2]
#                 path = '//'.join(a)
#                 path += '//'
#                 files = listdir(path)
#                 for f in files:
#                     counter+=1
#                     filestr += str(counter) + ':  ' + f + '<br>'
#                     print(str(counter) + ':  ' + f)
#                 reply('ok')
#                 app.ChatBot.addAppMsg(filestr)
                   
#     else: 
#         reply('I am not functioned to do this !')

# # ------------------Driver Code--------------------

# t1 = Thread(target = app.ChatBot.start)
# t1.start()

# # Lock main thread until Chatbot has started
# while not app.ChatBot.started:
#     time.sleep(0.5)

# wish()
# voice_data = None
# while True:
#     if app.ChatBot.isUserInput():
#         #take input from GUI
#         voice_data = app.ChatBot.popUserInput()
#     else:
#         #take input from Voice
#         voice_data = record_audio()

#     #process voice_data
#     if 'proton' in voice_data:
#         try:
#             #Handle sys.exit()
#             respond(voice_data)
#         except SystemExit:
#             reply("Exit Successfull")
#             break
#         except:
#             #some other exception got raised
#             print("EXCEPTION raised while closing.") 
#             break
        


# import pyttsx3
# import speech_recognition as sr
# from datetime import date
# import time
# import webbrowser
# import datetime
# from pynput.keyboard import Key, Controller
# import pyautogui
# import sys
# import os
# from os import listdir
# from os.path import isfile, join
# import platform
# import subprocess
# import wikipedia
# import Gesture_Controller
# import app
# from threading import Thread

# # -------------Object Initialization---------------
# today = date.today()
# r = sr.Recognizer()
# keyboard = Controller()

# # MAC FIX: pyttsx3 initialization
# try:
#     engine = pyttsx3.init()
#     # Mac voices are different, stick to default or select specifically
#     voices = engine.getProperty('voices')
#     engine.setProperty('voice', voices[0].id)
# except Exception as e:
#     print(f"TTS Engine Warning: {e}")

# # ----------------Variables------------------------
# file_exp_status = False
# files =[]
# path = ''
# is_awake = True 

# # ------------------Functions----------------------
# def reply(audio):
#     app.ChatBot.addAppMsg(audio)
#     print(audio)
#     engine.say(audio)
#     engine.runAndWait()

# def wish():
#     hour = int(datetime.datetime.now().hour)
#     if hour>=0 and hour<12:
#         reply("Good Morning!")
#     elif hour>=12 and hour<18:
#         reply("Good Afternoon!")   
#     else:
#         reply("Good Evening!")  
#     reply("I am Jarvis. Online and ready sir!")

# def record_audio():
#     with sr.Microphone() as source:
#         r.pause_threshold = 0.8
#         voice_data = ''
#         try:
#             # Adjust for ambient noise helps on Mac mics
#             r.adjust_for_ambient_noise(source, duration=0.5)
#             print("Listening...")
#             audio = r.listen(source, phrase_time_limit=5)
#             voice_data = r.recognize_google(audio)
#         except sr.RequestError:
#             reply('Sorry my Service is down. Plz check your Internet connection')
#         except sr.UnknownValueError:
#             pass
#         return voice_data.lower() if voice_data else ""

# def open_file_mac(filepath):
#     """Mac equivalent of os.startfile"""
#     subprocess.call(['open', filepath])

# def respond(voice_data):
#     global file_exp_status, files, is_awake, path
#     print(voice_data)
#     voice_data.replace('jarvis', '')
#     app.eel.addUserMsg(voice_data)

#     if is_awake==False:
#         if 'wake up' in voice_data:
#             is_awake = True
#             wish()
#     # --- NEW SHORT & SWEET COMMANDS ---

#     # COMMAND: "Proton Start"
#     if 'start' in voice_data:
#         reply('Starting System...')
#         # Launches the camera window as a separate process
#         subprocess.Popen([sys.executable, 'src/Gesture_Controller.py'])

#     # COMMAND: "Proton Stop"
#     elif 'stop' in voice_data:
#         reply('Stopping System...')
#         # MAC FIX: Force kills the camera process because it's running separately
#         os.system("pkill -f Gesture_Controller.py")

#     elif 'hello' in voice_data:
#         wish()
#     elif 'what is your name' in voice_data:
#         reply('My name is Proton!')
#     elif 'date' in voice_data:
#         reply(today.strftime("%B %d, %Y"))
#     elif 'time' in voice_data:
#         reply(str(datetime.datetime.now()).split(" ")[1].split('.')[0])
#     elif 'search' in voice_data:
#         reply('Searching for ' + voice_data.split('search')[1])
#         url = 'https://google.com/search?q=' + voice_data.split('search')[1]
#         try:
#             webbrowser.get().open(url)
#             reply('This is what I found Sir')
#         except:
#             reply('Please check your Internet')
#     elif 'location' in voice_data:
#         reply('Which place are you looking for ?')
#         temp_audio = record_audio()
#         app.eel.addUserMsg(temp_audio)
#         reply('Locating...')
#         url = 'https://google.nl/maps/place/' + temp_audio + '/&amp;'
#         try:
#             webbrowser.get().open(url)
#             reply('This is what I found Sir')
#         except:
#             reply('Please check your Internet')
#     elif ('bye' in voice_data) or ('by' in voice_data):
#         reply("Good bye Sir! Have a nice day.")
#         is_awake = False
#     elif ('exit' in voice_data) or ('terminate' in voice_data):
#         if Gesture_Controller.GestureController.gc_mode:
#             Gesture_Controller.GestureController.gc_mode = 0
#         app.ChatBot.close()
#         sys.exit()
    
#     # DYNAMIC CONTROLS
#     elif 'launch gesture' in voice_data: 
#         # We shortened the command to "launch gesture" to make it easier to say
#         reply('Launching Gesture System...')
#         # MAC FIX: Use subprocess to launch a separate, independent window
#         # This bypasses the macOS threading restriction.
#         subprocess.Popen([sys.executable, 'src/Gesture_Controller.py'])

#     elif ('stop gesture' in voice_data):
#         if Gesture_Controller.GestureController.gc_mode:
#             Gesture_Controller.GestureController.gc_mode = 0
#             reply('Gesture recognition stopped')
#         else:
#             reply('Gesture recognition is already inactive')
        
#     elif 'copy' in voice_data:
#         # Mac uses Command, not Ctrl, but usually standard python libs map ctrl to command on mac.
#         # If not, switch Key.ctrl to Key.cmd
#         with keyboard.pressed(Key.cmd):
#             keyboard.press('c')
#             keyboard.release('c')
#         reply('Copied')
          
#     elif 'paste' in voice_data:
#         with keyboard.pressed(Key.cmd):
#             keyboard.press('v')
#             keyboard.release('v')
#         reply('Pasted')
        
#     elif 'list' in voice_data:
#         counter = 0
#         path = '/Users/' + os.getlogin() + '/Documents/' # Changed to Mac Documents default
#         try:
#             files = listdir(path)
#             filestr = ""
#             for f in files:
#                 counter+=1
#                 filestr += str(counter) + ':  ' + f + '<br>'
#             file_exp_status = True
#             reply('These are the files in your documents directory')
#             app.ChatBot.addAppMsg(filestr)
#         except:
#              reply('Could not access documents')
        
#     elif file_exp_status == True:
#         counter = 0   
#         if 'open' in voice_data:
#             if isfile(join(path,files[int(voice_data.split(' ')[-1])-1])):
#                 # MAC FIX
#                 open_file_mac(path + files[int(voice_data.split(' ')[-1])-1])
#                 file_exp_status = False
#             else:
#                 try:
#                     path = path + files[int(voice_data.split(' ')[-1])-1] + '//'
#                     files = listdir(path)
#                     filestr = ""
#                     for f in files:
#                         counter+=1
#                         filestr += str(counter) + ':  ' + f + '<br>'
#                     reply('Opened Successfully')
#                     app.ChatBot.addAppMsg(filestr)
#                 except:
#                     reply('You do not have permission to access this folder')
#         if 'back' in voice_data:
#             filestr = ""
#             # Simple check, Mac paths start with /
#             if path == '/':
#                 reply('Sorry, this is the root directory')
#             else:
#                 a = path.split('//')[:-2]
#                 path = '//'.join(a)
#                 path += '//'
#                 files = listdir(path)
#                 for f in files:
#                     counter+=1
#                     filestr += str(counter) + ':  ' + f + '<br>'
#                 reply('ok')
#                 app.ChatBot.addAppMsg(filestr)
#     else: 
#         reply('I am not functioned to do this !')

# # ------------------Driver Code--------------------
# t1 = Thread(target = app.ChatBot.start)
# t1.start()

# while not app.ChatBot.started:
#     time.sleep(0.5)

# wish()
# voice_data = None
# while True:
#     if app.ChatBot.isUserInput():
#         voice_data = app.ChatBot.popUserInput()
#     else:
#         voice_data = record_audio()

#     if 'jarvis' in voice_data:
#         try:
#             respond(voice_data)
#         except SystemExit:
#             reply("Exit Successfull")
#             break
#         except Exception as e:
#             print(f"Error: {e}")
#             break

#!updated phase 2.2 jarvis
#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════
JARVIS - MODULAR VOICE & GESTURE ORCHESTRATOR
═══════════════════════════════════════════════════════════════════════════

PURPOSE:
This is the MAIN ENTRY POINT for the Jarvis-EcoSign system. It acts as the
"Command Center" that:
1. Launches the GUI (using eel)
2. Listens for voice or text input
3. Launches/stops the vision system (vision_backend.py)

ARCHITECTURE:
    User Input (Voice/Text)
           ↓
    Jarvis.py (This File)
           ↓
    subprocess.Popen('vision_backend.py')
           ↓
    Multiprocessing Hub
    ├─ HCI_Controller.py (Mouse)
    └─ ISL_Controller.py (Sign Language)

SAFE IMPORTS:
All audio-related imports are wrapped in try/except blocks. If PyAudio or
pyttsx3 fails to load, the system falls back to "TEXT MODE" where you can
type commands instead of speaking them.

AUTHOR: Nittaany (Satyam C)
PLATFORM: macOS Silicon (M1/M2)
PHASE: 2.3 (Modularization Complete)
═══════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import subprocess
import time
import datetime
import threading
import platform

# ═══════════════════════════════════════════════════════════════════════════
# SAFE AUDIO IMPORTS (Won't crash if drivers are broken)
# ═══════════════════════════════════════════════════════════════════════════
AUDIO_AVAILABLE = False

try:
    import pyttsx3
    import speech_recognition as sr
    
    # Initialize Text-to-Speech Engine
    engine = pyttsx3.init()
    
    # Mac-specific voice settings
    if platform.system() == "Darwin":
        engine.setProperty('rate', 190)  # Slower speech rate for clarity
    
    AUDIO_AVAILABLE = True
    print("[JARVIS] ✅ Audio drivers loaded successfully")
    
except ImportError as e:
    print(f"[JARVIS] ⚠️  Audio Warning: {e}")
    print("[JARVIS] Running in TEXT MODE (type commands instead of speaking)")
    
except Exception as e:
    print(f"[JARVIS] ⚠️  Audio initialization failed: {e}")
    print("[JARVIS] Running in TEXT MODE")

# ═══════════════════════════════════════════════════════════════════════════
# GUI MODULE IMPORT
# ═══════════════════════════════════════════════════════════════════════════
try:
    import app
    print("[JARVIS] ✅ GUI module loaded")
except Exception as e:
    print(f"[JARVIS] ❌ FATAL: Could not load GUI module: {e}")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════
# GLOBAL STATE VARIABLES
# ═══════════════════════════════════════════════════════════════════════════
vision_process = None  # Subprocess handle for vision_backend.py
is_awake = True        # Bot sleep/wake state

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def reply(text):
    """
    Output to both Console and GUI, optionally with voice.
    
    This is your main output function. It:
    1. Prints to console (for debugging)
    2. Sends message to the Eel GUI (user sees it in browser)
    3. Speaks it aloud (if audio is available)
    """
    print(f"[JARVIS] {text}")
    
    # Send to GUI
    try:
        app.ChatBot.addAppMsg(text)
    except:
        pass
    
    # Text-to-Speech (if available)
    if AUDIO_AVAILABLE:
        try:
            engine.say(text)
            engine.runAndWait()
        except:
            pass

def listen():
    """
    Captures voice input using Google Speech Recognition.
    
    Returns:
        str: Recognized text (lowercase), or None if failed
    
    Note: This requires internet connection (Google API)
    """
    if not AUDIO_AVAILABLE:
        return None
    
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            r.pause_threshold = 0.8  # Silence duration before ending phrase
            r.adjust_for_ambient_noise(source, duration=0.5)
            
            print("[LISTENING]...")
            audio = r.listen(source, phrase_time_limit=5)
            
            # Use Google's free API
            query = r.recognize_google(audio, language='en-in')
            return query.lower()
            
    except sr.UnknownValueError:
        # Google couldn't understand the audio
        return None
    except sr.RequestError:
        reply("Internet connection required for voice recognition")
        return None
    except Exception as e:
        print(f"[LISTEN ERROR] {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════════
# COMMAND PROCESSOR
# ═══════════════════════════════════════════════════════════════════════════

def process_command(query):
    """
    Parses user input and executes the appropriate action.
    
    This is the "brain" of Jarvis. It interprets what the user said/typed
    and calls the appropriate system functions.
    
    Args:
        query (str): User's command (lowercase)
    """
    global vision_process, is_awake
    
    query = query.lower().strip()
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 1: VISION SYSTEM CONTROL
    # ═══════════════════════════════════════════════════════════════
    
    if "start" in query or "launch" in query:
        """Launch the modular vision system"""
        reply("Initializing Modular Vision System...")
        
        # Check if already running
        if vision_process is not None and vision_process.poll() is None:
            reply("System is already running.")
            return
        
        # Launch vision_backend.py as a separate process
        try:
            vision_process = subprocess.Popen([
                sys.executable, 
                'src/vision_backend.py'
            ])
            reply("Vision System Active. Press Q to switch modes.")
        except Exception as e:
            reply(f"Failed to launch vision system: {e}")
    
    elif "stop" in query or "terminate" in query:
        """Stop the vision system"""
        reply("Stopping Vision System...")
        
        if vision_process:
            vision_process.terminate()
            vision_process.wait()  # Wait for clean shutdown
            vision_process = None
        
        # Backup kill (macOS specific)
        if platform.system() == "Darwin":
            os.system("pkill -f vision_backend.py")
        
        reply("System Offline.")
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 2: BASIC UTILITIES
    # ═══════════════════════════════════════════════════════════════
    
    elif "time" in query:
        """Tell current time"""
        current_time = datetime.datetime.now().strftime("%H:%M")
        reply(f"It is {current_time}")
    
    elif "date" in query:
        """Tell current date"""
        current_date = datetime.datetime.now().strftime("%B %d, %Y")
        reply(f"Today is {current_date}")
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 3: SYSTEM STATE CONTROL
    # ═══════════════════════════════════════════════════════════════
    
    elif "wake up" in query:
        """Activate bot"""
        is_awake = True
        reply("Online and ready.")
    
    elif "sleep" in query or "standby" in query:
        """Deactivate bot (stops listening)"""
        is_awake = False
        reply("Standing by. Say 'wake up' to resume.")
    
    elif "exit" in query or "bye" in query or "goodbye" in query:
        """Shutdown entire system"""
        reply("Shutting down. Goodbye.")
        
        # Clean shutdown of vision system
        if vision_process:
            vision_process.terminate()
        
        # Force kill any remaining processes
        if platform.system() == "Darwin":
            os.system("pkill -f vision_backend.py")
        
        # Exit Python
        os._exit(0)
    
    # ═══════════════════════════════════════════════════════════════
    # CATEGORY 4: HELP & INFO
    # ═══════════════════════════════════════════════════════════════
    
    elif "help" in query:
        """Show available commands"""
        help_text = """
        Available Commands:
        - "start" / "launch" → Activate vision system
        - "stop" / "terminate" → Deactivate vision system
        - "time" → Tell current time
        - "date" → Tell current date
        - "sleep" → Enter standby mode
        - "wake up" → Resume from standby
        - "exit" / "bye" → Shutdown system
        """
        reply(help_text)
    
    else:
        """Unknown command"""
        reply("I didn't understand that. Say 'help' for available commands.")

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION FLOW
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("═══════════════════════════════════════════════════")
    print("   JARVIS - MODULAR ARCHITECTURE v2.3")
    print("═══════════════════════════════════════════════════")
    print()
    
    # Status Report
    if AUDIO_AVAILABLE:
        print("✅ Voice Input: ENABLED")
        print("✅ Text-to-Speech: ENABLED")
    else:
        print("⚠️  Voice Input: DISABLED (running in TEXT MODE)")
        print("    Type your commands in the GUI instead.")
    print()
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 1: Launch GUI in Background Thread
    # ═══════════════════════════════════════════════════════════════
    gui_thread = threading.Thread(target=app.ChatBot.start)
    gui_thread.daemon = True  # Thread dies when main process dies
    gui_thread.start()
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 2: Wait for GUI to Initialize
    # ═══════════════════════════════════════════════════════════════
    print("[INIT] Waiting for GUI to load...")
    timeout = 30  # seconds
    start_time = time.time()
    
    while not app.ChatBot.started:
        if time.time() - start_time > timeout:
            print("[ERROR] GUI failed to start within 30 seconds")
            sys.exit(1)
        time.sleep(0.5)
    
    print("[INIT] ✅ GUI loaded successfully")
    print()
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 3: Initial Greeting
    # ═══════════════════════════════════════════════════════════════
    reply("System Initialized. Ready for commands.")
    reply("Say 'start' to launch the vision system.")
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 4: Main Command Loop
    # ═══════════════════════════════════════════════════════════════
    print("[READY] Entering command loop...")
    print("        Type in GUI or speak (if audio enabled)")
    print()
    
    while True:
        query = None
        
        # PRIORITY A: Check for GUI Text Input
        if app.ChatBot.isUserInput():
            query = app.ChatBot.popUserInput()
            app.ChatBot.addUserMsg(query)  # Echo back to GUI
            print(f"[INPUT: TEXT] {query}")
        
        # PRIORITY B: Check for Voice Input (if awake and audio available)
        elif AUDIO_AVAILABLE and is_awake:
            try:
                query = listen()
                if query:
                    app.ChatBot.addUserMsg(query)  # Show in GUI
                    print(f"[INPUT: VOICE] {query}")
            except Exception as e:
                print(f"[VOICE ERROR] {e}")
        
        # EXECUTE COMMAND
        if query:
            try:
                process_command(query)
            except Exception as e:
                print(f"[COMMAND ERROR] {e}")
                reply("An error occurred while processing that command.")
        
        # Small delay to prevent CPU spinning
        time.sleep(0.1)