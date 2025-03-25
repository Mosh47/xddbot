import ctypes
import time
from ctypes import wintypes

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_RETURN = 0x0D

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD),
                ("wParamL", wintypes.WORD),
                ("wParamH", wintypes.WORD)]

class INPUT_union(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT),
                ("ki", KEYBDINPUT),
                ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD),
                ("union", INPUT_union)]

KEY_CODE_CACHE = {}
for char in range(256):
    try:
        vk = ctypes.windll.user32.VkKeyScanW(chr(char))
        KEY_CODE_CACHE[char] = vk & 0xFF
    except:
        KEY_CODE_CACHE[char] = 0

EXTRA = ctypes.c_ulong(0)
EXTRA_PTR = ctypes.pointer(EXTRA)

INPUT_POOL_SIZE = 128
INPUT_POOL = []
for _ in range(INPUT_POOL_SIZE):
    union = INPUT_union()
    union.ki = KEYBDINPUT(0, 0, 0, 0, EXTRA_PTR)
    INPUT_POOL.append(INPUT(INPUT_KEYBOARD, union))

VK_CODE = {
    'backspace': 0x08, 'tab': 0x09, 'clear': 0x0C, 'enter': 0x0D, 'shift': 0x10,
    'ctrl': 0x11, 'alt': 0x12, 'pause': 0x13, 'caps_lock': 0x14, 'esc': 0x1B,
    'spacebar': 0x20, 'page_up': 0x21, 'page_down': 0x22, 'end': 0x23, 'home': 0x24,
    'left_arrow': 0x25, 'up_arrow': 0x26, 'right_arrow': 0x27, 'down_arrow': 0x28,
    'select': 0x29, 'print': 0x2A, 'execute': 0x2B, 'print_screen': 0x2C,
    'ins': 0x2D, 'del': 0x2E, 'help': 0x2F,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34, '5': 0x35, '6': 0x36,
    '7': 0x37, '8': 0x38, '9': 0x39,
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46, 'g': 0x47,
    'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E,
    'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54, 'u': 0x55,
    'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
    'numpad_0': 0x60, 'numpad_1': 0x61, 'numpad_2': 0x62, 'numpad_3': 0x63,
    'numpad_4': 0x64, 'numpad_5': 0x65, 'numpad_6': 0x66, 'numpad_7': 0x67,
    'numpad_8': 0x68, 'numpad_9': 0x69,
    'multiply_key': 0x6A, 'add_key': 0x6B, 'separator_key': 0x6C,
    'subtract_key': 0x6D, 'decimal_key': 0x6E, 'divide_key': 0x6F,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74, 'f6': 0x75,
    'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
    'num_lock': 0x90, 'scroll_lock': 0x91, 'left_shift': 0xA0, 'right_shift': 0xA1,
    'left_control': 0xA2, 'right_control': 0xA3, 'left_menu': 0xA4, 'right_menu': 0xA5,
    '/': 0xBF, '\\': 0xDC
}

def send_key(key_code, up=False):
    """Send a keyboard input event to Windows"""
    ii_ = INPUT_union()
    ii_.ki = KEYBDINPUT(key_code, 0, KEYEVENTF_KEYUP if up else 0, 0, EXTRA_PTR)
    x = INPUT(INPUT_KEYBOARD, ii_)
    ctypes.windll.user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))

def press_and_release(key_code):
    """Press and release a key"""
    send_key(key_code)
    send_key(key_code, up=True)

def type_string(string):
    """Type a string by simulating key presses"""
    for char in string:
        if char == '/':
            key_code = VK_CODE.get('/')
            press_and_release(key_code)
        else:
            char_upper = char.upper()
            key_code = ord(char_upper)
            press_and_release(key_code)

