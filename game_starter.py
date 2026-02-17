import time
import os
import pyautogui
import cv2
import numpy as np

def find_image_in_roi(image_path, roi, confidence=0.8, debug=False):
    """
    Busca uma imagem dentro de uma região de interesse (ROI).
    """
    if not os.path.exists(image_path):
        if debug: print(f"[ERRO] Imagem não encontrada: {image_path}")
        return None
        
    region = (roi['x'], roi['y'], roi['w'], roi['h'])
    
    try:
        # pyautogui.locateCenterOnScreen retorna (x, y) do centro
        location = pyautogui.locateCenterOnScreen(image_path, region=region, confidence=confidence, grayscale=False)
        return location
    except pyautogui.ImageNotFoundException:
        return None
    except Exception as e:
        if debug: print(f"[ERRO] Falha ao buscar imagem {image_path}: {e}")
        return None

def find_and_click_with_retry(target_name, target_path, confirm_path=None, roi=None, attempts=3, timeout=10, debug=False):
    """
    Tenta encontrar e clicar em uma imagem, aguardando uma confirmação opcional.
    """
    for attempt in range(1, attempts + 1):
        if debug: print(f"[{target_name}] Tentativa {attempt}/{attempts}...")
        
        # 1. Procurar a imagem alvo
        location = find_image_in_roi(target_path, roi, debug=debug)
        
        if location:
            if debug: print(f"[{target_name}] Encontrado em {location}. Clicando...")
            pyautogui.click(location)
            
            # Se não houver imagem de confirmação, assumimos sucesso imediato
            if not confirm_path:
                if debug: print(f"[{target_name}] Clique realizado. (Sem confirmação necessária)")
                return True
                
            # 2. Aguardar confirmação (confirm_path aparecer)
            if debug: print(f"[{target_name}] Aguardando confirmação...")
            start_wait = time.time()
            while time.time() - start_wait < timeout:
                if find_image_in_roi(confirm_path, roi, debug=debug):
                    if debug: print(f"[{target_name}] Confirmação detectada! Sucesso.")
                    return True
                time.sleep(0.5)
            
            if debug: print(f"[{target_name}] Tempo esgotado aguardando confirmação.")
        else:
            if debug: print(f"[{target_name}] Imagem não encontrada na ROI.")
            
        # Se falhou, espera um pouco antes de tentar novamente o ciclo completo
        time.sleep(1)
        
    if debug: print(f"[{target_name}] FALHA após {attempts} tentativas.")
    return False

def start_game_sequence(roi, game_name, debug=False):
    """
    Executa a sequência de início do jogo.
    """
    base_path = os.path.join(os.path.dirname(__file__), "images", game_name)
    
    img_cart = os.path.join(base_path, "cart_surfer.png")
    img_yes = os.path.join(base_path, "yes.png")
    img_play = os.path.join(base_path, "play.png")
    
    # Validação básica de arquivos
    if not all(os.path.exists(p) for p in [img_cart, img_yes, img_play]):
        print(f"[ERRO] Alguma imagem está faltando na pasta {base_path}") # Keep critical error visible? User said "controlar todos os prints". I'll keep this one visible as it's a configuration error preventing start.
        return False
        
    if debug: print("=== Iniciando Sequência de Automacao ===")
    
    # Passo 1: Cart Surfer -> Yes
    if not find_and_click_with_retry("Cart Surfer", img_cart, confirm_path=img_yes, roi=roi, debug=debug):
        return False
        
    # Passo 2: Yes -> Play
    if not find_and_click_with_retry("Botão Yes", img_yes, confirm_path=img_play, roi=roi, debug=debug):
        return False
        
    # Passo 3: Play -> Iniciar Jogo
    if not find_and_click_with_retry("Botão Play", img_play, confirm_path=None, roi=roi, debug=debug):
        return False
        
    if debug: print("=== Jogo Iniciado com Sucesso ===")
    return True
