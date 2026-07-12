import os
import time
from connection_monitor import RecoveryState

class RecoveryManager:
    def __init__(self, roi, game_name, debug=False):
        self.roi = roi
        self.game_name = game_name
        self.debug = debug
        self.timeout = 90.0
        
        self.base_path = os.path.join(os.path.dirname(__file__), "images", game_name)
        
    def _path(self, filename):
        return os.path.join(self.base_path, filename)
        
    def run_recovery(self, find_and_click_with_retry_fn):
        """
        Executa todo o fluxo de recuperação visual.
        Retorna True se concluído com sucesso, False se der timeout.
        Passamos o find_and_click_with_retry_fn para evitar imports circulares pesados.
        """
        start_time = time.monotonic()
        
        def check_timeout():
            if time.monotonic() - start_time > self.timeout:
                print("[RecoveryManager] TIMEOUT GLOBAL ATINGIDO (90s)!")
                return True # Abort!
            return False

        print("\n[RecoveryManager] Iniciando fluxo de recuperacao de conexao...")

        # 1. Clicar em connection_lost.png
        # Tenta achar o botao por algumas tentativas. Se nao achar, assume que estamos 
        # travados em outra tela e forca o refresh (F5).
        if not find_and_click_with_retry_fn("Connection Lost OK", self._path("connection_lost.png"), roi=self.roi, attempts=3, debug=self.debug, abort_check=check_timeout):
            print("[RecoveryManager] connection_lost.png nao encontrado. Forcando refresh (F5)...")
            import pyautogui
            pyautogui.press('f5')
            time.sleep(3) # Tempo inicial para a pagina comecar a recarregar

        # 2. account.png
        print("[RecoveryManager] Aguardando tela de selecao de conta...")
        if not find_and_click_with_retry_fn("Account", self._path("account.png"), roi=self.roi, attempts=40, timeout=2, debug=self.debug, abort_check=check_timeout):
            return False
            
        # 3. login.png
        print("[RecoveryManager] Aguardando botao de login...")
        if not find_and_click_with_retry_fn("Login", self._path("login.png"), roi=self.roi, attempts=40, timeout=2, debug=self.debug, abort_check=check_timeout):
            return False

        # 4. server.png
        print("[RecoveryManager] Aguardando tela de servidores...")
        if not find_and_click_with_retry_fn("Server", self._path("server.png"), roi=self.roi, attempts=40, timeout=2, debug=self.debug, abort_check=check_timeout):
            return False

        # 5. Esperar personagem no jogo
        print("[RecoveryManager] Aguardando carregamento da sala (procurando mapa)...")
        if not find_and_click_with_retry_fn("Map", self._path("map.png"), roi=self.roi, attempts=60, timeout=2, debug=self.debug, abort_check=check_timeout):
            return False

        # 6. Tentar clicar no atalho do Cart Surfer diretamente (caso a aba de jogos já esteja aberta)
        print("[RecoveryManager] Procurando atalho do Cart Surfer diretamente...")
        cart_surfer_found = find_and_click_with_retry_fn("Map Cart Surfer", self._path("map_cart_surfer.png"), roi=self.roi, attempts=4, timeout=2, debug=self.debug, abort_check=check_timeout)
        
        if not cart_surfer_found:
            # 7. Se não achou, significa que a aba está fechada. Clicar em map_games.png
            print("[RecoveryManager] Atalho nao encontrado. Clicando na aba de jogos...")
            if not find_and_click_with_retry_fn("Map Games", self._path("map_games.png"), roi=self.roi, attempts=15, timeout=2, debug=self.debug, abort_check=check_timeout):
                return False
                
            # 8. E tentar clicar no atalho do Cart Surfer novamente
            print("[RecoveryManager] Aguardando atalho do Cart Surfer...")
            if not find_and_click_with_retry_fn("Map Cart Surfer", self._path("map_cart_surfer.png"), roi=self.roi, attempts=15, timeout=2, debug=self.debug, abort_check=check_timeout):
                return False
            
        print("[RecoveryManager] Recuperacao concluida com sucesso! Voltando ao loop principal.")
        return True
