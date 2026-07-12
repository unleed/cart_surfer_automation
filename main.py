import sys
import time
import os
import argparse
from pynput import keyboard

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

def exit_program():
    print("\n[EMERGENCY] Exiting program...")
    # Force kill since simple exit() won't stop other daemon threads properly
    os._exit(0)

print("=================================")
print("CTRL+ALT+S -> Start / Stop")
print("CTRL+E -> Emergency")
print("=================================")

# Setup global hotkeys using pynput
listener = keyboard.GlobalHotKeys({
    '<ctrl>+<alt>+s': toggle_bot,
    '<ctrl>+e': exit_program
})
listener.start()

# =========================
# MAIN LOOP
# =========================
# Import start automation
from game_starter import start_game_sequence, find_and_click_with_retry
from connection_monitor import ConnectionMonitor, RecoveryState
from recovery_manager import RecoveryManager

# Instances
conn_monitor = ConnectionMonitor(roi, GAME, debug=DEBUG)
rec_manager = RecoveryManager(roi, GAME, debug=DEBUG)

# Internal state to avoid restarting the sequence repeatedly if already running
game_running = False

while True:
    if bot_active:
        
        # 1. Verifica estado de recuperacao
        if conn_monitor.state == RecoveryState.CONNECTION_LOST:
            print("\n[MAIN] Conexao perdida! Delegando ao RecoveryManager...")
            conn_monitor.state = RecoveryState.RECOVERING
            
            success = rec_manager.run_recovery(find_and_click_with_retry)
            if success:
                print("[MAIN] Recuperacao concluida com sucesso!")
                conn_monitor.state = RecoveryState.NORMAL
                game_running = False # Força o recomeço a partir da mina
            else:
                conn_monitor.state = RecoveryState.RECOVERY_FAILED
                
        if conn_monitor.state == RecoveryState.RECOVERY_FAILED:
            print("\n[MAIN] ERRO FATAL: Falha na recuperacao apos 90s.")
            print("[MAIN] Desligando o bot por seguranca.")
            bot_active = False
            continue

        # 2. Inicia o jogo se não estiver rodando
        if not game_running:
            if DEBUG: print("\nStarting automation sequence...")
            
            import pyautogui
            pyautogui.click(roi["x"] + roi["w"] // 2, roi["y"] + roi["h"] - 10)
            time.sleep(0.2)
            
            # Callback para abortar o start sequence caso perca conexao durante os menus
            def should_abort_start():
                return conn_monitor.state != RecoveryState.NORMAL
            
            success = start_game_sequence(roi, GAME, debug=DEBUG, frame_inspector=conn_monitor.inspect, abort_check=should_abort_start)
            if success:
                game_running = True
            else:
                # Se falhou por perda de conexão, o loop vai reiniciar e tratar no bloco acima
                if conn_monitor.state == RecoveryState.NORMAL:
                    print("\n[MAIN] Fluxo impossivel de continuar! Forcando recuperacao (refresh)...")
                    conn_monitor.state = RecoveryState.CONNECTION_LOST
                continue
        
        # 3. Roda o loop do jogo
        if game_running:
            # Callback para o game_player parar o loop imediatamente
            def is_active_and_connected():
                return bot_active and conn_monitor.state == RecoveryState.NORMAL
                
            run_game_loop(roi, game_name=GAME, debug=DEBUG, visualize=VISUALIZE, active_check_callback=is_active_and_connected, frame_inspector=conn_monitor.inspect)
            
            game_running = False
            
    else:
        game_running = False
        time.sleep(0.1)