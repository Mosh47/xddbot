from pynput import keyboard, mouse
from pynput.keyboard import Key, Controller
import time
import threading
import win32api, win32con
keyboard_controller = Controller()
VK_CONTROL = 0x11
mouse_listener = None
is_running = False
def send_right():
    win32api.keybd_event(win32con.VK_RIGHT, 0, 0, 0)  
    time.sleep(0.005)  
    win32api.keybd_event(win32con.VK_RIGHT, 0, win32con.KEYEVENTF_KEYUP, 0)  
def send_left():
    win32api.keybd_event(win32con.VK_LEFT, 0, 0, 0)  
    time.sleep(0.005)  
    win32api.keybd_event(win32con.VK_LEFT, 0, win32con.KEYEVENTF_KEYUP, 0)  
def on_scroll(x, y, dx, dy):
    if win32api.GetAsyncKeyState(VK_CONTROL) & 0x8000:
        if dy < 0:  
            send_right()
        elif dy > 0:  
            send_left()
def start_listener():
    global mouse_listener, is_running
    if is_running:
        return False
    mouse_listener = mouse.Listener(on_scroll=on_scroll)
    mouse_listener.start()
    is_running = True
    return True
def stop_listener():
    global mouse_listener, is_running
    if is_running and mouse_listener:
        mouse_listener.stop()
        is_running = False
        return True
    return False
def is_active():
    return is_running
if __name__ == "__main__":
    start_listener()
    print("Script running. Hold Ctrl and scroll to move left/right.")
    print("Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_listener()
        print("Script terminated.")