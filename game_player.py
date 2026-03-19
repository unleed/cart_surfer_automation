import numpy as np
import time
import pyautogui
import cv2
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import mss
from pynput.keyboard import Controller, Key
from game_starter import find_and_click_with_retry

_kb = Controller()

trick_executor = ThreadPoolExecutor(max_workers=2)

def perform_loop(debug=False, done_event=None):
    """Executes loop trick: down + space (runs in separate thread)."""
    if debug: print("[TRICK] Executing: LOOP (down + space)")
    _kb.press(Key.down)
    _kb.release(Key.down)
    _kb.press(Key.space)
    _kb.release(Key.space)
    time.sleep(1.1) # Simulates trick time
    if done_event:
        done_event.set()

def perform_360(debug=False, done_event=None):
    """Executes 360 trick: space + right (runs in separate thread)."""
    if debug: print("[TRICK] Executing: 360 (space + right)")
    _kb.press(Key.space)
    _kb.release(Key.space)
    _kb.press(Key.right)
    _kb.release(Key.right)
    time.sleep(0.8) # Simulates trick time
    if done_event:
        done_event.set()

def _trigger_trick(fn, debug):
    """Triggers a trick function in a pool and returns the completion Event."""
    done_event = threading.Event()
    trick_executor.submit(fn, debug, done_event)
    return done_event

