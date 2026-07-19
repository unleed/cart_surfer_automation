import re

with open("game_player.py", "r") as f:
    content = f.read()

# 1. Imports
content = re.sub(r'import pyautogui\n', '', content)
content = re.sub(r'from pynput\.keyboard import Controller, Key\n', 'from platform_input import GameKey\n', content)
content = re.sub(r'_kb = Controller\(\)\n', '', content)

# 2. TrickController Init
content = content.replace('def __init__(self, debug=False):', 'def __init__(self, context):')
content = content.replace('self.debug = debug', 'self.debug = context.debug\n        self.input = context.input')

# 3. TrickController _kb usage
content = content.replace('_kb.press(key)', 'self.input.press(key)')
content = content.replace('_kb.release(key)', 'self.input.release(key)')

# 4. TrickController Keys
content = content.replace('Key.down', 'GameKey.DOWN')
content = content.replace('Key.space', 'GameKey.SPACE')
content = content.replace('Key.right', 'GameKey.RIGHT')
content = content.replace('Key.left', 'GameKey.LEFT')

# 5. run_game_loop signature
content = content.replace(
    'def run_game_loop(roi, game_name="newcp", debug=False, visualize=False, active_check_callback=None, frame_inspector=None):',
    'def run_game_loop(context, roi, visualize=False, active_check_callback=None, frame_inspector=None):'
)

# 6. run_game_loop internal references
content = content.replace('trick_controller = TrickController(debug=debug)', 'trick_controller = TrickController(context)')
content = content.replace('if debug:', 'if context.debug:')
content = content.replace('if debug :', 'if context.debug:')
content = content.replace('game_name ==', 'context.game_name ==')
content = content.replace('game_name,', 'context.game_name,')

content = content.replace('pyautogui.click(', 'context.input.click(')

content = content.replace('find_and_click_with_retry("Shack", img_shack, roi=roi, debug=debug)', 'find_and_click_with_retry("Shack", img_shack, context, roi=roi)')

with open("game_player.py", "w") as f:
    f.write(content)
