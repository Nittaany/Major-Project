import eel
import os
import queue

class ChatBot:
    started = False
    # Thread-safe queue for Jarvis communication
    userinputQueue = queue.Queue()

    @staticmethod
    def isUserInput():
        return not ChatBot.userinputQueue.empty()

    @staticmethod
    def popUserInput():
        return ChatBot.userinputQueue.get()

    @staticmethod
    def close_callback(route, websockets):
        os._exit(0)

    # --- EXPOSED TO JS ---
    @eel.expose
    def getUserInput(msg):
        ChatBot.userinputQueue.put(msg)
    
    @staticmethod
    def addUserMsg(msg):
        try: eel.addUserMsg(msg)
        except: pass
    
    @staticmethod
    def addAppMsg(msg):
        try: eel.addAppMsg(msg)
        except: pass

    @staticmethod
    def start():
        # ═══════════════════════════════════════════════════════════
        # ROBUST PATH RESOLUTION FOR macOS/Linux
        # ═══════════════════════════════════════════════════════════
        
        # 1. Get the absolute path to THIS file (app.py)
        current_file = os.path.abspath(__file__)
        print(f"[APP] Current file: {current_file}")
        
        # 2. Get the directory containing this file (src/)
        src_dir = os.path.dirname(current_file)
        print(f"[APP] Source directory: {src_dir}")
        
        # 3. The web folder should be in the SAME directory as app.py
        #    Structure should be: src/app.py and src/web/
        web_folder = os.path.join(src_dir, 'web')
        
        # 4. Verify it exists
        if not os.path.exists(web_folder):
            print(f"[ERROR] Web folder NOT found at: {web_folder}")
            print(f"[ERROR] Please ensure your structure is:")
            print(f"        src/")
            print(f"        ├── app.py")
            print(f"        ├── Jarvis.py")
            print(f"        └── web/")
            print(f"             ├── index.html")
            print(f"             ├── css/")
            print(f"             └── js/")
            return

        # 5. Double-check that index.html exists
        index_path = os.path.join(web_folder, 'index.html')
        if not os.path.exists(index_path):
            print(f"[ERROR] index.html NOT found at: {index_path}")
            return

        print(f"[APP] ✅ Web folder located: {web_folder}")
        print(f"[APP] ✅ index.html found: {index_path}")

        # ═══════════════════════════════════════════════════════════
        # INITIALIZE EEL WITH CORRECT PATH
        # ═══════════════════════════════════════════════════════════
        eel.init(web_folder, allowed_extensions=['.js', '.html'])
        
        ChatBot.started = True
        
        # ═══════════════════════════════════════════════════════════
        # LAUNCH CONFIGURATION
        # ═══════════════════════════════════════════════════════════
        launch_options = {
            'mode': 'default',           # Use system default browser (Safari/Chrome)
            'host': 'localhost',
            'port': 8000,                 # Changed from 27005 to standard 8000
            'block': False,               # Don't block main thread
            'size': (400, 600),           # Window size
            'close_callback': ChatBot.close_callback
        }
        
        try:
            print(f"[APP] Launching GUI on http://localhost:8000")
            eel.start('index.html', **launch_options)
            
            # Keep the app alive
            while ChatBot.started:
                try:
                    eel.sleep(1.0)
                except:
                    break
                    
        except Exception as e:
            print(f"[APP] FATAL ERROR: Could not launch browser.")
            print(f"[APP] Error details: {e}")
            ChatBot.started = False

# ═══════════════════════════════════════════════════════════
# STANDALONE TEST MODE
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═══════════════════════════════════════════════════")
    print("   JARVIS GUI - STANDALONE TEST MODE")
    print("═══════════════════════════════════════════════════")
    print()
    print("This will launch ONLY the GUI (no voice, no vision).")
    print("Use this to verify the web interface is working.")
    print()
    
    ChatBot.start()