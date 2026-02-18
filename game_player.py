import numpy as np
import time
import threading
import pydirectinput
import cv2
import keyboard
from fast_ctypes_screenshots import ScreenshotOfOneMonitor
from locate_pixelcolor_cpppragma import search_colors
from game_starter import find_and_click_with_retry

def perform_loop(debug=False, done_event=None):
    """Executes loop trick: down + space (runs in separate thread)."""
    if debug: print("[TRICK] Executing: LOOP (down + space)")
    keyboard.send("down")
    keyboard.send("space")
    time.sleep(0.8) # Simulates trick time
    if done_event:
        done_event.set()

def perform_360(debug=False, done_event=None):
    """Executes 360 trick: space + right (runs in separate thread)."""
    if debug: print("[TRICK] Executing: 360 (space + right)")
    keyboard.send("space")
    keyboard.send("right")
    time.sleep(0.8) # Simulates trick time
    if done_event:
        done_event.set()

def _trigger_trick(fn, debug):
    """Triggers a trick function in a daemon thread and returns the completion Event."""
    done_event = threading.Event()
    threading.Thread(target=fn, kwargs={"debug": debug, "done_event": done_event}, daemon=True).start()
    return done_event

def run_game_loop(roi, game_name, debug=False, visualize=False, active_check_callback=None):
    """
    Runs the main game loop.
    
    Args:
        roi: Dictionary with ROI coordinates {'x': int, 'y': int, 'w': int, 'h': int}
        game_name: Game name ('journey' or 'newcp') to define colors.
        debug: If True, shows logs.
        visualize: If True, shows visualization window.
        active_check_callback: Function that returns True if the loop should continue processing frames.
    """
    
    # =========================
    # CONFIGURATIONS
    # =========================
    
    # Local imports to avoid error if not at top
    import os

    # Defining color based on game with ternary
    allcolors = [[35, 35, 35]] if game_name == 'newcp' else [[0, 0, 0]]
    bgrcolors = np.array(allcolors, dtype=np.uint8)

    sign_count = 0
    last_sign_visible = False
    last_sign_time = time.time()
    last_x_pos = None
    last_trick = None  # None, 'loop' or '360' — controls trick alternation
    _trick_done = None   # Event signaling when current trick finished
    last_trick_time = 0.0  # Timestamp of last triggered trick

    def trick_cooldown():
        return 1.1 if last_trick == 'loop' else 1.0

    TURN_TIME = 1.65
    RESET_TIMEOUT = 4.0
    
    # 'close.png' configuration
    path_close = os.path.join(os.path.dirname(__file__), "images", game_name, "close.png")
    img_close = cv2.imread(path_close)
    if img_close is None:
        if debug: print(f"[WARNING] Image close.png not found at: {path_close}")
        
    last_check_close = time.time()
    CHECK_CLOSE_INTERVAL = 1.0  # Checks every 1 second to avoid weighing down the loop
    
    # Only starts looking for close button after X seconds
    TIME_BEFORE_CHECK_CLOSE = 45
    game_start_time = time.time()
    close_detection_active = False  # Flag to indicate when close detection is active

    if debug: print("Starting game loop...")

    while True:        
        with ScreenshotOfOneMonitor(monitor=0, ascontiguousarray=False) as sct:
            frame = sct.screenshot_one_monitor()
        
        # =========================
        # GAME END DETECTION (CLOSE)
        # =========================
        # Periodically checks if 'close' button appeared, but ONLY AFTER {TIME_BEFORE_CHECK_CLOSE} SECONDS
        current_time = time.time()
        if (img_close is not None and 
            (current_time - game_start_time > TIME_BEFORE_CHECK_CLOSE) and 
            (current_time - last_check_close > CHECK_CLOSE_INTERVAL)):
            
            # Activates flag to stop sign detection
            if not close_detection_active:
                close_detection_active = True
                if debug: print("[INFO] close.png detection activated. Stopping sign detection.")
            
            last_check_close = current_time
            
            # Match Template
            pass_search = frame
            # Remove alpha channel if exists in frame for search
            if frame.shape[2] == 4:
                pass_search = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
            res = cv2.matchTemplate(pass_search, img_close, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            if max_val >= 0.8: # Confidence
                if debug: print(f"Game end detected! (Confidence: {max_val:.2f})")
                
                # Clicks center of close button
                h_close, w_close = img_close.shape[:2]
                cx = max_loc[0] + w_close // 2
                cy = max_loc[1] + h_close // 2
                
                pydirectinput.click(cx, cy)

                if game_name == 'newcp':
                    # 'shack.png' configuration
                    base_path = os.path.join(os.path.dirname(__file__), "images", game_name)
                    img_shack = os.path.join(base_path, "shack.png")
                    
                    find_and_click_with_retry("Shack", img_shack, roi=roi, debug=debug)

                    # Requested sleep of 5.0 before returning (restart)
                    time.sleep(5.0)
                    return
                
                # Requested sleep of 0.5 before returning (restart)
                time.sleep(0.5)
                return # Exits function, causing bot to restart cycle
                
        # If callback says inactive, just sleeps and continues
        if active_check_callback and not active_check_callback():
            time.sleep(0.05)
            # cv2.destroyAllWindows()
            continue
            
        # =========================
        # SIGN DETECTION (only runs if close detection is not active)
        # =========================
        detectado_esq = False
        detectado_dir = False
        sign_detected = False

        # if not close_detection_active:
        # Crops only ROI area
        x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]
        frame_roi = frame[y:y+h, x:x+w]

        # Reduces resolution and analyzes upper half
        small = frame_roi[::2, ::2]
        small = small[0:int(small.shape[0]*0.6), :]

        # =========================
        # SIGN DETECTION BY ZONES
        # =========================
        h_small, w_small = small.shape[:2]
        
        # Defines zone size (adjust as needed)
        zone_w = int(w_small * 0.05) # 5% of width
        zone_h = int(h_small * 0.10) # 10% of height
        
        # Left Zone (Center 25% width, 80% height)
        cx_esq = int(w_small * 0.25)
        cy_esq = int(h_small * 0.80)
        x1_esq = cx_esq - zone_w // 2
        y1_esq = cy_esq - zone_h // 2
        x2_esq = cx_esq + zone_w // 2
        y2_esq = cy_esq + zone_h // 2
        
        # Right Zone (Center 75% width, 80% height)
        cx_dir = int(w_small * 0.75)
        cy_dir = int(h_small * 0.80)
        x1_dir = cx_dir - zone_w // 2
        y1_dir = cy_dir - zone_h // 2
        x2_dir = cx_dir + zone_w // 2
        y2_dir = cy_dir + zone_h // 2

        # Crops
        # Ensures limits within image
        x1_esq, y1_esq = max(0, x1_esq), max(0, y1_esq)
        x2_esq, y2_esq = min(w_small, x2_esq), min(h_small, y2_esq)
        
        x1_dir, y1_dir = max(0, x1_dir), max(0, y1_dir)
        x2_dir, y2_dir = min(w_small, x2_dir), min(h_small, y2_dir)

        roi_esq = small[y1_esq:y2_esq, x1_esq:x2_esq]
        roi_dir = small[y1_dir:y2_dir, x1_dir:x2_dir]

        # Search in zones
        found_left = search_colors(pic=roi_esq, colors=bgrcolors, cpus=4)
        found_right = search_colors(pic=roi_dir, colors=bgrcolors, cpus=4)
        
        detected_left = np.any(found_left)
        detected_right = np.any(found_right)
        
        sign_detected = detected_left or detected_right

        # =========================
        # TRICKS (when sign_count == 0 and nno sign visible)
        # =========================
        # Only triggers new trick if: previous finished AND cooldown passed
        # And mainly: if NO sign detected in this exact frame
        can_trick = (_trick_done is None or _trick_done.is_set())
        is_cooldown_ok = (time.time() - last_trick_time) >= trick_cooldown()
        
        if sign_count == 0 and not sign_detected and can_trick and is_cooldown_ok:
            # Alternates between loop and 360: does the one NOT done last
            if last_trick != '360':
                last_trick = '360'
                _trick_done = _trigger_trick(perform_360, debug)
            else:
                last_trick = 'loop'
                _trick_done = _trigger_trick(perform_loop, debug)
            last_trick_time = time.time()

        # =========================
        # VISUALIZATION
        # =========================
        if visualize:
            vis = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            
            # Draws zone rectangles in visualization
            # Left
            color_left = (0, 255, 0) if detected_left else (255, 0, 0)
            cv2.rectangle(vis, (x1_esq, y1_esq), (x2_esq, y2_esq), color_left, 2)
            
            # Right
            color_right = (0, 255, 0) if detected_right else (255, 0, 0)
            cv2.rectangle(vis, (x1_dir, y1_dir), (x2_dir, y2_dir), color_right, 2)

            vis = cv2.resize(vis, (vis.shape[1]*2, vis.shape[0]*2))
            
            # Status Text
            status_txt = "NONE"
            if detected_left: status_txt = "LEFT"
            if detected_right: status_txt = "RIGHT"
            
            cv2.putText(vis, f"Detected: {status_txt}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.imshow("Sign Detection", vis)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                # Ends loop if 'q' is pressed in window
                cv2.destroyAllWindows()
                break

        # =========================
        # SIGN COUNTING
        # =========================
        if sign_detected and not last_sign_visible:
            sign_count += 1
            last_sign_time = time.time()
            if debug:
                status_txt = "NONE"
                if detected_left: status_txt = "LEFT"
                if detected_right: status_txt = "RIGHT"
                print(f"Sign #{sign_count} detected at: {status_txt}")

        last_sign_visible = sign_detected

        if time.time() - last_sign_time > RESET_TIMEOUT:
            if sign_count != 0:
                if debug:
                    print("Resetting counter")
            sign_count = 0
            last_x_pos = None

        # =========================
        # TURN ONLY ON 3RD
        # =========================
        if sign_count >= 3:
            
            turn_needed = False
            
            if detected_right:
                if debug:
                    print(f"RIGHT (Zone) -> ↩ TURNING LEFT")
                keyboard.press("down")
                keyboard.press("left")
                time.sleep(TURN_TIME)
                keyboard.release("left")
                keyboard.release("down")
                turn_needed = True
            elif detected_left:
                if debug:
                    print(f"LEFT (Zone) -> ↪ TURNING RIGHT")
                keyboard.press("down")
                keyboard.press("right")
                time.sleep(TURN_TIME)
                keyboard.release("right")
                keyboard.release("down")
                turn_needed = True
                
            if turn_needed:
                sign_count = 0
