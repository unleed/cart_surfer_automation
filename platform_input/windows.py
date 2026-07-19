import pyautogui
from pynput.keyboard import Controller, Key
from .base import InputController
from .keys import GameKey, MouseButton

class WindowsInputController(InputController):
    def __init__(self):
        self._kb = Controller()
        self._key_map = {
            GameKey.LEFT: Key.left,
            GameKey.RIGHT: Key.right,
            GameKey.UP: Key.up,
            GameKey.DOWN: Key.down,
            
            GameKey.SPACE: Key.space,
            GameKey.ENTER: Key.enter,
            GameKey.ESC: Key.esc,
            GameKey.TAB: Key.tab,
            
            GameKey.SHIFT: Key.shift,
            GameKey.CTRL: Key.ctrl,
            GameKey.ALT: Key.alt,
            
            GameKey.F1: Key.f1,
            GameKey.F2: Key.f2,
            GameKey.F3: Key.f3,
            GameKey.F4: Key.f4,
            GameKey.F5: Key.f5,
            GameKey.F6: Key.f6,
            GameKey.F7: Key.f7,
            GameKey.F8: Key.f8,
            GameKey.F9: Key.f9,
            GameKey.F10: Key.f10,
            GameKey.F11: Key.f11,
            GameKey.F12: Key.f12,
        }
        
    def _map_key(self, key: GameKey):
        mapped = self._key_map.get(key)
        if not mapped:
            raise ValueError(f"Key {key} not mapped in WindowsInputController")
        return mapped
        
    def _map_mouse_button(self, button: MouseButton) -> str:
        if button == MouseButton.LEFT:
            return 'left'
        elif button == MouseButton.RIGHT:
            return 'right'
        elif button == MouseButton.MIDDLE:
            return 'middle'
        return 'left'

    def press(self, key: GameKey) -> None:
        self._kb.press(self._map_key(key))
        
    def release(self, key: GameKey) -> None:
        self._kb.release(self._map_key(key))
        
    def click(self, x: int, y: int, button: MouseButton = MouseButton.LEFT) -> None:
        pyautogui.click(x, y, button=self._map_mouse_button(button))
        
    def mouse_down(self, button: MouseButton = MouseButton.LEFT) -> None:
        pyautogui.mouseDown(button=self._map_mouse_button(button))
        
    def mouse_up(self, button: MouseButton = MouseButton.LEFT) -> None:
        pyautogui.mouseUp(button=self._map_mouse_button(button))
        
    def move_to(self, x: int, y: int) -> None:
        pyautogui.moveTo(x, y)
