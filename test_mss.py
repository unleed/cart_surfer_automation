import mss
try:
    with mss.mss() as sct:
        print("Monitors:", sct.monitors)
        try:
            img = sct.grab(sct.monitors[0])
            print("Successfully grabbed monitor 0")
        except Exception as e:
            print("Failed to grab monitor 0:", repr(e))
        
        try:
            img = sct.grab(sct.monitors[1])
            print("Successfully grabbed monitor 1")
        except Exception as e:
            print("Failed to grab monitor 1:", repr(e))
except Exception as e:
    print("Failed to initialize mss:", repr(e))
