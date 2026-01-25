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
"""
Jarvis - Voice Assistant & System Orchestrator
Launches Gesture Controller as independent subprocess
Platform: macOS Silicon
"""

import pyttsx3
import speech_recognition as sr
from datetime import date
import time
import webbrowser
import datetime
from pynput.keyboard import Key, Controller
import pyautogui
import sys
import os
from os import listdir
from os.path import isfile, join
import platform
import subprocess
import Gesture_Controller
import app
from threading import Thread

# ═══════════════════════════════════════════════════════════════
# INITIALIZATION
# ═══════════════════════════════════════════════════════════════

today = date.today()
r = sr.Recognizer()
keyboard = Controller()

# TTS Engine
try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    print("[JARVIS] TTS Engine initialized")
except Exception as e:
    print(f"[JARVIS] TTS Warning: {e}")

# Variables
file_exp_status = False
files = []
path = ''
is_awake = True
gesture_process = None  # Track subprocess

# ═══════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def reply(audio):
    """Speak and display message"""
    app.ChatBot.addAppMsg(audio)
    print(f"[JARVIS] {audio}")
    engine.say(audio)
    engine.runAndWait()

def wish():
    """Greet based on time of day"""
    hour = int(datetime.datetime.now().hour)
    if hour >= 0 and hour < 12:
        reply("Good Morning!")
    elif hour >= 12 and hour < 18:
        reply("Good Afternoon!")   
    else:
        reply("Good Evening!")  
    reply("I am Jarvis. Online and ready sir!")

def record_audio():
    """Capture voice input"""
    with sr.Microphone() as source:
        r.pause_threshold = 0.8
        voice_data = ''
        try:
            r.adjust_for_ambient_noise(source, duration=0.5)
            print("[JARVIS] Listening...")
            audio = r.listen(source, phrase_time_limit=5)
            voice_data = r.recognize_google(audio)
        except sr.RequestError:
            reply('Sorry, my service is down. Please check your internet.')
        except sr.UnknownValueError:
            pass
        return voice_data.lower() if voice_data else ""

def open_file_mac(filepath):
    """macOS equivalent of os.startfile"""
    subprocess.call(['open', filepath])

def respond(voice_data):
    """Process voice commands"""
    global file_exp_status, files, is_awake, path, gesture_process
    
    print(f"[JARVIS] Command: {voice_data}")
    voice_data = voice_data.replace('jarvis', '')
    app.eel.addUserMsg(voice_data)

    if not is_awake:
        if 'wake up' in voice_data:
            is_awake = True
            wish()
        return

    # ═══════════════════════════════════════════════════════
    # GESTURE CONTROL COMMANDS (IMPROVED)
    # ═══════════════════════════════════════════════════════
    
    if 'start' in voice_data or 'launch gesture' in voice_data:
        reply('Starting Gesture System...')
        try:
            # Kill any existing process
            os.system("pkill -f Gesture_Controller.py")
            time.sleep(0.5)
            
            # Launch new process
            gesture_process = subprocess.Popen([
                sys.executable, 
                'src/Gesture_Controller.py'
            ])
            reply('Gesture system launched successfully')
        except Exception as e:
            reply(f'Failed to start gesture system: {str(e)}')
    
    elif 'stop' in voice_data or 'stop gesture' in voice_data:
        reply('Stopping Gesture System...')
        try:
            if gesture_process:
                gesture_process.terminate()
                gesture_process = None
            os.system("pkill -f Gesture_Controller.py")
            reply('Gesture system stopped')
        except Exception as e:
            reply(f'Error stopping gesture system: {str(e)}')
    
    # ═══════════════════════════════════════════════════════
    # BASIC COMMANDS
    # ═══════════════════════════════════════════════════════
    
    elif 'hello' in voice_data:
        wish()
    
    elif 'what is your name' in voice_data:
        reply('My name is Jarvis!')
    
    elif 'date' in voice_data:
        reply(today.strftime("%B %d, %Y"))
    
    elif 'time' in voice_data:
        reply(str(datetime.datetime.now()).split(" ")[1].split('.')[0])
    
    elif 'search' in voice_data:
        query = voice_data.split('search')[1]
        reply(f'Searching for {query}')
        url = 'https://google.com/search?q=' + query
        try:
            webbrowser.get().open(url)
            reply('This is what I found')
        except:
            reply('Please check your internet')
    
    elif 'location' in voice_data:
        reply('Which place are you looking for?')
        temp_audio = record_audio()
        app.eel.addUserMsg(temp_audio)
        reply('Locating...')
        url = 'https://google.nl/maps/place/' + temp_audio
        try:
            webbrowser.get().open(url)
            reply('This is what I found')
        except:
            reply('Please check your internet')
    
    elif 'bye' in voice_data or 'by' in voice_data:
        reply("Goodbye sir! Have a nice day.")
        is_awake = False
    
    elif 'exit' in voice_data or 'terminate' in voice_data:
        if gesture_process:
            gesture_process.terminate()
        os.system("pkill -f Gesture_Controller.py")
        app.ChatBot.close()
        sys.exit()
    
    elif 'copy' in voice_data:
        with keyboard.pressed(Key.cmd):
            keyboard.press('c')
            keyboard.release('c')
        reply('Copied')
    
    elif 'paste' in voice_data:
        with keyboard.pressed(Key.cmd):
            keyboard.press('v')
            keyboard.release('v')
        reply('Pasted')
    
    elif 'list' in voice_data:
        counter = 0
        path = '/Users/' + os.getlogin() + '/Documents/'
        try:
            files = listdir(path)
            filestr = ""
            for f in files:
                counter += 1
                filestr += str(counter) + ':  ' + f + '<br>'
            file_exp_status = True
            reply('These are the files in your documents directory')
            app.ChatBot.addAppMsg(filestr)
        except:
            reply('Could not access documents')
    
    elif file_exp_status == True:
        counter = 0   
        if 'open' in voice_data:
            if isfile(join(path, files[int(voice_data.split(' ')[-1])-1])):
                open_file_mac(path + files[int(voice_data.split(' ')[-1])-1])
                file_exp_status = False
            else:
                try:
                    path = path + files[int(voice_data.split(' ')[-1])-1] + '//'
                    files = listdir(path)
                    filestr = ""
                    for f in files:
                        counter += 1
                        filestr += str(counter) + ':  ' + f + '<br>'
                    reply('Opened successfully')
                    app.ChatBot.addAppMsg(filestr)
                except:
                    reply('You do not have permission to access this folder')
        
        if 'back' in voice_data:
            filestr = ""
            if path == '/':
                reply('Sorry, this is the root directory')
            else:
                a = path.split('//')[:-2]
                path = '//'.join(a) + '//'
                files = listdir(path)
                for f in files:
                    counter += 1
                    filestr += str(counter) + ':  ' + f + '<br>'
                reply('Okay')
                app.ChatBot.addAppMsg(filestr)
    
    else: 
        reply('I am not programmed for that yet')

# ═══════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  JARVIS - Voice Assistant")
    print("=" * 60)
    
    t1 = Thread(target=app.ChatBot.start)
    t1.start()
    
    while not app.ChatBot.started:
        time.sleep(0.5)
    
    wish()
    voice_data = None
    
    while True:
        if app.ChatBot.isUserInput():
            voice_data = app.ChatBot.popUserInput()
        else:
            voice_data = record_audio()
        
        if 'jarvis' in voice_data:
            try:
                respond(voice_data)
            except SystemExit:
                reply("Exit successful")
                break
            except Exception as e:
                print(f"[ERROR] {e}")
                break