import time
import keyboard
import ctypes
from input_utils import execute_command_batched, execute_whisper_batched

class HotkeyManager:
    def __init__(self, settings, execute_callback=None):
        self.settings = settings
        self.whisper_settings = {}
        self.registered_hotkeys = set()
        self.execute_callback = execute_callback or self.execute_command
        self.last_executed = {}
        self.last_execution_time = 0
        self.execution_cooldown = 0.1  # 100ms cooldown between executions
        
    def set_whisper_settings(self, whisper_settings):
        self.whisper_settings = whisper_settings
        
    def is_poe_window_active(self):
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            window_title = buff.value
            return "Path of Exile" in window_title
        except Exception as e:
            print(f"Error checking window: {e}")
            return False
            
    def clear_all_hotkeys(self):
        try:
            for hotkey_id in list(self.registered_hotkeys):
                try:
                    keyboard.remove_hotkey(hotkey_id)
                except Exception as e:
                    pass
            self.registered_hotkeys.clear()
        except Exception as e:
            pass
            
    def register_all_hotkeys(self):
        try:
            self.clear_all_hotkeys()
            time.sleep(0.1)
            
            self.register_hotkeys()
            self.register_whisper_hotkeys()
        except Exception as e:
            pass
            
    def register_hotkeys(self):
        try:
            for cmd_id, cmd_data in self.settings.items():
                if cmd_id == 'logout':
                    continue
                    
                hotkey = cmd_data.get('hotkey')
                if not hotkey or not isinstance(hotkey, str) or hotkey.startswith('mouse'):
                    continue
                    
                cmd_text = cmd_data.get('text')
                if not cmd_text:
                    continue
                    
                def execute_command_if_poe(cmd_text=cmd_text, hotkey=hotkey):
                    if self.is_poe_window_active():
                        self.execute_command(cmd_text)
                
                try:
                    hotkey_id = keyboard.add_hotkey(hotkey, execute_command_if_poe, suppress=False)
                    self.registered_hotkeys.add(hotkey_id)
                except Exception as e:
                    print(f"Failed to register hotkey {hotkey}")
        except Exception as e:
            print(f"Error in register_hotkeys")
            
    def register_whisper_hotkeys(self):
        try:
            if not self.whisper_settings:
                return
                
            for cmd_id, cmd_data in self.whisper_settings.items():
                hotkey = cmd_data.get('hotkey')
                if not hotkey or not isinstance(hotkey, str) or hotkey.startswith('mouse'):
                    continue
                    
                cmd_text = cmd_data.get('text')
                if not cmd_text:
                    continue
                    
                def execute_whisper_if_poe(cmd_text=cmd_text, hotkey=hotkey):
                    if self.is_poe_window_active():
                        self.execute_whisper(cmd_text)
                
                try:
                    hotkey_id = keyboard.add_hotkey(hotkey, execute_whisper_if_poe, suppress=False)
                    self.registered_hotkeys.add(hotkey_id)
                except Exception as e:
                    print(f"Failed to register whisper hotkey {hotkey}")
        except Exception as e:
            print(f"Error in register_whisper_hotkeys: {e}")
            
    def execute_command(self, command_text):
        try:
            current_time = time.time()
            if current_time - self.last_execution_time < self.execution_cooldown:
                return
            self.last_execution_time = current_time
            execute_command_batched(command_text)
        except Exception as e:
            print(f"Error executing command: {e}")
            
    def execute_whisper(self, whisper_text):
        try:
            current_time = time.time()
            if current_time - self.last_execution_time < self.execution_cooldown:
                return
            self.last_execution_time = current_time
            execute_whisper_batched(whisper_text)
        except Exception as e:
            print(f"Error executing whisper: {e}")
            
    def set_show_settings_callback(self, callback):
        self.show_settings_callback = callback
        # Only register F10 hotkey without suppressing it
        keyboard.add_hotkey('f10', callback, suppress=False)
        
    def update_settings(self, new_settings, new_whisper_settings=None):
        try:
            self.settings = new_settings
            if new_whisper_settings:
                self.whisper_settings = new_whisper_settings
            self.register_all_hotkeys()
        except Exception as e:
            pass
