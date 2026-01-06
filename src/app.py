import eel
import os
from queue import Queue

class ChatBot:

    started = False
    userinputQueue = Queue()

    def isUserInput():
        return not ChatBot.userinputQueue.empty()

    def popUserInput():
        return ChatBot.userinputQueue.get()

    def close_callback(route, websockets):
        exit()

    @eel.expose
    def getUserInput(msg):
        ChatBot.userinputQueue.put(msg)
        print(msg)
    
    def close():
        ChatBot.started = False
    
    def addUserMsg(msg):
        eel.addUserMsg(msg)
    
    def addAppMsg(msg):
        eel.addAppMsg(msg)

    def start():
        path = os.path.dirname(os.path.abspath(__file__))
        eel.init(path + r'/web', allowed_extensions=['.js', '.html'])
        
        # Define the launch options common to both modes
        launch_options = {
            'host': 'localhost',
            'port': 27005,
            'block': False,
            'size': (350, 480),
            'position': (10, 100),
            'disable_cache': True,
            'close_callback': ChatBot.close_callback
        }

        try:
            print("Attempting to launch Firefox...")
            # TRY 1: Open in Firefox
            eel.start('index.html', mode='firefox', **launch_options)
            ChatBot.started = True
        except Exception as e:
            print(f"Firefox failed ({e}). Falling back to Default Browser.")
            try:
                # TRY 2: Fallback to Default (Safari/System Default)
                eel.start('index.html', mode='default', **launch_options)
                ChatBot.started = True
            except Exception as e2:
                print(f"FATAL: Could not launch any browser. {e2}")
                ChatBot.started = False

        # Keep the main thread alive while the GUI is running
        while ChatBot.started:
            try:
                eel.sleep(1.0)
            except:
                break