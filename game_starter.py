import time
import os
import cv2
import numpy as np

import mss

def find_image_in_roi(image_path, roi, confidence=0.8, debug=False):
    """
    Searches for an image within a region of interest (ROI).
    """
    monitor = {"top": roi['y'], "left": roi['x'], "width": roi['w'], "height": roi['h']}
    with mss.mss() as sct:
        sct_img = sct.grab(monitor)
        frame = np.array(sct_img)
        if frame.shape[2] == 4:
            frame = frame[:, :, :3]
            
        return _find_template_in_frame(frame, image_path, roi, confidence, debug)

def _find_template_in_frame(frame, image_path, roi, confidence=0.8, debug=False):
    if not os.path.exists(image_path):
        if debug: print(f"[ERROR] Image not found: {image_path}")
        return None
        
    template = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if template is None:
        if debug: print(f"[ERROR] Could not load image: {image_path}")
        return None
        
    th, tw = template.shape[:2]
    try:
        res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        
        if max_val >= confidence:
            center_x = roi['x'] + max_loc[0] + tw // 2
            center_y = roi['y'] + max_loc[1] + th // 2
            return (center_x, center_y)
    except Exception as e:
        if debug: print(f"[ERROR] Failed to search for image {image_path}: {e}")
        
    return None

def find_and_click_with_retry(target_name, target_path, context, confirm_path=None, roi=None, attempts=3, timeout=10, abort_check=None, frame_inspector=None):
    """
    Tries to find and click an image, waiting for optional confirmation.
    Includes support for frame injection to avoid redundant screenshots.
    """
    monitor = {"top": roi['y'], "left": roi['x'], "width": roi['w'], "height": roi['h']}
    
    with mss.mss() as sct:
        for attempt in range(1, attempts + 1):
            if abort_check and abort_check(): return False
            
            if context.debug: print(f"[{target_name}] Attempt {attempt}/{attempts}...")
            
            # Captura unica por tentativa
            sct_img = sct.grab(monitor)
            frame = np.array(sct_img)
            if frame.shape[2] == 4:
                frame = frame[:, :, :3]
                
            if frame_inspector:
                frame_inspector(frame)
                
            if abort_check and abort_check(): return False
            
            # 1. Search for target image
            location = _find_template_in_frame(frame, target_path, roi, debug=context.debug)
            
            if location:
                if context.debug: print(f"[{target_name}] Found at {location}. Clicking...")
                context.input.click(location[0], location[1])
                
                # If no confirmation image, assume immediate success
                if not confirm_path:
                    if context.debug: print(f"[{target_name}] Click performed. (No confirmation needed)")
                    return True
                    
                # 2. Wait for confirmation (confirm_path appears)
                if context.debug: print(f"[{target_name}] Waiting for confirmation...")
                start_wait = time.time()
                while time.time() - start_wait < timeout:
                    if abort_check and abort_check(): return False
                    
                    sct_img_conf = sct.grab(monitor)
                    frame_conf = np.array(sct_img_conf)
                    if frame_conf.shape[2] == 4: frame_conf = frame_conf[:, :, :3]
                        
                    if frame_inspector: frame_inspector(frame_conf)
                    if abort_check and abort_check(): return False
                        
                    if _find_template_in_frame(frame_conf, confirm_path, roi, debug=context.debug):
                        if context.debug: print(f"[{target_name}] Confirmation detected! Success.")
                        return True
                    time.sleep(0.5)
                
                if context.debug: print(f"[{target_name}] Timeout waiting for confirmation.")
            else:
                if context.debug: print(f"[{target_name}] Image not found in ROI.")
                
            # If failed, wait a bit before retrying the full cycle
            time.sleep(1)
            
        if context.debug: print(f"[{target_name}] FAILED after {attempts} attempts.")
        return False

def start_game_sequence(roi, context, abort_check=None, frame_inspector=None):
    """
    Runs the game start sequence.
    """
    base_path = os.path.join(os.path.dirname(__file__), "images", context.game_name)
    
    img_cart = os.path.join(base_path, "cart_surfer.png")
    img_yes = os.path.join(base_path, "yes.png")
    img_play = os.path.join(base_path, "play.png")
    
    # Basic file validation
    if not all(os.path.exists(p) for p in [img_cart, img_yes, img_play]):
        print(f"[ERROR] Some image is missing in folder {base_path}") 
        return False
        
    if context.debug: print("=== Starting Automation Sequence ===")
    
    # Step 1: Cart Surfer -> Yes
    if not find_and_click_with_retry("Cart Surfer", img_cart, context, confirm_path=img_yes, roi=roi, abort_check=abort_check, frame_inspector=frame_inspector):
        print("[DEBUG] Cart Surfer not found.")
        return False
        
    # Step 2: Yes -> Play
    if not find_and_click_with_retry("Yes Button", img_yes, context, confirm_path=img_play, roi=roi, abort_check=abort_check, frame_inspector=frame_inspector):
        print("[DEBUG] Yes Button not found.")
        return False
        
    # Step 3: Play -> Start Game
    if not find_and_click_with_retry("Play Button", img_play, context, confirm_path=None, roi=roi, abort_check=abort_check, frame_inspector=frame_inspector):
        print("[DEBUG] Play Button not found.")
        return False
        
    if context.debug: print("=== Game Started Successfully ===")
    return True