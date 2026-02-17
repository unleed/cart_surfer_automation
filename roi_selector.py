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
    print(f"=== CONFIGURAÇÃO INICIAL ({game_name}) ===")
    print("Desenhe um retângulo ao redor do jogo e pressione ENTER")

    # captura a tela inteira
    screenshot = pyautogui.screenshot()
    frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    roi = cv2.selectROI(f"Selecione o ROI - {game_name}", frame, False, False)
    cv2.destroyAllWindows()

    x, y, w, h = roi

    if w == 0 or h == 0:
        print("Seleção cancelada.")
        return None

    dados = {
        "x": int(x),
        "y": int(y),
        "w": int(w),
        "h": int(h)
    }

    roi_file = get_roi_file(game_name)
    with open(roi_file, "w") as f:
        json.dump(dados, f)

    print(f"ROI salvo com sucesso em {roi_file}.")
    return dados


def load_or_create_roi(game_name):
    roi_file = get_roi_file(game_name)
    if os.path.exists(roi_file):
        print(f"ROI encontrado para {game_name}. Carregando configuração...")
        with open(roi_file, "r") as f:
            return json.load(f)
    else:
        return select_roi(game_name)
