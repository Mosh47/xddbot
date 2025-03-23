import sys
import os
import json
import keyboard
import time
import ctypes
import subprocess
import threading
from ctypes import wintypes
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QSystemTrayIcon, 
                             QMenu, QAction, QComboBox, QStatusBar, QMessageBox)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer

try:
    import logout
    import stashscroll
    import npcap_detector
    import update_checker
except ImportError as e:
    print(f"Failed to import module: {e}")

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_RETURN = 0x0D

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

class KeyCaptureWidget(QLineEdit):
    def __init__(self, initial_hotkey='', parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setText(initial_hotkey)
        self.setCursor(Qt.PointingHandCursor)
        self.setPlaceholderText("Click to capture hotkey...")
        self.setToolTip("Click once to start capturing, then press any key or mouse button")
        self.setFocusPolicy(Qt.ClickFocus)
        self.capturing = False
        self.hotkey = initial_hotkey
        self.first_click = True
        
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.capturing = True
        self.first_click = True
        self.setText("Press any key or mouse button...")
        self.selectAll()
        
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.capturing = False
        self.first_click = True
        if not self.hotkey:
            self.setText("No key set")
        else:
            self.setText(self.hotkey)
    
    def mousePressEvent(self, event):
        if self.first_click:
            self.first_click = False
            super().mousePressEvent(event)
            return
            
        if not self.capturing:
            super().mousePressEvent(event)
            return
            
        button_map = {
            Qt.LeftButton: "mouse1",
            Qt.RightButton: "mouse2",
            Qt.MiddleButton: "mouse3",
            Qt.BackButton: "mouse4",
            Qt.ForwardButton: "mouse5"
        }
        
        modifiers = []
        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            modifiers.append("ctrl")
        if QApplication.keyboardModifiers() & Qt.AltModifier:
            modifiers.append("alt")
        if QApplication.keyboardModifiers() & Qt.ShiftModifier:
            modifiers.append("shift")
            
        button_text = button_map.get(event.button(), "")
        
        if button_text:
            if modifiers:
                self.hotkey = "+".join(modifiers + [button_text])
            else:
                self.hotkey = button_text
                
            self.setText(self.hotkey)
            self.clearFocus()
        else:
            super().mousePressEvent(event)
            
    def keyPressEvent(self, event):
        if not self.capturing:
            return super().keyPressEvent(event)
            
        modifiers = []
        if event.modifiers() & Qt.ControlModifier:
            modifiers.append("ctrl")
        if event.modifiers() & Qt.AltModifier:
            modifiers.append("alt")
        if event.modifiers() & Qt.ShiftModifier:
            modifiers.append("shift")
            
        key = event.key()
        key_text = ""
        
        if Qt.Key_F1 <= key <= Qt.Key_F12:
            key_text = f"f{key - Qt.Key_F1 + 1}"
        elif Qt.Key_A <= key <= Qt.Key_Z:
            key_text = chr(key).lower()
        elif Qt.Key_0 <= key <= Qt.Key_9:
            key_text = chr(key)
        else:
            key_map = {
                Qt.Key_Escape: "esc",
                Qt.Key_Tab: "tab",
                Qt.Key_Space: "space",
                Qt.Key_Return: "enter",
                Qt.Key_Backspace: "backspace",
                Qt.Key_Delete: "delete",
                Qt.Key_Home: "home",
                Qt.Key_End: "end",
                Qt.Key_PageUp: "pageup",
                Qt.Key_PageDown: "pagedown",
                Qt.Key_Insert: "insert",
                Qt.Key_Left: "left",
                Qt.Key_Right: "right",
                Qt.Key_Up: "up",
                Qt.Key_Down: "down"
            }
            key_text = key_map.get(key, "")
            
        if not key_text:
            return
            
        if modifiers:
            self.hotkey = "+".join(modifiers + [key_text])
        else:
            self.hotkey = key_text
            
        self.setText(self.hotkey)
        self.clearFocus()
        
    def get_hotkey(self):
        return self.hotkey
        
    def set_hotkey(self, hotkey):
        self.hotkey = hotkey
        self.setText(hotkey)

class CommandHotkeys(QWidget):
    def __init__(self):
        super().__init__()
        
        self.registered_hotkeys = set()
        
        self.settings = {
            'command1': {
                'text': 'hideout',
                'hotkey': 'f5'
            },
            'command2': {
                'text': 'exit',
                'hotkey': 'f6'
            },
            'logout': {
                'hotkey': 'f9'
            }
        }
        
        self.load_settings()
        self.logout_process = None
        self.init_ui()
        
        self.register_hotkeys()
        self.start_logout_script()
        self.create_tray_icon()
        
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.update_connection_display)
        self.connection_timer.start(2000)

    def init_ui(self):
        self.setWindowTitle('PoE Command Hotkeys')
        self.setGeometry(300, 300, 500, 220)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        self.setStyleSheet("""
            QWidget {
                background-color: #2D2D2D;
                color: #E0E0E0;
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                font-size: 10pt;
            }
            QLabel {
                color: #E0E0E0;
            }
            QLineEdit, QComboBox {
                background-color: #3D3D3D;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 4px;
                color: #E0E0E0;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                padding: 6px 12px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #0085EB;
            }
            QPushButton:pressed {
                background-color: #00669E;
            }
            QPushButton#clearButton {
                background-color: #aa3333;
                color: white;
                font-weight: bold;
                min-width: 20px;
                max-width: 20px;
                padding: 0px;
            }
            QPushButton#clearButton:hover {
                background-color: #dd3333;
            }
            KeyCaptureWidget {
                background-color: #3D3D3D;
                color: #E0E0E0;
                border: 1px solid #555555;
                padding: 4px;
                border-radius: 3px;
            }
        """)
        
        main_layout = QVBoxLayout()
        
        logout_layout = QHBoxLayout()
        logout_label = QLabel('Logout:')
        self.logout_text = QLineEdit("logout")
        self.logout_text.setEnabled(False)
        
        hotkey_layout = QHBoxLayout()
        hotkey_layout.setSpacing(2)
        self.logout_hotkey = KeyCaptureWidget(self.settings['logout']['hotkey'])
        self.logout_clear = QPushButton("✕")
        self.logout_clear.setObjectName("clearButton")
        self.logout_clear.setToolTip("Clear hotkey")
        self.logout_clear.clicked.connect(lambda: self.clear_hotkey('logout'))
        hotkey_layout.addWidget(self.logout_hotkey)
        hotkey_layout.addWidget(self.logout_clear)
        
        logout_save = QPushButton('Save')
        logout_save.clicked.connect(lambda: self.save_command('logout'))
        
        logout_layout.addWidget(logout_label)
        logout_layout.addWidget(self.logout_text)
        logout_layout.addLayout(hotkey_layout)
        logout_layout.addWidget(logout_save)
        
        cmd1_layout = QHBoxLayout()
        cmd1_label = QLabel('Command 1:')
        self.cmd1_text = QLineEdit(self.settings['command1']['text'])
        
        hotkey1_layout = QHBoxLayout()
        hotkey1_layout.setSpacing(2)
        self.cmd1_hotkey = KeyCaptureWidget(self.settings['command1']['hotkey'])
        self.cmd1_clear = QPushButton("✕")
        self.cmd1_clear.setObjectName("clearButton")
        self.cmd1_clear.setToolTip("Clear hotkey")
        self.cmd1_clear.clicked.connect(lambda: self.clear_hotkey(1))
        hotkey1_layout.addWidget(self.cmd1_hotkey)
        hotkey1_layout.addWidget(self.cmd1_clear)
        
        cmd1_save = QPushButton('Save')
        cmd1_save.clicked.connect(lambda: self.save_command(1))
        
        cmd1_layout.addWidget(cmd1_label)
        cmd1_layout.addWidget(self.cmd1_text)
        cmd1_layout.addLayout(hotkey1_layout)
        cmd1_layout.addWidget(cmd1_save)
        
        cmd2_layout = QHBoxLayout()
        cmd2_label = QLabel('Command 2:')
        self.cmd2_text = QLineEdit(self.settings['command2']['text'])
        
        hotkey2_layout = QHBoxLayout()
        hotkey2_layout.setSpacing(2)
        self.cmd2_hotkey = KeyCaptureWidget(self.settings['command2']['hotkey'])
        self.cmd2_clear = QPushButton("✕")
        self.cmd2_clear.setObjectName("clearButton")
        self.cmd2_clear.setToolTip("Clear hotkey")
        self.cmd2_clear.clicked.connect(lambda: self.clear_hotkey(2))
        hotkey2_layout.addWidget(self.cmd2_hotkey)
        hotkey2_layout.addWidget(self.cmd2_clear)
        
        cmd2_save = QPushButton('Save')
        cmd2_save.clicked.connect(lambda: self.save_command(2))
        
        cmd2_layout.addWidget(cmd2_label)
        cmd2_layout.addWidget(self.cmd2_text)
        cmd2_layout.addLayout(hotkey2_layout)
        cmd2_layout.addWidget(cmd2_save)
        
        main_layout.addLayout(logout_layout)
        main_layout.addLayout(cmd1_layout)
        main_layout.addLayout(cmd2_layout)
        
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #2D2D2D;
                color: #E0E0E0;
                border-top: 1px solid #555555;
            }
        """)
        self.connection_label = QLabel("Connection: Not connected")
        self.status_bar.addWidget(self.connection_label)
        main_layout.addWidget(self.status_bar)
        
        self.setLayout(main_layout)
        self.hide()
    
    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon()
        pixmap = self.create_icon_pixmap()
        icon.addPixmap(pixmap)
        self.tray_icon.setIcon(icon)
        
        tray_menu = QMenu()
        
        show_action = QAction("Settings", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.close_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    
    def create_icon_pixmap(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setBrush(QBrush(QColor(0, 120, 215)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Arial", 32, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "P")
        
        painter.end()
        return pixmap
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()
    
    def load_settings(self):
        try:
            settings_file = os.path.join(update_checker.APP_DATA_DIR, 'poe_settings.json')
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
            elif os.path.exists('poe_settings.json'):
                with open('poe_settings.json', 'r') as f:
                    loaded_settings = json.load(f)
                    self.settings.update(loaded_settings)
                    self.save_settings()
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            update_checker.ensure_app_data_dir()
            settings_file = os.path.join(update_checker.APP_DATA_DIR, 'poe_settings.json')
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def register_hotkeys(self):
        for hotkey in self.registered_hotkeys:
            try:
                keyboard.remove_hotkey(hotkey)
            except:
                pass
        
        self.registered_hotkeys.clear()
        
        try:
            hotkey = self.settings['command1']['hotkey']
            if not hotkey.startswith('mouse'):
                hotkey1 = keyboard.add_hotkey(
                    hotkey, 
                    lambda: self.execute_command(self.settings['command1']['text']),
                    suppress=True
                )
                self.registered_hotkeys.add(hotkey1)
        except Exception as e:
            print(f"Error registering hotkey 1: {e}")
        
        try:
            hotkey = self.settings['command2']['hotkey']
            if not hotkey.startswith('mouse'):
                hotkey2 = keyboard.add_hotkey(
                    hotkey, 
                    lambda: self.execute_command(self.settings['command2']['text']),
                    suppress=True
                )
                self.registered_hotkeys.add(hotkey2)
        except Exception as e:
            print(f"Error registering hotkey 2: {e}")
        
        try:
            hotkey_settings = keyboard.add_hotkey('f10', self.show_settings)
            self.registered_hotkeys.add(hotkey_settings)
        except Exception as e:
            print(f"Error registering settings hotkey: {e}")
    
    def send_key(self, key_code, up=False):
        extra = ctypes.c_ulong(0)
        ii_ = INPUT_union()
        ii_.ki = KEYBDINPUT(key_code, 0, KEYEVENTF_KEYUP if up else 0, 0, ctypes.pointer(extra))
        x = INPUT(INPUT_KEYBOARD, ii_)
        ctypes.windll.user32.SendInput(1, ctypes.byref(x), ctypes.sizeof(x))
    
    def press_and_release(self, key_code):
        self.send_key(key_code)
        self.send_key(key_code, up=True)
    
    def type_string(self, string):
        for char in string:
            if char == '/':
                key_code = VK_CODE.get('/')
                self.press_and_release(key_code)
            else:
                char_upper = char.upper()
                key_code = ord(char_upper)
                self.press_and_release(key_code)
    
    def execute_command(self, command_text):
        try:
            self.press_and_release(VK_RETURN)
            self.type_string("/" + command_text)
            self.press_and_release(VK_RETURN)
        except Exception as e:
            print(f"Error executing command: {e}")
    
    def start_logout_script(self):
        try:
            hotkey = self.settings['logout']['hotkey']
            success = logout.init_logout_tool(
                hotkey=hotkey
            )
            
            if success:
                hotkey_registered = logout.register_logout_hotkey()
                self.logout_process = hotkey_registered
            else:
                self.logout_process = False
                    
        except Exception as e:
            print(f"Failed to start logout functionality: {e}")
            self.logout_process = False

    def perform_logout(self):
        try:
            logout.perform_logout()
        except Exception as e:
            print(f"Error triggering logout: {e}")
    
    def restart_logout_script(self):
        if self.logout_process:
            logout.shutdown_logout_tool()
            self.logout_process = False
        self.start_logout_script()
    
    def update_connection_display(self):
        try:
            connection_info = logout.get_connection_info()
            if len(connection_info) > 40:
                parts = connection_info.split('->')
                if len(parts) > 1:
                    connection_info = f"...{parts[1]}"
            
            self.connection_label.setText(f"Connection: {connection_info}")
        except Exception:
            self.connection_label.setText("Connection: Error")
    
    def update_logout_script(self):
        self.restart_logout_script()
    
    def save_command(self, command_num):
        if command_num == 1:
            self.settings['command1']['text'] = self.cmd1_text.text()
            self.settings['command1']['hotkey'] = self.cmd1_hotkey.get_hotkey()
        elif command_num == 2:
            self.settings['command2']['text'] = self.cmd2_text.text()
            self.settings['command2']['hotkey'] = self.cmd2_hotkey.get_hotkey()
        else:
            self.settings['logout']['hotkey'] = self.logout_hotkey.get_hotkey()
            self.update_logout_script()
        
        self.save_settings()
        self.register_hotkeys()
    
    def show_settings(self):
        self.show()
        self.activateWindow()
    
    def closeEvent(self, event):
        event.ignore()
        self.hide()
    
    def close_application(self):
        if self.logout_process:
            try:
                logout.shutdown_logout_tool()
            except:
                pass
        
        self.tray_icon.hide()
        QApplication.quit()
    
    def clear_hotkey(self, command_num):
        if command_num == 1:
            self.cmd1_hotkey.set_hotkey("")
        elif command_num == 2:
            self.cmd2_hotkey.set_hotkey("")
        else:
            self.logout_hotkey.set_hotkey("")

def check_single_instance():
    mutex_name = "Global\\XDDBotSingleInstance"
    try:
        mutex = ctypes.windll.kernel32.CreateMutexW(None, 1, mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183:
            return False
        return True
    except:
        return True

def main():
    if not check_single_instance():
        QMessageBox.warning(None, "Already Running", "XDDBot is already running.")
        return sys.exit(1)
        
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app_font = QFont("Segoe UI", 9)
    app.setFont(app_font)
    
    update_result = update_checker.check_for_update_at_startup()
    if update_result == 1:
        return sys.exit(0)
    
    window = CommandHotkeys()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()