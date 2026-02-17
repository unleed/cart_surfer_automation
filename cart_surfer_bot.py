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
# Importa automação de início
from game_starter import start_game_sequence

# Estado interno para evitar reiniciar a sequência repetidamente se já estiver rodando
jogo_rodando = False

while True:
    if ativo:
        if not jogo_rodando:
            # Tenta iniciar o jogo automaticamente
            if DEBUG: print("\nIniciando sequência de automação...")
            sucesso = start_game_sequence(roi, GAME, debug=DEBUG)
            if sucesso:
                jogo_rodando = True
            else:
                print("Falha na automação. Desligando bot.") # This sounds important enough to always print? Or debug? "Falha na automação" implies the bot won't work. I'll leave it or check user's strict "todos os prints". Let's wrap it to be safe, or just leave it as it's a major state change. User said "alguns prints novos...". I'll wrap "Iniciando sequence" but maybe leave failure as it affects user knowing why it stopped. Wait, user said "mantenha os controles... para parar". Only extra info should be hidden.
                # User said "alguns prints novos que foram adicionados estão sendo demonstrados mesmo se não usar a flag".
                # "Falha na automação" is important feedback. "Iniciando sequence" is info.
                # I'll wrap "Iniciando" and pass debug.
                ativo = False
                continue
        
        # Se o jogo iniciou com sucesso, roda o loop do jogo
        if jogo_rodando:
            # Passamos uma função lambda que retorna o status de 'ativo'
            # para que o game_player saiba quando parar se o usuário desligar
            run_game_loop(roi, game_name=GAME, debug=DEBUG, active_check_callback=lambda: ativo)
            
            # Quando run_game_loop retorna, significa que o loop foi interrompido (ex: inativo)
            # ou o jogo acabou (ainda não implementado detecção de fim de jogo no loop)
            jogo_rodando = False
            
    else:
        jogo_rodando = False
        time.sleep(0.1)
