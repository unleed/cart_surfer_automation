import platform
import os
from .base import InputController

def get_input_controller() -> InputController:
    os_name = platform.system()
    
    if os_name == "Windows":
        from .windows import WindowsInputController
        return WindowsInputController()
    elif os_name == "Linux":
        is_wayland = os.environ.get("XDG_SESSION_TYPE") == "wayland" or os.environ.get("WAYLAND_DISPLAY")
        if is_wayland:
            raise RuntimeError(
                "O bot não possui suporte ao Wayland porque a biblioteca de captura de tela (mss) "
                "requer o X11 (XGetImage) para funcionar com alta performance.\n"
                "Por favor, faça logout e inicie uma sessão X11/Xorg para rodar o bot."
            )
        else:
            from .linux_x11 import LinuxX11InputController
            return LinuxX11InputController()
    else:
        # Default fallback
        from .windows import WindowsInputController
        return WindowsInputController()