def perform_turn(direction, debug=False):
    TURN_TIME = 1.64
    if direction == "right":
        if debug:
            print(f"RIGHT (Zone) -> ↩ TURNING LEFT")
        _kb.press(Key.down)
        _kb.press(Key.left)
        time.sleep(TURN_TIME)
        _kb.release(Key.left)
        _kb.release(Key.down)
        turn_needed = True
    elif direction == "left":
        if debug:
            print(f"LEFT (Zone) -> ↪ TURNING RIGHT")
        _kb.press(Key.down)
        _kb.press(Key.right)
        time.sleep(TURN_TIME)
        _kb.release(Key.right)
        _kb.release(Key.down)
        turn_needed = True

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
    
    allcolors = [[35, 35, 35]] if game_name == 'newcp' else [[0, 0, 0]]
    bgr_target_color = np.array(allcolors[0], dtype=np.uint8)

    sign_count = 0
    last_sign_visible = False
    last_sign_time = time.time()
    last_x_pos = None
    last_trick = None  # None, 'loop' or '360' — controls trick alternation
    _trick_done = None   # Event signaling when current trick finished

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

    # =========================
    # PRE-CALCULATIONS (Dica 4)
    # =========================
    # Reducing resolution to create variables previously
    small_w = (roi["w"] + 1) // 2
    small_h = int(((roi["h"] + 1) // 2) * 0.6)
    
    zone_w = int(small_w * 0.05)
    zone_h = int(small_h * 0.10)
    
    cx_esq = int(small_w * 0.25)
    cy_esq = int(small_h * 0.80)
    x1_esq = max(0, cx_esq - zone_w // 2)
    y1_esq = max(0, cy_esq - zone_h // 2)
    x2_esq = min(small_w, cx_esq + zone_w // 2)
    y2_esq = min(small_h, cy_esq + zone_h // 2)
    
    cx_dir = int(small_w * 0.75)
    cy_dir = int(small_h * 0.80)
    x1_dir = max(0, cx_dir - zone_w // 2)
    y1_dir = max(0, cy_dir - zone_h // 2)
    x2_dir = min(small_w, cx_dir + zone_w // 2)
    y2_dir = min(small_h, cy_dir + zone_h // 2)

    x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]
    monitor_roi = {"top": y, "left": x, "width": w, "height": h}

    with mss.mss() as sct:
        while True:        
            sct_img = sct.grab(monitor_roi)
            frame_roi = np.array(sct_img)
            
            # =========================
            # GAME END DETECTION (CLOSE)
            # =========================
            current_time = time.time()
            if (img_close is not None and 
                (current_time - game_start_time > TIME_BEFORE_CHECK_CLOSE) and 
                (current_time - last_check_close > CHECK_CLOSE_INTERVAL)):
                
                if not close_detection_active:
                    close_detection_active = True
                    if debug: print("[INFO] close.png detection activated. Stopping sign detection.")
                
                last_check_close = current_time
                
                h_f, w_f = frame_roi.shape[:2]
                
                # Restrict search area to upper right (where buttons usually are)
                search_area = frame_roi[0:int(h_f/2), int(w_f/4):w_f]
                pass_search = search_area
                
                if pass_search.shape[2] == 4:
                    pass_search = cv2.cvtColor(pass_search, cv2.COLOR_BGRA2BGR)
                    
                res = cv2.matchTemplate(pass_search, img_close, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                
                if max_val >= 0.8:
                    if debug: print(f"Game end detected! (Confidence: {max_val:.2f})")
                    
                    h_close, w_close = img_close.shape[:2]
                    # Compensating X pos because we cut 1/4 left and we are inside the ROI bounds
                    cx = x + max_loc[0] + w_close // 2 + int(w_f/4)
                    cy = y + max_loc[1] + h_close // 2
                    
                    pyautogui.click(cx, cy)

                    if game_name == 'newcp':
                        base_path = os.path.join(os.path.dirname(__file__), "images", game_name)
                        img_shack = os.path.join(base_path, "shack.png")
                        find_and_click_with_retry("Shack", img_shack, roi=roi, debug=debug)
                        time.sleep(4.0)
                        return
                    
                    time.sleep(0.5)
                    return
                    
            if active_check_callback and not active_check_callback():
                time.sleep(0.05)
                continue
                
            # =========================
            # SIGN DETECTION
            # =========================
            small = frame_roi[::2, ::2]
            small = small[0:int(small.shape[0]*0.6), :]

            roi_esq = small[y1_esq:y2_esq, x1_esq:x2_esq]
            roi_dir = small[y1_dir:y2_dir, x1_dir:x2_dir]

            # Convert BGRA to BGR equivalent check (Slice apenas os canais BGRA)
            if roi_esq.shape[2] == 4:
                roi_esq = roi_esq[:, :, :3]
                roi_dir = roi_dir[:, :, :3]

            # Vectorized processing with Numpy OpenCV base
            mask_left = cv2.inRange(roi_esq, bgr_target_color, bgr_target_color)
            mask_right = cv2.inRange(roi_dir, bgr_target_color, bgr_target_color)
            
            detected_left = cv2.countNonZero(mask_left) > 0
            detected_right = cv2.countNonZero(mask_right) > 0
            
            sign_detected = detected_left or detected_right

            # =========================
            # TRICKS
            # =========================
            can_trick = (_trick_done is None or _trick_done.is_set())
            
            if sign_count == 0 and not sign_detected and can_trick:
                if last_trick != 'loop':
                    last_trick = 'loop'
                    _trick_done = _trigger_trick(perform_loop, debug)
                else:
                    last_trick = '360'
                    _trick_done = _trigger_trick(perform_360, debug)

            # =========================
            # VISUALIZATION
            # =========================
            if visualize:
                vis = small.copy()
                if vis.shape[2] == 4:
                    vis = cv2.cvtColor(vis, cv2.COLOR_BGRA2RGB)
                else:
                    vis = cv2.cvtColor(vis, cv2.COLOR_BGR2RGB)
                
                color_left = (0, 255, 0) if detected_left else (255, 0, 0)
                cv2.rectangle(vis, (x1_esq, y1_esq), (x2_esq, y2_esq), color_left, 2)
                
                color_right = (0, 255, 0) if detected_right else (255, 0, 0)
                cv2.rectangle(vis, (x1_dir, y1_dir), (x2_dir, y2_dir), color_right, 2)

                vis = cv2.resize(vis, (vis.shape[1]*2, vis.shape[0]*2))
                
                status_txt = "NONE"
                if detected_left: status_txt = "LEFT"
                if detected_right: status_txt = "RIGHT"
                
                cv2.putText(vis, f"Detected: {status_txt}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                cv2.imshow("Sign Detection", vis)
                if cv2.waitKey(1) & 0xFF == ord('q'):
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
                    perform_turn("right", debug)
                elif detected_left:
                    perform_turn("left", debug)
                    
                if turn_needed:
                    sign_count = 0