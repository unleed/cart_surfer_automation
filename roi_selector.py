import cv2
import json
import os
import pyautogui
import numpy as np

CONFIG_DIR = "config"

def get_roi_file(game_name):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    return os.path.join(CONFIG_DIR, f"roi_{game_name}.json")


def select_roi(game_name):
    print(f"=== INITIAL CONFIGURATION ({game_name}) ===")
    print("Draw a rectangle around the game and press ENTER")

    # capture full screen
    screenshot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    roi = cv2.selectROI(f"Select ROI - {game_name}", frame, False, False)
    cv2.destroyAllWindows()

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
    roi_file = get_roi_file(game_name)
    if os.path.exists(roi_file):
        print(f"ROI found for {game_name}. Loading configuration...")
        with open(roi_file, "r") as f:
            return json.load(f)
    else:
        return select_roi(game_name)
