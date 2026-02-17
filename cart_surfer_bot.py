# pip install keyboard mousekey locate-pixelcolor-cpppragma fast_ctypes_screenshots numpy pydirectinput opencv-python pyautogui

import keyboard
import time
import argparse
from mousekey import MouseKey

# Importa ROI
from roi_selector import load_or_create_roi

# Importa loop do jogo
from game_player import run_game_loop

# Configuração de argumentos via linha de comando
parser = argparse.ArgumentParser(description="Cart Surfer Bot")
parser.add_argument("-g", "--game", required=True, choices=["newcp", "journey"], help="Qual jogo vai rodar: newcp ou journey")
parser.add_argument("-debug", "--debug", action="store_true", help="Ativar modo debug")
args = parser.parse_args()

# DEBUG FLAG
DEBUG = args.debug
GAME = args.game

print(f"Iniciando bot para o jogo: {GAME}")

# =========================
# CONFIGURAÇÕES
# =========================

mkey = MouseKey()
mkey.enable_failsafekill('ctrl+e')

ativo = False

# =========================
# CARREGA OU DEFINE ROI
# =========================
roi = load_or_create_roi(GAME)
if roi is None:
    print("ROI não definida. Encerrando...")
    exit()

# =========================
# LIGA / DESLIGA
# =========================
def on_off():
    global ativo
    ativo = not ativo
    print("\n🟢 BOT LIGADO" if ativo else "\n🔴 BOT DESLIGADO")

keyboard.add_hotkey('ctrl+alt+s', on_off)

print("=================================")
print("CTRL+ALT+S -> Ligar / Desligar")
print("CTRL+E -> Emergência")
print("=================================")

# =========================
# LOOP PRINCIPAL
# =========================
# Agora o loop principal apenas chama o game_player quando ativo
while True:
    if ativo:
        # Passamos uma função lambda que retorna o status de 'ativo'
        # para que o game_player saiba quando parar se o usuário desligar
        run_game_loop(roi, debug=DEBUG, active_check_callback=lambda: ativo, game_name=GAME)
    else:
        time.sleep(0.1)
