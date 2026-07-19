from platform_input.base import InputController

class BotContext:
    def __init__(self, input_controller: InputController, game_name: str, debug: bool = False):
        self.input = input_controller
        self.game_name = game_name
        self.debug = debug
