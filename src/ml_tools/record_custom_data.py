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
    
    # --- FIX 1: DYNAMIC RESOLUTION ---
    # We read the ACTUAL resolution from the camera
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if not cap.isOpened() or frame_width == 0:
        print("[ERROR] Could not open camera.")
        return
        
    print(f"[CAMERA] Resolution detected: {frame_width}x{frame_height}")

    # 3. Batch Loop
    current_session_count = 0
    
    print(f"\n════════════════════════════════════════════════════")
    print(f" TARGET CLASS: {rel_path}")
    print(f" GOAL:         {target_count} new videos")
    print(f" PATH:         {save_dir}")
    print(f"════════════════════════════════════════════════════")

    while current_session_count < target_count:
        # --- STATE 1: WAITING FOR USER ---
        while True:
            ret, frame = cap.read()
            if not ret: break

            display = cv2.flip(frame, 1)

            # UI Overlay
            cv2.rectangle(display, (0,0), (640, 60), (0, 200, 0), -1)
            cv2.putText(display, f"NEXT: Clip {current_session_count + 1}/{target_count}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(display, "PRESS [SPACE] TO START", (20, 450), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display, "[Q] Back to Menu", (450, 450), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            cv2.imshow("Jarvis Recorder", display)

            key = cv2.waitKey(1)
            if key == ord('q'): 
                cap.release()
                cv2.destroyAllWindows()
                return 
            
            if key == 32: # SPACE BAR
                break 

        # --- STATE 2: RECORDING ---
        filename = os.path.join(save_dir, f"custom_{int(time.time())}.mp4")
        
        # --- FIX 2: MATCH RESOLUTION IN WRITER ---
        # Use 'mp4v' (standard) or 'avc1' (H.264 for Mac)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v') 
        out = cv2.VideoWriter(filename, fourcc, 30.0, (frame_width, frame_height))
        
        start_time = time.time()
        print(f" -> Recording Clip {current_session_count + 1}...")

        while (time.time() - start_time) < CLIP_DURATION:
            ret, frame = cap.read()
            if not ret: break

            # Write RAW frame (No Flip!)
            # This MUST match the (frame_width, frame_height) set above
            out.write(frame)

            # Show FLIPPED frame
            display = cv2.flip(frame, 1)
            cv2.circle(display, (30, 30), 20, (0, 0, 255), -1)
            cv2.putText(display, "RECORDING...", (60, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.imshow("Jarvis Recorder", display)
            cv2.waitKey(1)

        out.release()
        current_session_count += 1
        print(f"    [SAVED] {filename}")
        
        # Verify file size isn't empty
        if os.path.getsize(filename) < 1000:
             print("    [WARNING] File seems empty! Check Camera Permissions.")
        
        cv2.waitKey(500) 

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
        rel_path = input("Enter Class Path (e.g. 'Adjectives/1. loud/') or 'q': ").strip()
        
        if rel_path.lower() == 'q':
            sys.exit(0)
            
        if not rel_path: continue

        # --- FIX 3: SANITIZE INPUT ---
        # Remove backslashes users might accidentally paste from terminal
        rel_path = rel_path.replace('\\', '') 

        try:
            count_str = input(f"How many videos for '{rel_path}'? ")
            if not count_str.isdigit(): continue
            target_count = int(count_str)
            record_batch(rel_path, target_count)
        except ValueError:
            continue

if __name__ == "__main__":
    main()