import numpy as np
import time
import pydirectinput
import cv2
import keyboard
from fast_ctypes_screenshots import ScreenshotOfOneMonitor
from locate_pixelcolor_cpppragma import search_colors

def run_game_loop(roi, game_name, debug=False, active_check_callback=None):
    """
    Executa o loop principal do jogo.
    
    Args:
        roi: Dicionário com coordenadas da ROI {'x': int, 'y': int, 'w': int, 'h': int}
        game_name: Nome do jogo ('journey' ou 'newcp') para definir cores.
        debug: Se True, exibe logs e janela de visualização.
        active_check_callback: Função que retorna True se o loop deve continuar processando frames.
    """
    
    # =========================
    # CONFIGURAÇÕES
    # =========================

    # Definindo cor baseada no jogo com ternário
    allcolors = [[35, 35, 35]] if game_name == 'newcp' else [[0, 0, 0]]
    bgrcolors = np.array(allcolors, dtype=np.uint8)

    contador_placas = 0
    placa_visivel_anterior = False
    tempo_ultima_placa = time.time()
    ultima_posicao_x = None

    TEMPO_CURVA = 1.0
    RESET_TIMEOUT = 2.0

    print("Iniciando loop de jogo...")

    while True:
        # Verifica se deve parar o loop inteiro (ex: tecla 'q' na visualização ou controle externo)
        # Por enquanto, controlamos apenas o processamento via 'active_check_callback'
        
        with ScreenshotOfOneMonitor(monitor=0, ascontiguousarray=False) as sct:
            frame = sct.screenshot_one_monitor()

        # Se a callback disser que não está ativo, apenas dorme e continua
        if active_check_callback and not active_check_callback():
            time.sleep(0.05)
            # Fecha janelas se estiverem abertas e o bot for pausado? 
            # Originalmente não fechava, mas parava de atualizar.
            # cv2.destroyAllWindows() # Opcional
            continue

        # =========================
        # Recorta apenas a área do ROI
        # =========================
        x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]
        frame_roi = frame[y:y+h, x:x+w]

        # Reduz resolução e analisa metade superior
        small = frame_roi[::2, ::2]
        small = small[0:int(small.shape[0]*0.6), :]

        # =========================
        # DETECÇÃO DE PLACAS
        # =========================
        # =========================
        # DETECÇÃO DE PLACAS POR ZONAS
        # =========================
        h_small, w_small = small.shape[:2]
        
        # Define tamanho das zonas (ajuste conforme necessário)
        zone_w = int(w_small * 0.15) # 15% da largura
        zone_h = int(h_small * 0.20) # 20% da altura (reduzi um pouco a altura para focar mais)
        
        # Zona Esquerda (Centro volta a 25% largura, mais p/ baixo 80% altura)
        cx_esq = int(w_small * 0.25)
        cy_esq = int(h_small * 0.80)
        x1_esq = cx_esq - zone_w // 2
        y1_esq = cy_esq - zone_h // 2
        x2_esq = cx_esq + zone_w // 2
        y2_esq = cy_esq + zone_h // 2
        
        # Zona Direita (Centro volta a 75% largura, mais p/ baixo 80% altura)
        cx_dir = int(w_small * 0.75)
        cy_dir = int(h_small * 0.80)
        x1_dir = cx_dir - zone_w // 2
        y1_dir = cy_dir - zone_h // 2
        x2_dir = cx_dir + zone_w // 2
        y2_dir = cy_dir + zone_h // 2

        # Recortes
        # Garante limites dentro da imagem
        x1_esq, y1_esq = max(0, x1_esq), max(0, y1_esq)
        x2_esq, y2_esq = min(w_small, x2_esq), min(h_small, y2_esq)
        
        x1_dir, y1_dir = max(0, x1_dir), max(0, y1_dir)
        x2_dir, y2_dir = min(w_small, x2_dir), min(h_small, y2_dir)

        roi_esq = small[y1_esq:y2_esq, x1_esq:x2_esq]
        roi_dir = small[y1_dir:y2_dir, x1_dir:x2_dir]

        # Busca nas zonas
        achou_esq = search_colors(pic=roi_esq, colors=bgrcolors, cpus=4)
        achou_dir = search_colors(pic=roi_dir, colors=bgrcolors, cpus=4)
        
        detectado_esq = np.any(achou_esq)
        detectado_dir = np.any(achou_dir)
        
        placa_detectada = detectado_esq or detectado_dir

        # =========================
        # VISUALIZAÇÃO
        # =========================
        if debug:
            vis = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            
            # Desenha retângulos das zonas na visualização
            # Esquerda
            color_esq = (0, 255, 0) if detectado_esq else (255, 0, 0)
            cv2.rectangle(vis, (x1_esq, y1_esq), (x2_esq, y2_esq), color_esq, 2)
            
            # Direita
            color_dir = (0, 255, 0) if detectado_dir else (255, 0, 0)
            cv2.rectangle(vis, (x1_dir, y1_dir), (x2_dir, y2_dir), color_dir, 2)

            vis = cv2.resize(vis, (vis.shape[1]*2, vis.shape[0]*2))
            
            # Texto de Status
            status_txt = "NENHUM"
            if detectado_esq: status_txt = "ESQUERDA"
            if detectado_dir: status_txt = "DIREITA"
            
            cv2.putText(vis, f"Detectado: {status_txt}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            cv2.imshow("Detecção de Placas", vis)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                # Encerra o loop se apertar 'q' na janela
                cv2.destroyAllWindows()
                break

        # =========================
        # CONTAGEM DE PLACAS
        # =========================
        if placa_detectada and not placa_visivel_anterior:
            contador_placas += 1
            tempo_ultima_placa = time.time()
            if debug:
                status_txt = "NENHUM"
                if detectado_esq: status_txt = "ESQUERDA"
                if detectado_dir: status_txt = "DIREITA"
                print(f"Placa #{contador_placas} detectada na: {status_txt}")

        placa_visivel_anterior = placa_detectada

        if time.time() - tempo_ultima_placa > RESET_TIMEOUT:
            if contador_placas != 0:
                if debug:
                    print("Resetando contador")
            contador_placas = 0
            ultima_posicao_x = None

        # =========================
        # VIRAR APENAS NA 3ª
        # =========================
        if contador_placas >= 3 and placa_detectada:
            
            turn_needed = False
            
            if detectado_dir:
                if debug:
                    print(f"DIREITA (Zona) -> ↩ VIRANDO ESQUERDA")
                pydirectinput.keyDown("down")
                pydirectinput.keyDown("left")
                time.sleep(TEMPO_CURVA)
                pydirectinput.keyUp("left")
                pydirectinput.keyUp("down")
                turn_needed = True
            elif detectado_esq:
                if debug:
                    print(f"ESQUERDA (Zona) -> ↪ VIRANDO DIREITA")
                pydirectinput.keyDown("down")
                pydirectinput.keyDown("right")
                time.sleep(TEMPO_CURVA)
                pydirectinput.keyUp("right")
                pydirectinput.keyUp("down")
                turn_needed = True
                
            if turn_needed:
                contador_placas = 0
