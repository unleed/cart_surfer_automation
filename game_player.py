import numpy as np
import time
import threading
import pydirectinput
import cv2
import keyboard
from fast_ctypes_screenshots import ScreenshotOfOneMonitor
from locate_pixelcolor_cpppragma import search_colors
from game_starter import find_and_click_with_retry

def fazer_loop(debug=False, done_event=None):
    """Executa a manobra loop: baixo + espaço (roda em thread separada)."""
    if debug: print("[MANOBRA] Executando: LOOP (baixo + espaço)")
    keyboard.send("down")
    keyboard.send("space")
    time.sleep(0.8) # Simula tempo da manobra
    if done_event:
        done_event.set()

def fazer_360(debug=False, done_event=None):
    """Executa a manobra 360: espaço + direita (roda em thread separada)."""
    if debug: print("[MANOBRA] Executando: 360 (espaço + direita)")
    keyboard.send("space")
    keyboard.send("right")
    time.sleep(0.8) # Simula tempo da manobra
    if done_event:
        done_event.set()

def _disparar_manobra(fn, debug):
    """Dispara uma função de manobra em thread daemon e retorna o Event de conclusão."""
    done_event = threading.Event()
    threading.Thread(target=fn, kwargs={"debug": debug, "done_event": done_event}, daemon=True).start()
    return done_event

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
    
    # Imports locais para evitar erro se não estiverem no topo
    import os

    # Definindo cor baseada no jogo com ternário
    allcolors = [[35, 35, 35]] if game_name == 'newcp' else [[0, 0, 0]]
    bgrcolors = np.array(allcolors, dtype=np.uint8)

    contador_placas = 0
    placa_visivel_anterior = False
    tempo_ultima_placa = time.time()
    ultima_posicao_x = None
    ultima_manobra = None  # None, 'loop' ou '360' — controla alternância de manobras
    _manobra_done = None   # Event que sinaliza quando a manobra em curso terminou
    tempo_ultima_manobra = 0.0  # Timestamp da última manobra disparada

    def cooldown_manobra():
        return 1.1 if ultima_manobra == 'loop' else 1.0

    TEMPO_CURVA = 1.65
    RESET_TIMEOUT = 4.0
    
    # Configuração do 'close.png'
    path_close = os.path.join(os.path.dirname(__file__), "images", game_name, "close.png")
    img_close = cv2.imread(path_close)
    if img_close is None:
        if debug: print(f"[AVISO] Imagem close.png não encontrada em: {path_close}")
        
    last_check_close = time.time()
    CHECK_CLOSE_INTERVAL = 1.0  # Checa a cada 1 segundo para não pesar o loop
    
    # Só começa a procurar o botão close depois de X segundos
    TIME_BEFORE_CHECK_CLOSE = 45
    game_start_time = time.time()
    close_detection_active = False  # Flag para indicar quando a detecção de close está ativa

    if debug: print("Iniciando loop de jogo...")

    while True:        
        with ScreenshotOfOneMonitor(monitor=0, ascontiguousarray=False) as sct:
            frame = sct.screenshot_one_monitor()
        
        # =========================
        # DETECÇÃO DO FIM DO JOGO (CLOSE)
        # =========================
        # Verifica periodicamente se o botão 'close' apareceu, mas SÓ APÓS {TIME_BEFORE_CHECK_CLOSE} SEGUNDOS
        current_time = time.time()
        if (img_close is not None and 
            (current_time - game_start_time > TIME_BEFORE_CHECK_CLOSE) and 
            (current_time - last_check_close > CHECK_CLOSE_INTERVAL)):
            
            # Ativa a flag para parar a detecção de placas
            if not close_detection_active:
                close_detection_active = True
                if debug: print("[INFO] Detecção de close.png ativada. Parando detecção de placas.")
            
            last_check_close = current_time
            
            # Match Template
            pass_search = frame
            # Remove canal alpha se existir no frame para busca
            if frame.shape[2] == 4:
                pass_search = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
            res = cv2.matchTemplate(pass_search, img_close, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            if max_val >= 0.8: # Confiança
                if debug: print(f"Fim de jogo detectado! (Confiança: {max_val:.2f})")
                
                # Clica no centro do botão close
                h_close, w_close = img_close.shape[:2]
                cx = max_loc[0] + w_close // 2
                cy = max_loc[1] + h_close // 2
                
                pydirectinput.click(cx, cy)

                if game_name == 'newcp':
                    # Configuração do 'shack.png'
                    base_path = os.path.join(os.path.dirname(__file__), "images", game_name)
                    img_shack = os.path.join(base_path, "shack.png")
                    
                    find_and_click_with_retry("Shack", img_shack, roi=roi, debug=debug)

                    # Sleep solicitado de 5.0 antes de retornar (reiniciar)
                    time.sleep(5.0)
                    return
                
                # Sleep solicitado de 0.5 antes de retornar (reiniciar)
                time.sleep(0.5)
                return # Sai da função, fazendo o bot reiniciar o ciclo
                
        # Se a callback disser que não está ativo, apenas dorme e continua
        if active_check_callback and not active_check_callback():
            time.sleep(0.05)
            # cv2.destroyAllWindows()
            continue
            
        # =========================
        # DETECÇÃO DE PLACAS (só executa se close detection não estiver ativa)
        # =========================
        detectado_esq = False
        detectado_dir = False
        placa_detectada = False

        # if not close_detection_active:
        # Recorta apenas a área do ROI
        x, y, w, h = roi["x"], roi["y"], roi["w"], roi["h"]
        frame_roi = frame[y:y+h, x:x+w]

        # Reduz resolução e analisa metade superior
        small = frame_roi[::2, ::2]
        small = small[0:int(small.shape[0]*0.6), :]

        # =========================
        # DETECÇÃO DE PLACAS POR ZONAS
        # =========================
        h_small, w_small = small.shape[:2]
        
        # Define tamanho das zonas (ajuste conforme necessário)
        zone_w = int(w_small * 0.05) # 5% da largura
        zone_h = int(h_small * 0.10) # 10% da altura
        
        # Zona Esquerda (Centro 25% largura, 80% altura)
        cx_esq = int(w_small * 0.25)
        cy_esq = int(h_small * 0.80)
        x1_esq = cx_esq - zone_w // 2
        y1_esq = cy_esq - zone_h // 2
        x2_esq = cx_esq + zone_w // 2
        y2_esq = cy_esq + zone_h // 2
        
        # Zona Direita (Centro 75% largura, 80% altura)
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
        # MANOBRAS (quando contador_placas == 0 e nenhuma placa visível)
        # =========================
        # Só dispara nova manobra se: a anterior já terminou E o cooldown passou
        # E principalmente: se NÃO tem placa detectada neste exato frame
        manobra_livre = (_manobra_done is None or _manobra_done.is_set())
        cooldown_ok = (time.time() - tempo_ultima_manobra) >= cooldown_manobra()
        
        if contador_placas == 0 and not placa_detectada and manobra_livre and cooldown_ok:
            # Alterna entre loop e 360: faz a que NÃO foi feita por último
            if ultima_manobra != '360':
                ultima_manobra = '360'
                _manobra_done = _disparar_manobra(fazer_360, debug)
            else:
                ultima_manobra = 'loop'
                _manobra_done = _disparar_manobra(fazer_loop, debug)
            tempo_ultima_manobra = time.time()

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
        if contador_placas >= 3:
            
            turn_needed = False
            
            if detectado_dir:
                if debug:
                    print(f"DIREITA (Zona) -> ↩ VIRANDO ESQUERDA")
                keyboard.press("down")
                keyboard.press("left")
                time.sleep(TEMPO_CURVA)
                keyboard.release("left")
                keyboard.release("down")
                turn_needed = True
            elif detectado_esq:
                if debug:
                    print(f"ESQUERDA (Zona) -> ↪ VIRANDO DIREITA")
                keyboard.press("down")
                keyboard.press("right")
                time.sleep(TEMPO_CURVA)
                keyboard.release("right")
                keyboard.release("down")
                turn_needed = True
                
            if turn_needed:
                contador_placas = 0