def get_input_from_pool(index, key_code, up=False):
    """Get a pre-allocated input structure from the pool and configure it for a key press/release"""
    if index >= len(INPUT_POOL):
        for _ in range(32):
            union = INPUT_union()
            union.ki = KEYBDINPUT(0, 0, 0, 0, EXTRA_PTR)
            INPUT_POOL.append(INPUT(INPUT_KEYBOARD, union))
    
    input_struct = INPUT_POOL[index]
    input_struct.union.ki.wVk = key_code
    input_struct.union.ki.dwFlags = KEYEVENTF_KEYUP if up else 0
    
    return input_struct

def create_key_input(key_code, up=False):
    """Create a keyboard input event with optimized structure creation"""
    return INPUT(
        INPUT_KEYBOARD,
        INPUT_union(ki=KEYBDINPUT(key_code, 0, KEYEVENTF_KEYUP if up else 0, 0, EXTRA_PTR))
    )

def send_batched_input(inputs):
    """Send multiple input events in a single Windows API call"""
    if not inputs:
        return
    input_array = (INPUT * len(inputs))(*inputs)
    ctypes.windll.user32.SendInput(len(inputs), ctypes.byref(input_array), ctypes.sizeof(INPUT))

def execute_command_batched(command_text):
    """Execute a command using batched input events with optimized structure reuse"""
    input_count = 4 + (len(command_text) * 2)
    
    INPUT_ARRAY_TYPE = INPUT * input_count
    
    input_array = INPUT_ARRAY_TYPE()
    
    idx = 0
    
    input_array[idx] = get_input_from_pool(idx, VK_RETURN, False)
    idx += 1
    input_array[idx] = get_input_from_pool(idx, VK_RETURN, True)
    idx += 1
    
    for char in command_text:
        if char == '/':
            key_code = VK_CODE.get('/')
        else:
            key_code = KEY_CODE_CACHE.get(ord(char.upper()), 0x41)
        
        input_array[idx] = get_input_from_pool(idx, key_code, False)
        idx += 1
        
        input_array[idx] = get_input_from_pool(idx, key_code, True)
        idx += 1
    
    input_array[idx] = get_input_from_pool(idx, VK_RETURN, False)
    idx += 1
    input_array[idx] = get_input_from_pool(idx, VK_RETURN, True)
    
    ctypes.windll.user32.SendInput(input_count, ctypes.byref(input_array), ctypes.sizeof(INPUT))

def execute_whisper_batched(whisper_text):
    """Execute a whisper using batched input events with optimized structure reuse"""
    input_count = 4 + (len(whisper_text) * 2) + 2
    
    INPUT_ARRAY_TYPE = INPUT * input_count
    
    input_array = INPUT_ARRAY_TYPE()
    
    idx = 0
    
    input_array[idx] = get_input_from_pool(idx, 0x11, False)
    idx += 1
    
    input_array[idx] = get_input_from_pool(idx, VK_RETURN, False)
    idx += 1
    
    input_array[idx] = get_input_from_pool(idx, VK_RETURN, True)
    idx += 1
    
    input_array[idx] = get_input_from_pool(idx, 0x11, True)
    idx += 1
    
    for char in whisper_text:
        if char == '/':
            key_code = VK_CODE.get('/')
        else:
            key_code = KEY_CODE_CACHE.get(ord(char.upper()), 0x41)
        
        input_array[idx] = get_input_from_pool(idx, key_code, False)
        idx += 1
        
        input_array[idx] = get_input_from_pool(idx, key_code, True)
        idx += 1
    
    input_array[idx] = get_input_from_pool(idx, VK_RETURN, False)
    idx += 1
    input_array[idx] = get_input_from_pool(idx, VK_RETURN, True)
    
    ctypes.windll.user32.SendInput(input_count, ctypes.byref(input_array), ctypes.sizeof(INPUT))

def check_single_instance():
    """Check if another instance of the application is already running"""
    mutex_name = "Global\\XDDBotSingleInstance"
    try:
        mutex = ctypes.windll.kernel32.CreateMutexW(None, 1, mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183:
            return False
        return True
    except:
        return True 