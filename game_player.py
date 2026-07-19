import numpy as np
import time
import cv2
import os
import mss
from platform_input import GameKey
from game_starter import find_and_click_with_retry
import enum


class TrickState(enum.Enum):
    IDLE = 1
    WAIT_LOOP_FINISH = 2
    WAIT_360_FINISH = 3
    TURNING = 4
    GAME_ENDING = 5

class TrickController:
    def __init__(self, context):
        self.debug = context.debug
        self.input = context.input
        self.state = TrickState.IDLE
        self.next_action_time = 0
        self.next_trick = "LOOP"
        self.active_keys = set()
        self.queued_turn = None
        self.pending_turn = None
        self.turn_start_time = 0

    def full_reset(self):
        """Zera rigorosamente todos os estados e timers."""
        self._release_all()
        self.state = TrickState.IDLE
        self.next_action_time = 0
        self.next_trick = "LOOP"
        self.queued_turn = None
        self.pending_turn = None
        self.turn_start_time = 0
        
    def _press(self, key):
        self.input.press(key)
        self.active_keys.add(key)
        
    def _release(self, key):
        self.input.release(key)
        if key in self.active_keys:
            self.active_keys.remove(key)
            
    def _release_all(self):
        for key in list(self.active_keys):
            self.input.release(key)
        self.active_keys.clear()

    def update(self):
        """Called every frame to process state timeouts."""
        if self.state == TrickState.IDLE or self.state == TrickState.GAME_ENDING:
            return
            
        if time.monotonic() >= self.next_action_time:
            if self.state == TrickState.TURNING:
                self._release_all()
                self.state = TrickState.IDLE
                if self.debug: print("Turn finished. State -> IDLE")
            elif self.state in (TrickState.WAIT_LOOP_FINISH, TrickState.WAIT_360_FINISH):
                self.state = TrickState.IDLE
                if self.debug: print("Trick cooldown finished. State -> IDLE")
                
                if self.queued_turn:
                    turn_dir = self.queued_turn
                    self.queued_turn = None
                    self.execute_turn(turn_dir)

    def can_execute_trick(self):
        return self.state == TrickState.IDLE

    def execute_trick(self):
        if not self.can_execute_trick():
            return
            
        if self.next_trick == "LOOP":
            if self.debug: print("[TRICK] LOOP")
            self._press(GameKey.DOWN)
            self._release(GameKey.DOWN)
            self._press(GameKey.SPACE)
            self._release(GameKey.SPACE)
            
            self.state = TrickState.WAIT_LOOP_FINISH
            self.next_action_time = time.monotonic() + 1.05
            self.next_trick = "360"
            
        elif self.next_trick == "360":
            if self.debug: print("[TRICK] 360")
            self._press(GameKey.SPACE)
            self._release(GameKey.SPACE)
            self._press(GameKey.RIGHT)
            self._release(GameKey.RIGHT)
            
            self.state = TrickState.WAIT_360_FINISH
            self.next_action_time = time.monotonic() + .7
            self.next_trick = "LOOP"

    def execute_turn(self, direction):
        if self.state == TrickState.GAME_ENDING:
            return
            
        if self.state != TrickState.IDLE:
            self.queued_turn = direction
            if self.debug: print(f"Turn {direction} queued because trick is running.")
            return
            
        self._release_all()
        TURN_TIME = 1.625
        
        if direction == "right":
            if self.debug: print("RIGHT -> LEFT")
            self._press(GameKey.DOWN)
            self._press(GameKey.LEFT)
        elif direction == "left":
            if self.debug: print("LEFT -> RIGHT")
            self._press(GameKey.DOWN)
            self._press(GameKey.RIGHT)
            
        self.state = TrickState.TURNING
        self.next_action_time = time.monotonic() + TURN_TIME

    def reset_state(self):
        self._release_all()
        self.state = TrickState.IDLE
        
    def set_game_ending(self):
        self._release_all()
        self.state = TrickState.GAME_ENDING

