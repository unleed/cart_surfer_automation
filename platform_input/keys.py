from enum import Enum, auto

class GameKey(Enum):
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    
    SPACE = auto()
    ENTER = auto()
    ESC = auto()
    TAB = auto()
    
    SHIFT = auto()
    CTRL = auto()
    ALT = auto()
    
    F1 = auto()
    F2 = auto()
    F3 = auto()
    F4 = auto()
    F5 = auto()
    F6 = auto()
    F7 = auto()
    F8 = auto()
    F9 = auto()
    F10 = auto()
    F11 = auto()
    F12 = auto()

class MouseButton(Enum):
    LEFT = auto()
    RIGHT = auto()
    MIDDLE = auto()
