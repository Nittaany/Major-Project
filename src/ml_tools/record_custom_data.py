import cv2
import os
import time
import sys

# --- CONFIGURATION ---
# Fixed Root Path
DATASET_ROOT = "/Users/nitant/Documents/Major-Project/data/raw/INCLUDE50"
CLIP_DURATION = 3  # Seconds per clip

def record_batch(rel_path, target_count):
    # 1. Setup Directory
    save_dir = os.path.join(DATASET_ROOT, rel_path)
    
    if not os.path.exists(save_dir):
        print(f"[WARN] Folder not found: {save_dir}")
        create = input("Create this new class folder? (y/n): ").strip().lower()
        if create == 'y':
            os.makedirs(save_dir)
            print(f"[INFO] Created: {save_dir}")
        else:
            print("[INFO] Skipping...")
            return

    # 2. Camera Setup
    cap = cv2.VideoCapture(0) # Change to 1 if using external webcam
    if not cap.isOpened():
        print("[ERROR] Could not open camera.")
        return

    # 3. Batch Loop
    current_session_count = 0
    
    print(f"\n════════════════════════════════════════════════════")
    print(f" TARGET CLASS: {rel_path}")
    print(f" GOAL:         {target_count} new videos")
    print(f" DURATION:     {CLIP_DURATION}s per video")
    print(f" PATH:         {save_dir}")
    print(f"════════════════════════════════════════════════════")

    while current_session_count < target_count:
        # --- STATE 1: WAITING FOR USER (The "Good to Go" State) ---
        while True:
            ret, frame = cap.read()
            if not ret: break

            # Mirror for display interaction
            display = cv2.flip(frame, 1)

            # UI Overlay
            # Green Box = Ready
            cv2.rectangle(display, (0,0), (640, 60), (0, 200, 0), -1)
            cv2.putText(display, f"NEXT: Clip {current_session_count + 1}/{target_count}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(display, "PRESS [SPACE] TO START RECORDING", (20, 450), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display, "[Q] Back to Menu", (450, 450), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow("Jarvis Recorder", display)

            key = cv2.waitKey(1)
            if key == ord('q'): 
                cap.release()
                cv2.destroyAllWindows()
                return # Go back to main menu
            
            if key == 32: # SPACE BAR pressed
                break # Exit wait loop, start recording

        # --- STATE 2: RECORDING (The "Action" State) ---
        filename = os.path.join(save_dir, f"custom_{int(time.time())}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(filename, fourcc, 30.0, (640, 480))
        
        start_time = time.time()
        print(f" -> Recording Clip {current_session_count + 1}...")

        while (time.time() - start_time) < CLIP_DURATION:
            ret, frame = cap.read()
            if not ret: break

            # 1. Write RAW frame to disk (No Flip!)
            out.write(frame)

            # 2. Show FLIPPED frame to user with Red "Rec" dot
            display = cv2.flip(frame, 1)
            cv2.circle(display, (30, 30), 20, (0, 0, 255), -1)
            cv2.putText(display, "RECORDING...", (60, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imshow("Jarvis Recorder", display)
            cv2.waitKey(1)

        out.release()
        current_session_count += 1
        print(f"    [SAVED] {filename}")
        
        # Small cooldown so you don't accidentally double-press
        cv2.waitKey(500) 

    # Cleanup after batch
    cap.release()
    cv2.destroyAllWindows()
    print("\n[SUCCESS] Batch completed.")

def main():
    print("════════════════════════════════════════════════════")
    print(" JARVIS-ECOSIGN: CUSTOM DATASET RECORDER")
    print("════════════════════════════════════════════════════")
    print(f"Root: {DATASET_ROOT}")

    while True:
        print("\n--- NEW BATCH ---")
        rel_path = input("Enter Class Path (e.g. 'Adjectives/1. loud/') or 'q' to quit: ").strip()
        
        if rel_path.lower() == 'q':
            print("Exiting...")
            sys.exit(0)
            
        if not rel_path:
            continue

        try:
            count_str = input(f"How many videos for '{rel_path}'? ")
            if not count_str.isdigit():
                print("[ERROR] Please enter a valid number.")
                continue
            target_count = int(count_str)
        except ValueError:
            continue

        # Launch the GUI loop for this class
        record_batch(rel_path, target_count)

if __name__ == "__main__":
    main()