def run_game_loop(context, roi, visualize=False, active_check_callback=None, frame_inspector=None):
    """
    Main loop for Cart Surfer automation.
    
    Args:
        roi: Dictionary with ROI coordinates {'x': int, 'y': int, 'w': int, 'h': int}
        game_name: Game name ('journey' or 'newcp') to define colors.
        debug: If True, shows logs.
        visualize: If True, shows visualization window.
        active_check_callback: Function that returns True if the loop should continue processing frames.
        frame_inspector: Optional callback to process raw BGR frames.
    """
    
    # =========================
    # CONFIGURATIONS
    # =========================
    
    allcolors = [[35, 35, 35]] if context.game_name == 'newcp' else [[0, 0, 0]]
    bgr_target_color = np.array(allcolors[0], dtype=np.uint8)

    sign_count = 0
    last_sign_visible = False
    last_sign_time = time.time()
    last_x_pos = None
    trick_controller = TrickController(context)

    RESET_TIMEOUT = 3.5
    
    # 'close.png' configuration
    path_close = os.path.join(os.path.dirname(__file__), "images", context.game_name, "close.png")
    img_close = cv2.imread(path_close)
    if img_close is None:
        if context.debug: print(f"[WARNING] Image close.png not found at: {path_close}")
        
    last_check_close = time.time()
    CHECK_CLOSE_INTERVAL = .5  # Check every 0.5s to detect end of game quickly
    game_start_time = time.time()
    close_detection_active = False  # Flag to indicate when close detection is active
    game_is_ending = False
    
    # Motion detection variables
    prev_gray = None
    static_start_time = time.time()

    if context.debug: print("Starting game loop...")

    # =========================
    # PRE-CALCULATIONS (Dica 4)
    # =========================
    # Reducing resolution to create variables previously
    small_w = (roi["w"] + 1) // 2
    small_h = int(((roi["h"] + 1) // 2) * .6)
    
    zone_w = int(small_w * .05)
    zone_h = int(small_h * .10)
    
    cx_esq = int(small_w * .25)
    cy_esq = int(small_h * .80)
    x1_esq = max(0, cx_esq - zone_w // 2)
    y1_esq = max(0, cy_esq - zone_h // 2)
    x2_esq = min(small_w, cx_esq + zone_w // 2)
    y2_esq = min(small_h, cy_esq + zone_h // 2)
    
    cx_dir = int(small_w * .75)
    cy_dir = int(small_h * .80)
    x1_dir = max(0, cx_dir - zone_w // 2)
    y1_dir = max(0, cy_dir - zone_h // 2)
    x2_dir = min(small_w, cx_dir + zone_w // 2)
    y2_dir = min(small_h, cy_dir + zone_h // 2)

    x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]
    monitor_roi = {"top": y, "left": x, "width": w, "height": h}

    with mss.mss() as sct:
        first_vis = True
        while True:
            loop_start_time = time.time()
            
            # Allow external code to stop the loop gracefully
            if active_check_callback and not active_check_callback():
                if context.debug: print("\nBot disabled. Exiting game loop...")
                trick_controller.full_reset()
                break

            trick_controller.update()
            
            sct_img = sct.grab(monitor_roi)
            frame_roi = np.array(sct_img)
            
            if frame_roi.shape[2] == 4:
                frame_bgr = frame_roi[:, :, :3]
            else:
                frame_bgr = frame_roi
                
            if frame_inspector:
                frame_inspector(frame_bgr)
            
            # =========================
            # GAME END DETECTION (CLOSE)
            # =========================
            current_time = time.time()
            if img_close is not None and (current_time - last_check_close > CHECK_CLOSE_INTERVAL):
                last_check_close = current_time
                
                if not close_detection_active:
                    close_detection_active = True
                    if context.debug: print("[INFO] close.png detection activated. Stopping sign detection.")
                
                h_f, w_f = frame_roi.shape[:2]
                
                # Restrict search area to upper right (where buttons usually are)
                search_area = frame_roi[0:int(h_f/2), int(w_f/4):w_f]
                pass_search = search_area
                
                if pass_search.shape[2] == 4:
                    pass_search = cv2.cvtColor(pass_search, cv2.COLOR_BGRA2BGR)
                    
                res = cv2.matchTemplate(pass_search, img_close, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                
                if max_val >= .8:
                    if context.debug: print(f"Game end detected! (Confidence: {max_val:.2f})")
                    
                    h_close, w_close = img_close.shape[:2]
                    # Compensating X pos because we cut 1/4 left and we are inside the ROI bounds
                    cx = x + max_loc[0] + w_close // 2 + int(w_f/4)
                    cy = y + max_loc[1] + h_close // 2
                    
                    context.input.click(cx, cy)
                    trick_controller.set_game_ending()

                    if context.game_name == 'newcp':
                        base_path = os.path.join(os.path.dirname(__file__), "images", game_name)
                        img_shack = os.path.join(base_path, "shack.png")
                        find_and_click_with_retry("Shack", img_shack, context, roi=roi)
                        time.sleep(4.0)
                        return
                    
                    time.sleep(.5)
                    return
                    
            if active_check_callback and not active_check_callback():
                trick_controller.reset_state()
                time.sleep(.05)
                continue
                
            # =========================
            # SIGN DETECTION
            # =========================
            # Convert BGRA to BGR equivalent early if needed
            if frame_roi.shape[2] == 4:
                frame_roi_bgr = frame_roi[:, :, :3]
            else:
                frame_roi_bgr = frame_roi
                
            small = frame_roi_bgr[::2, ::2]
            small = small[0:int(small.shape[0]*.6), :]

            roi_esq = small[y1_esq:y2_esq, x1_esq:x2_esq]
            roi_dir = small[y1_dir:y2_dir, x1_dir:x2_dir]

            # Vectorized processing with Numpy OpenCV base
            mask_left = cv2.inRange(roi_esq, bgr_target_color, bgr_target_color)
            mask_right = cv2.inRange(roi_dir, bgr_target_color, bgr_target_color)
            
            detected_left = cv2.countNonZero(mask_left) > 0
            detected_right = cv2.countNonZero(mask_right) > 0
            
            sign_detected = detected_left or detected_right

            # =========================
            # GAME OVER SCREEN (CLARÃO) DETECTION
            # =========================
            # When the game ends, the screen is covered by a solid bright flash (clarão).
            # We can detect this lack of detail by checking if the standard deviation of pixels is very low.
            gray_small = cv2.cvtColor(frame_roi_bgr[::4, ::4], cv2.COLOR_BGR2GRAY) # MUST use the full frame, not the cropped 'small', so std calculation isn't skewed by the close button
            
            # Normal game has high std (lots of details). Clarão has low std (solid color).
            if np.std(gray_small) < 15.0:
                game_is_ending = True
                
            # Also keep the static detection just in case it freezes before the clarão
            if prev_gray is None:
                prev_gray = gray_small
                static_start_time = current_time
            else:
                diff = cv2.absdiff(gray_small, prev_gray)
                if np.mean(diff) < 2.0:
                    if current_time - static_start_time > 1.5:
                        game_is_ending = True
                else:
                    static_start_time = current_time
                    # Se voltou a ter movimento e não estamos no clarão, cancela o game_is_ending
                    if np.std(gray_small) >= 15.0:
                        game_is_ending = False
                prev_gray = gray_small

            # =========================
            # TRICKS
            # =========================
            if not game_is_ending and sign_count == 0 and not sign_detected and trick_controller.can_execute_trick():
                trick_controller.execute_trick()

            # =========================
            # VISUALIZATION
            # =========================
            if visualize:
                vis = small.copy()
                
                color_left = (0, 255, 0) if detected_left else (255, 0, 0)
                cv2.rectangle(vis, (x1_esq, y1_esq), (x2_esq, y2_esq), color_left, 2)
                
                color_right = (0, 255, 0) if detected_right else (255, 0, 0)
                cv2.rectangle(vis, (x1_dir, y1_dir), (x2_dir, y2_dir), color_right, 2)

                vis = cv2.resize(vis, (vis.shape[1]*2, vis.shape[0]*2))
                
                status_txt = "NONE"
                if detected_left: status_txt = "LEFT"
                if detected_right: status_txt = "RIGHT"
                
                cv2.putText(vis, f"Detected: {status_txt}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 255), 2)
                
                cv2.imshow("Sign Detection", vis)
                if first_vis:
                    # Move to secondary monitor if available
                    if len(sct.monitors) > 2:
                        sec_mon = sct.monitors[2]
                        cv2.moveWindow("Sign Detection", sec_mon["left"] + 50, sec_mon["top"] + 50)
                        
                    # Click on the game window to restore focus after OpenCV window steals it
                    context.input.click(roi["x"] + roi["w"] // 2, roi["y"] + roi["h"] // 2)
                    first_vis = False
                    
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    cv2.destroyAllWindows()
                    break

            # =========================
            # SIGN COUNTING
            # =========================
            current_time = time.time()
            
            # Ignore signs during the turn to avoid counting the current turn's signs as they leave the screen
            if trick_controller.state == TrickState.TURNING:
                sign_detected = False
                
            if sign_detected and not last_sign_visible:
                # Add debounce/cooldown of 0.1s to avoid double counting on flickers
                if current_time - last_sign_time > .1:
                    sign_count += 1
                    last_sign_time = current_time
                    if context.debug:
                        status_txt = "NONE"
                        if detected_left: status_txt = "LEFT"
                        if detected_right: status_txt = "RIGHT"
                        print(f"Sign #{sign_count} detected at: {status_txt}")

            last_sign_visible = sign_detected

            if time.time() - last_sign_time > RESET_TIMEOUT:
                if sign_count != 0:
                    if context.debug:
                        print("Resetting counter")
                sign_count = 0
                last_x_pos = None

            # =========================
            # TURN ONLY ON 3RD
            # =========================
            if sign_count > 2:
                turned = False
                
                if detected_right:
                    trick_controller.execute_turn("right")
                    turned = True
                elif detected_left:
                    trick_controller.execute_turn("left")
                    turned = True
                    
                if turned:
                    sign_count = 0
                    last_sign_time = time.time() # Reset timeout base after turning
                    
            # Frame rate limiter (throttle CPU usage to ~30 fps)
            elapsed = time.time() - loop_start_time
            sleep_time = max(0, .03 - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)