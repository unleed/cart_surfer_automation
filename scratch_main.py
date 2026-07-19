with open("main.py", "r") as f:
    content = f.read()

# 1. Imports
content = content.replace('from game_starter import start_game_sequence, find_and_click_with_retry', 
'''from game_starter import start_game_sequence, find_and_click_with_retry
from platform_input import get_input_controller
from bot_context import BotContext''')

# 2. Setup context before instances
content = content.replace(
'''# Instances
conn_monitor = ConnectionMonitor(roi, GAME, debug=DEBUG)
rec_manager = RecoveryManager(roi, GAME, debug=DEBUG)''',
'''# Context & Instances
input_controller = get_input_controller()
context = BotContext(input_controller, GAME, debug=DEBUG)
conn_monitor = ConnectionMonitor(roi, GAME, debug=DEBUG)
rec_manager = RecoveryManager(context, roi)'''
)

# 3. Modify pyautogui commented lines
content = content.replace('# import pyautogui', '# context.input.click(roi["x"] + roi["w"] // 2, roi["y"] + roi["h"] - 10)')
content = content.replace('# pyautogui.click(roi["x"] + roi["w"] // 2, roi["y"] + roi["h"] - 10)', '')

# 4. Modify start_game_sequence call
content = content.replace(
    'success = start_game_sequence(roi, GAME, debug=DEBUG, frame_inspector=conn_monitor.inspect, abort_check=should_abort_start)',
    'success = start_game_sequence(roi, context, frame_inspector=conn_monitor.inspect, abort_check=should_abort_start)'
)

# 5. Modify run_game_loop call
content = content.replace(
    'run_game_loop(roi, game_name=GAME, debug=DEBUG, visualize=VISUALIZE, active_check_callback=is_active_and_connected, frame_inspector=conn_monitor.inspect)',
    'run_game_loop(context, roi, visualize=VISUALIZE, active_check_callback=is_active_and_connected, frame_inspector=conn_monitor.inspect)'
)

with open("main.py", "w") as f:
    f.write(content)
