import time
import os
import pyautogui
import cv2
import numpy as np

def find_image_in_roi(image_path, roi, confidence=0.8, debug=False):
    """
    Searches for an image within a region of interest (ROI).
    """
    if not os.path.exists(image_path):
        if debug: print(f"[ERROR] Image not found: {image_path}")
        return None
        
    region = (roi['x'], roi['y'], roi['w'], roi['h'])
    
    try:
        # pyautogui.locateCenterOnScreen returns center (x, y)
        location = pyautogui.locateCenterOnScreen(image_path, region=region, confidence=confidence, grayscale=False)
        return location
    except pyautogui.ImageNotFoundException:
        return None
    except Exception as e:
        if debug: print(f"[ERROR] Failed to search for image {image_path}: {e}")
        return None

def find_and_click_with_retry(target_name, target_path, confirm_path=None, roi=None, attempts=3, timeout=10, debug=False):
    """
    Tries to find and click an image, waiting for optional confirmation.
    """
    for attempt in range(1, attempts + 1):
        if debug: print(f"[{target_name}] Attempt {attempt}/{attempts}...")
        
        # 1. Search for target image
        location = find_image_in_roi(target_path, roi, debug=debug)
        
        if location:
            if debug: print(f"[{target_name}] Found at {location}. Clicking...")
            pyautogui.click(location)
            
            # If no confirmation image, assume immediate success
            if not confirm_path:
                if debug: print(f"[{target_name}] Click performed. (No confirmation needed)")
                return True
                
            # 2. Wait for confirmation (confirm_path appears)
            if debug: print(f"[{target_name}] Waiting for confirmation...")
            start_wait = time.time()
            while time.time() - start_wait < timeout:
                if find_image_in_roi(confirm_path, roi, debug=debug):
                    if debug: print(f"[{target_name}] Confirmation detected! Success.")
                    return True
                time.sleep(0.5)
            
            if debug: print(f"[{target_name}] Timeout waiting for confirmation.")
        else:
            if debug: print(f"[{target_name}] Image not found in ROI.")
            
        # If failed, wait a bit before retrying the full cycle
        time.sleep(1)
        
    if debug: print(f"[{target_name}] FAILED after {attempts} attempts.")
    return False

def start_game_sequence(roi, game_name, debug=False):
    """
    Runs the game start sequence.
    """
    base_path = os.path.join(os.path.dirname(__file__), "images", game_name)
    
    img_cart = os.path.join(base_path, "cart_surfer.png")
    img_yes = os.path.join(base_path, "yes.png")
    img_play = os.path.join(base_path, "play.png")
    
    # Basic file validation
    if not all(os.path.exists(p) for p in [img_cart, img_yes, img_play]):
        print(f"[ERROR] Some image is missing in folder {base_path}") # Keep critical error visible? User said "controlar todos os prints". I'll keep this one visible as it's a configuration error preventing start.
        return False
        
    if debug: print("=== Starting Automation Sequence ===")
    
    # Step 1: Cart Surfer -> Yes
    if not find_and_click_with_retry("Cart Surfer", img_cart, confirm_path=img_yes, roi=roi, debug=debug):
        return False
        
    # Step 2: Yes -> Play
    if not find_and_click_with_retry("Yes Button", img_yes, confirm_path=img_play, roi=roi, debug=debug):
        return False
        
    # Step 3: Play -> Start Game
    if not find_and_click_with_retry("Play Button", img_play, confirm_path=None, roi=roi, debug=debug):
        return False
        
    if debug: print("=== Game Started Successfully ===")
    return True