import cv2
import os
import time
from enum import Enum

class RecoveryState(Enum):
    NORMAL = 1
    CONNECTION_LOST = 2
    RECOVERING = 3
    RECOVERY_FAILED = 4

class ConnectionMonitor:
    def __init__(self, roi, game_name, debug=False):
        self.roi = roi
        self.game_name = game_name
        self.debug = debug
        self.state = RecoveryState.NORMAL
        
        base_path = os.path.join(os.path.dirname(__file__), "images", game_name)
        self.connection_lost_path = os.path.join(base_path, "connection_lost.png")
        
        if os.path.exists(self.connection_lost_path):
            self.template = cv2.imread(self.connection_lost_path, cv2.IMREAD_COLOR)
        else:
            self.template = None
            if self.debug: print(f"[ConnectionMonitor] AVISO: {self.connection_lost_path} nao encontrado!")

        self.last_check_time = 0
        self.check_interval = 0.25 # Polling de 4Hz para deteccao levissima

    def inspect(self, frame):
        """
        Callback de inspecao: recebe um frame BGR e checa se ha conexao perdida.
        """
        if self.state != RecoveryState.NORMAL or self.template is None:
            return

        current_time = time.monotonic()
        if current_time - self.last_check_time < self.check_interval:
            return
            
        self.last_check_time = current_time

        try:
            res = cv2.matchTemplate(frame, self.template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            
            if max_val >= 0.8:
                if self.debug: print("\n[ConnectionMonitor] CONEXAO PERDIDA DETECTADA!")
                self.state = RecoveryState.CONNECTION_LOST
                
        except Exception as e:
            if self.debug: print(f"[ConnectionMonitor] Erro na inspecao: {e}")
