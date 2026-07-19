from abc import ABC, abstractmethod
import time
from .keys import GameKey, MouseButton

class InputController(ABC):
    @abstractmethod
    def press(self, key: GameKey) -> None:
        pass
        
    @abstractmethod
    def release(self, key: GameKey) -> None:
        pass
        
    @abstractmethod
    def click(self, x: int, y: int, button: MouseButton = MouseButton.LEFT) -> None:
        pass
        
    @abstractmethod
    def mouse_down(self, button: MouseButton = MouseButton.LEFT) -> None:
        pass
        
    @abstractmethod
    def mouse_up(self, button: MouseButton = MouseButton.LEFT) -> None:
        pass
        
    @abstractmethod
    def move_to(self, x: int, y: int) -> None:
        pass

    def tap(self, key: GameKey, duration: float = 0.05) -> None:
        self.press(key)
        if duration > 0:
            time.sleep(duration)
        self.release(key)
