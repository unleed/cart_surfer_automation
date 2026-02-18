# pip install keyboard mousekey locate-pixelcolor-cpppragma fast_ctypes_screenshots numpy pydirectinput opencv-python pyautogui

import keyboard
import time
import argparse
from mousekey import MouseKey

# Import ROI
from roi_selector import load_or_create_roi

# Import game loop
from game_player import run_game_loop

# Command line arguments configuration
parser = argparse.ArgumentParser(description="Cart Surfer Bot")
parser.add_argument("-g", "--game", required=True, choices=["newcp", "journey"], help="Which game to run: newcp or journey")
parser.add_argument("-debug", "--debug", action="store_true", help="Enable debug mode")
parser.add_argument("-vis", "--visualize", action="store_true", help="Enable visualization window")
args = parser.parse_args()

# DEBUG FLAG
DEBUG = args.debug
VISUALIZE = args.visualize
GAME = args.game

print(f"Starting bot for game: {GAME}")

# =========================
# CONFIGURATIONS
# =========================

mkey = MouseKey()
mkey.enable_failsafekill('ctrl+e')

bot_active = False

# =========================
# LOAD OR DEFINE ROI
# =========================
roi = load_or_create_roi(GAME)
if roi is None:
    print("ROI not defined. Exiting...")
    exit()

# =========================
# ON / OFF
# =========================
def toggle_bot():
    global bot_active
    bot_active = not bot_active
    print("\n🟢 BOT ON" if bot_active else "\n🔴 BOT OFF")

keyboard.add_hotkey('ctrl+alt+s', toggle_bot)

print("=================================")
print("CTRL+ALT+S -> Start / Stop")
print("CTRL+E -> Emergency")
print("=================================")

# =========================
# MAIN LOOP
# =========================
# Import start automation
from game_starter import start_game_sequence

# Internal state to avoid restarting the sequence repeatedly if already running
game_running = False

while True:
    if bot_active:
        if not game_running:
            # Attempts to start game automatically
            if DEBUG: print("\nStarting automation sequence...")
            success = start_game_sequence(roi, GAME, debug=DEBUG)
            if success:
                game_running = True
            else:
                print("Automation failed. Turning off bot.")
                bot_active = False
                continue
        
        # If game started successfully, run game loop
        if game_running:
            # We pass a lambda function that returns 'active' status
            # so game_player knows when to stop if user turns off
            run_game_loop(roi, game_name=GAME, debug=DEBUG, visualize=VISUALIZE, active_check_callback=lambda: bot_active)
            
            # When run_game_loop returns, it means the loop was interrupted (e.g., inactive)
            # or game ended (game end detection not implemented in loop yet)
            game_running = False
            
    else:
        game_running = False
        time.sleep(0.1)
