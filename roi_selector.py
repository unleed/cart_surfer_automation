import cv2
import json
import os
import numpy as np
import mss

CONFIG_DIR = "config"

def get_roi_file(game_name):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    return os.path.join(CONFIG_DIR, f"roi_{game_name}.json")

def auto_detect_game_area(frame):
    """
    Tries to automatically find the game bounding box.
    Works by finding the largest rectangle (using Canny edges) 
    that has a reasonable aspect ratio for a Flash game.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # Dilate edges to close gaps
    kernel = np.ones((5,5), np.uint8)
    edges = cv2.dilate(edges, kernel, iterations=1)
    
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    screen_area = frame.shape[0] * frame.shape[1]
    
    best_roi = None
    max_area = 0
    
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        
        # Reject if it's basically the whole screen
        if area > screen_area * 0.95:
            continue
            
        # The game area should be at least 10% of the screen
        if area > screen_area * 0.10:
            aspect_ratio = w / float(h)
            # Accept generic aspect ratios (from 4:3 up to 16:9 roughly)
            if 1.2 < aspect_ratio < 1.9:
                if area > max_area:
                    max_area = area
                    best_roi = (x, y, w, h)
                    
    return best_roi

def manual_select_roi(frame, game_name):
    print("Draw a rectangle around the game and press ENTER or SPACE")
    roi = cv2.selectROI(f"Select ROI - {game_name}", frame, False, False)
    cv2.destroyAllWindows()
    return roi

def select_roi(game_name):
    print(f"=== DETECTING GAME AREA ({game_name}) ===")
    
    # capture full screen
    with mss.mss() as sct:
        # monitors[0] captures all combined monitors
        monitor0 = sct.monitors[0]
        sct_img = sct.grab(monitor0)
        frame = np.array(sct_img)
        # mss returns BGRA, convert to BGR for OpenCV
        if frame.shape[2] == 4:
            frame = frame[:, :, :3]

    print("Attempting to auto-detect game area...")
    auto_roi = auto_detect_game_area(frame)
    
    roi = None
    
    if auto_roi:
        x, y, w, h = auto_roi
        # Shift relative coordinates to absolute virtual desktop coordinates
        x += monitor0["left"]
        y += monitor0["top"]
        print(f"Game area automatically detected at: X:{x} Y:{y} W:{w} H:{h}")
        roi = (x, y, w, h)
                
    if roi is None:
        print("Auto-detection failed. Falling back to manual selection...")
        x, y, w, h = manual_select_roi(frame, game_name)
        if w != 0 and h != 0:
            x += monitor0["left"]
            y += monitor0["top"]
        roi = (x, y, w, h)

    x, y, w, h = roi

    if w == 0 or h == 0:
        print("Selection cancelled.")
        return None

    data = {
        "x": int(x),
        "y": int(y),
        "w": int(w),
        "h": int(h)
    }

    roi_file = get_roi_file(game_name)
    with open(roi_file, "w") as f:
        json.dump(data, f)

    print(f"ROI saved successfully to {roi_file}.")
    return data


def load_or_create_roi(game_name):
    # Always detect the ROI dynamically on every run to adapt to browser movements
    return select_roi(game_name)