import sys
import os
import json
import threading
import time
import ctypes
import keyboard
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSystemTrayIcon, QMenu, QAction, QStatusBar, QMessageBox, QScrollArea, QFrame, QGridLayout, QCheckBox, QSizePolicy, QTabWidget
from PyQt5.QtGui import QIcon, QFont, QPixmap, QPainter, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer, QPoint
import win32clipboard
import subprocess
try:
    import logout
    import stashscroll
    import npcap_detector
    import update_checker
except ImportError as e:
    print(f"Failed to import module: {e}")
from ui import KeyCaptureWidget, CommandUI, CommandRowCreator
from hotkey_manager import HotkeyManager
from input_utils import check_single_instance, press_and_release, type_string, VK_RETURN, INPUT, INPUT_union, KEYBDINPUT, KEYEVENTF_KEYUP, INPUT_KEYBOARD

class CommandHotkeys(QWidget):
    def __init__(self):
        super().__init__(None)
        print("Initializing application...")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint) 
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.dragging = False
        self.drag_position = None
        
        self.settings = {
            'logout': {
                'label': 'Logout:',
                'text': 'logout',
                'hotkey': 'f9',
                'is_editable': True
            },
            'command1': {
                'label': '',
                'text': 'hideout',
                'hotkey': 'f5',
                'is_editable': True
            },
            'command2': {
                'label': '',
                'text': 'exit',
                'hotkey': 'f6',
                'is_editable': True
            },
            'command3': {
                'label': '',
                'text': '',
                'hotkey': '',
                'is_editable': True
            }
        }
        self.whisper_settings = {
            'whisper1': {
                'label': '',
                'text': "One moment, I'm lagging",
                'hotkey': '',
                'is_editable': True
            },
            'whisper2': {
                'label': '',
                'text': "Sorry, I DCd that item to standard",
                'hotkey': '',
                'is_editable': True
            },
            'whisper3': {
                'label': '',
                'text': '',
                'hotkey': '',
                'is_editable': True
            }
        }
        self.ui_components = {}
        self.whisper_components = {}
        print("Loading settings...")
        self.load_settings()
        print("Initializing UI...")
        self.init_ui()
        
        print("Creating hotkey manager...")
        self.hotkey_manager = HotkeyManager(self.settings)
        self.hotkey_manager.set_whisper_settings(self.whisper_settings)
        self.hotkey_manager.set_show_settings_callback(self.show_settings)
        
        self.startup_timer = QTimer()
        self.startup_timer.setSingleShot(True)
        self.startup_timer.timeout.connect(self.delayed_startup)
        self.startup_timer.start(200)
        
        self.logout_process = None
        print("Creating tray icon...")
        self.create_tray_icon()
        
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.update_connection_display)
        self.connection_timer.start(2000)
        
        self.ping_timer = QTimer()
        self.ping_timer.timeout.connect(self.update_ping)
        self.ping_timer.start(1000)
        
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        
        self.setMinimumSize(800, 400)
        self.setMaximumWidth(800)
        
        self.hide()
    def register_all_commands(self):
        QTimer.singleShot(200, lambda: self._do_register_commands())
        
    def _do_register_commands(self):
        try:
            print("Registering commands...")
            
            self.hotkey_manager.clear_all_hotkeys()
            
            for cmd_id, cmd_data in self.settings.items():
                if cmd_data.get('hotkey'):
                    print(f"  Command {cmd_id}: '{cmd_data.get('text', '')}' with hotkey '{cmd_data.get('hotkey')}'")
                    
            for cmd_id, cmd_data in self.whisper_settings.items():
                if cmd_data.get('hotkey'):
                    print(f"  Whisper {cmd_id}: '{cmd_data.get('text', '')}' with hotkey '{cmd_data.get('hotkey')}'")
            
            self.hotkey_manager.update_settings(self.settings, self.whisper_settings)
            
            print("Commands registered successfully")
        except Exception as e:
            print(f"Error registering commands: {e}")
            import traceback
            traceback.print_exc()
            
    def init_ui(self):
        self.setWindowTitle('XDDBot')
        
        main_container = QWidget()
        main_container.setObjectName("mainContainer")
        main_container.setStyleSheet("""
            #mainContainer {
                background-color: #1c1c1c;
                border-radius: 10px;
                border: 1px solid #333333;
            }
        """)
        
        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("""
            #titleBar {
                background-color: #121212;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                border-bottom: 1px solid #333333;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        title_layout.setSpacing(0)
        
        title_label = QLabel("XDDBot")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; background-color: transparent;")
        
        close_button = QPushButton("×")
        close_button.setObjectName("closeButton")
        close_button.setFixedSize(24, 24)
        close_button.setStyleSheet("""
            #closeButton {
                background-color: transparent;
                color: #E0E0E0;
                font-size: 20px;
                border: none;
            }
            #closeButton:hover {
                background-color: #E04040;
                color: white;
                border-radius: 12px;
            }
        """)
        close_button.clicked.connect(self.hide)
        
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_button)
        
        self.command_ui = CommandUI(self)
        
        content_container = self.command_ui.build_ui(
            self.settings,
            self.whisper_settings,
            self.clear_hotkey,
            self.clear_whisper_hotkey,
            self.add_new_command,
            self.add_new_whisper,
            self.delete_bottom_command,
            self.delete_bottom_whisper,
            self.discard_changes,
            self.apply_all_settings,
            self.hide
        )
        
        self.ui_components = self.command_ui.ui_components
        self.whisper_components = self.command_ui.whisper_components
        self.status_bar = self.command_ui.status_bar
        
        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(title_bar)
        layout.addWidget(content_container)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(main_container)
        
        title_bar.mousePressEvent = self.title_bar_mouse_press_event
        title_bar.mouseMoveEvent = self.title_bar_mouse_move_event
        title_bar.mouseReleaseEvent = self.title_bar_mouse_release_event
        
        self.setLayout(main_layout)
        
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        main_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        content_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        
        self.setMinimumSize(650, 500)
        
        self.hide()
    def create_command_row(self, cmd_id, cmd_settings):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(5)
        
        if cmd_id != 'logout':
            text_input = QLineEdit(cmd_settings['text'])
            if not cmd_settings.get('is_editable', True):
                text_input.setEnabled(False)
            row_layout.addWidget(text_input, 3)
        else:
            logout_label = QLabel("Logout")
            logout_label.setStyleSheet("color: #FF3030; font-weight: bold;")
            row_layout.addWidget(logout_label, 3)
            
        hotkey_widget = KeyCaptureWidget(cmd_settings['hotkey'])
        if cmd_id == 'logout':
            hotkey_widget.setFixedWidth(150)
        else:
            hotkey_widget.setFixedWidth(90)
        
        clear_button = QPushButton("⨯")
        clear_button.setObjectName("clearButton")
        clear_button.setFixedWidth(20)
        clear_button.clicked.connect(lambda checked=False, cid=cmd_id: self.clear_hotkey(cid))
        
        hotkey_layout = QHBoxLayout()
        hotkey_layout.setSpacing(2)
        hotkey_layout.addWidget(hotkey_widget)
        hotkey_layout.addWidget(clear_button)
        row_layout.addLayout(hotkey_layout, 2)
        
        row_layout.addSpacing(40)
            
        self.ui_components[cmd_id] = {
            'hotkey': hotkey_widget,
            'clear': clear_button,
            'row_layout': row_layout
        }
        
        if cmd_id != 'logout':
            self.ui_components[cmd_id]['text'] = text_input
        else:
            self.ui_components[cmd_id]['label'] = logout_label
            
        return row_layout
        
    def create_whisper_row(self, cmd_id, cmd_settings):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(5)
        
        text_input = QLineEdit(cmd_settings['text'])
        if not cmd_settings.get('is_editable', True):
            text_input.setEnabled(False)
            
        hotkey_widget = KeyCaptureWidget(cmd_settings['hotkey'])
        hotkey_widget.setFixedWidth(90)
        
        clear_button = QPushButton("⨯")
        clear_button.setObjectName("clearButton")
        clear_button.setFixedWidth(20)
        clear_button.clicked.connect(lambda checked=False, cid=cmd_id: self.clear_whisper_hotkey(cid))
        
        row_layout.addWidget(text_input, 3)
        
        hotkey_layout = QHBoxLayout()
        hotkey_layout.setSpacing(2)
        hotkey_layout.addWidget(hotkey_widget)
        hotkey_layout.addWidget(clear_button)
        row_layout.addLayout(hotkey_layout, 2)
        
        row_layout.addSpacing(40)
            
        self.whisper_components[cmd_id] = {
            'text': text_input,
            'hotkey': hotkey_widget,
            'clear': clear_button,
            'row_layout': row_layout
        }
        
        return row_layout
    def delete_command(self, cmd_id):
        if cmd_id in self.settings and cmd_id != 'logout':
            print(f"Deleting command {cmd_id}")
            
            self.setUpdatesEnabled(False)
            
            tab_widget = self.findChild(QTabWidget)
            current_tab = 0
            if tab_widget:
                current_tab = tab_widget.currentIndex()
            
            hotkey = self.settings[cmd_id].get('hotkey')
            if hotkey:
                self.hotkey_manager.clear_all_hotkeys()
            
            del self.settings[cmd_id]
            
            components = self.ui_components.pop(cmd_id, None)
            if components and 'row_layout' in components:
                row_layout = components['row_layout']
                
                if row_layout:
                    while row_layout.count():
                        item = row_layout.takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()
                        elif item.layout():
                            self._clear_layout(item.layout())
            
            self.recreate_ui()
            
            tab_widget = self.findChild(QTabWidget)
            if tab_widget:
                tab_widget.setCurrentIndex(current_tab)
            
            current_height = self.height()
            row_height = 40
            spacing = 8
            new_height = max(400, current_height - (row_height + spacing))
            self.resize(self.width(), new_height)
            
            QTimer.singleShot(100, lambda: self.hotkey_manager.update_settings(self.settings, self.whisper_settings))
            
            self.setUpdatesEnabled(True)
            
            QApplication.processEvents()
            
            self.status_bar.showMessage("Command removed. Click Apply to save changes.", 3000)
            print(f"Command {cmd_id} removed from settings")
        else:
            print(f"Cannot delete command {cmd_id} - not found or is logout")

    def _clear_layout(self, layout):
        """Recursively remove all items from a layout"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())
            
    def delete_whisper_command(self, cmd_id):
        if cmd_id in self.whisper_settings:
            print(f"Deleting whisper command {cmd_id}")
            
            self.setUpdatesEnabled(False)
            
            tab_widget = self.findChild(QTabWidget)
            current_tab = 1
            if tab_widget:
                current_tab = tab_widget.currentIndex()
            
            hotkey = self.whisper_settings[cmd_id].get('hotkey')
            if hotkey:
                self.hotkey_manager.clear_all_hotkeys()
            
            del self.whisper_settings[cmd_id]
            
            components = self.whisper_components.pop(cmd_id, None)
            if components and 'row_layout' in components:
                row_layout = components['row_layout']
                
                if row_layout:
                    while row_layout.count():
                        item = row_layout.takeAt(0)
                        if item.widget():
                            item.widget().deleteLater()
                        elif item.layout():
                            self._clear_layout(item.layout())
            
            self.recreate_ui()
            
            tab_widget = self.findChild(QTabWidget)
            if tab_widget:
                tab_widget.setCurrentIndex(current_tab)
            
            current_height = self.height()
            row_height = 40
            spacing = 8
            new_height = max(400, current_height - (row_height + spacing))
            self.resize(self.width(), new_height)
            
            QTimer.singleShot(100, lambda: self.hotkey_manager.update_settings(self.settings, self.whisper_settings))
            
            self.setUpdatesEnabled(True)
            
            QApplication.processEvents()
            
            self.status_bar.showMessage("Whisper command removed. Click Apply to save changes.", 3000)
            print(f"Whisper command {cmd_id} removed from settings")
        else:
            print(f"Cannot delete whisper command {cmd_id} - not found")

    def delete_bottom_command(self):
        command_ids = [cmd_id for cmd_id in self.settings.keys() if cmd_id != 'logout']
        if not command_ids:
            return
        
        def get_command_number(cmd_id):
            try:
                return int(cmd_id.replace('command', ''))
            except:
                return 0
            
        last_command = sorted(command_ids, key=get_command_number)[-1]
        self.delete_command(last_command)
        self.status_bar.showMessage(f"Deleted command {last_command}. Click Apply to save changes.", 3000)
    
    def delete_bottom_whisper(self):
        whisper_ids = [cmd_id for cmd_id in self.whisper_settings.keys() if cmd_id.startswith('whisper')]
        if not whisper_ids:
            return
        
        def get_whisper_number(cmd_id):
            try:
                return int(cmd_id.replace('whisper', ''))
            except:
                return 0
            
        last_whisper = sorted(whisper_ids, key=get_whisper_number)[-1]
        self.delete_whisper_command(last_whisper)
        self.status_bar.showMessage(f"Deleted whisper {last_whisper}. Click Apply to save changes.", 3000)
    def add_new_command(self):
        if len(self.settings) - 1 >= 15:
            self.status_bar.showMessage("Maximum limit of 15 game commands reached", 3000)
            return
            
        self.setUpdatesEnabled(False)
        
        tab_widget = self.findChild(QTabWidget)
        current_tab = 0
        if tab_widget:
            current_tab = tab_widget.currentIndex()
        
        next_id = 3
        while f'command{next_id}' in self.settings:
            next_id += 1
            
        cmd_id = f'command{next_id}'
        self.settings[cmd_id] = {'label': '', 'text': '', 'hotkey': '', 'is_editable': True}
        
        self.recreate_ui()
        
        tab_widget = self.findChild(QTabWidget)
        if tab_widget:
            tab_widget.setCurrentIndex(current_tab)
        
        current_height = self.height()
        row_height = 40
        spacing = 8
        new_height = current_height + row_height + spacing
        self.resize(self.width(), new_height)
        
        self.setUpdatesEnabled(True)
        
        QApplication.processEvents()
        
        self.status_bar.showMessage("Command added. Set text and hotkey, then click Apply.", 3000)
        
    def add_new_whisper(self):
        if len(self.whisper_settings) >= 15:
            self.status_bar.showMessage("Maximum limit of 15 whisper commands reached", 3000)
            return
            
        self.setUpdatesEnabled(False)
        
        tab_widget = self.findChild(QTabWidget)
        current_tab = 1
        if tab_widget:
            current_tab = tab_widget.currentIndex()
        
        next_id = len(self.whisper_settings) + 1
        while f'whisper{next_id}' in self.whisper_settings:
            next_id += 1
            
        cmd_id = f'whisper{next_id}'
        self.whisper_settings[cmd_id] = {'label': '', 'text': '', 'hotkey': '', 'is_editable': True}
        
        self.recreate_ui()
        
        tab_widget = self.findChild(QTabWidget)
        if tab_widget:
            tab_widget.setCurrentIndex(current_tab)
        
        current_height = self.height()
        row_height = 40
        spacing = 8
        new_height = current_height + row_height + spacing
        self.resize(self.width(), new_height)
        
        self.setUpdatesEnabled(True)
        
        QApplication.processEvents()
        
        self.status_bar.showMessage("Whisper added. Set text and hotkey, then click Apply.", 3000)
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
        update_action = QAction("Check for Updates", self)
        update_action.triggered.connect(self.check_for_updates_action)
        tray_menu.addAction(update_action)
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.close_application)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
    def check_for_updates_action(self):
        try:
            result = update_checker.force_update_check()
            if result == 0:
                QMessageBox.information(self, "Updates", "No new updates available.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not check for updates: {str(e)}")
    def create_icon_pixmap(self):
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(0, 120, 215)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
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
                    if 'commands' in loaded_settings:
                        for cmd_id, cmd_data in loaded_settings['commands'].items():
                            if cmd_id in self.settings:
                                if 'text' in cmd_data:
                                    self.settings[cmd_id]['text'] = cmd_data['text']
                                if 'hotkey' in cmd_data:
                                    self.settings[cmd_id]['hotkey'] = cmd_data['hotkey']
                            elif cmd_id.startswith('command'):
                                self.settings[cmd_id] = cmd_data
                    if 'whispers' in loaded_settings:
                        for cmd_id, cmd_data in loaded_settings['whispers'].items():
                            if cmd_id in self.whisper_settings:
                                if 'text' in cmd_data:
                                    self.whisper_settings[cmd_id]['text'] = cmd_data['text']
                                if 'hotkey' in cmd_data:
                                    self.whisper_settings[cmd_id]['hotkey'] = cmd_data['hotkey']
                            elif cmd_id.startswith('whisper'):
                                self.whisper_settings[cmd_id] = cmd_data
            elif os.path.exists('poe_settings.json'):
                with open('poe_settings.json', 'r') as f:
                    loaded_settings = json.load(f)
                    for cmd_id, cmd_data in loaded_settings.items():
                        if cmd_id in self.settings:
                            if 'text' in cmd_data:
                                self.settings[cmd_id]['text'] = cmd_data['text']
                            if 'hotkey' in cmd_data:
                                self.settings[cmd_id]['hotkey'] = cmd_data['hotkey']
                    self.save_settings()
        except Exception as e:
            print(f"Error loading settings: {e}")
    def save_settings(self):
        try:
            print("Saving settings...")
            update_checker.ensure_app_data_dir()
            settings_file = os.path.join(update_checker.APP_DATA_DIR, 'poe_settings.json')
            
            save_data = {'commands': {}, 'whispers': {}}
            
            for cmd_id, cmd_data in self.settings.items():
                save_data['commands'][cmd_id] = {
                    'label': cmd_data.get('label', ''),
                    'text': cmd_data.get('text', ''),
                    'hotkey': cmd_data.get('hotkey', ''),
                    'is_editable': cmd_data.get('is_editable', True)
                }
                
            for cmd_id, cmd_data in self.whisper_settings.items():
                save_data['whispers'][cmd_id] = {
                    'label': cmd_data.get('label', ''),
                    'text': cmd_data.get('text', ''),
                    'hotkey': cmd_data.get('hotkey', ''),
                    'is_editable': cmd_data.get('is_editable', True)
                }
                
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
                
            with open(settings_file, 'w') as f:
                json.dump(save_data, f, indent=4)
                
            print(f"Settings saved successfully to {settings_file}")
        except Exception as e:
            print(f"Error saving settings: {e}")
            import traceback
            traceback.print_exc()
    def start_logout_script(self):
        try:
            print("Starting logout script...")
            hotkey = self.settings['logout']['hotkey']
            print(f"Using logout hotkey: {hotkey}")
            
            success = logout.init_logout_tool(hotkey=hotkey)
            if success:
                print("Logout tool initialized, registering hotkey...")
                hotkey_registered = logout.register_logout_hotkey()
                if hotkey_registered:
                    self.logout_process = hotkey_registered
                    print("Logout hotkey registered successfully")
                else:
                    self.logout_process = False
                    print("Failed to register logout hotkey")
            else:
                self.logout_process = False
                print("Failed to initialize logout tool")
        except Exception as e:
            print(f"Failed to start logout functionality: {str(e)}")
            import traceback
            traceback.print_exc()
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
    def update_logout_script(self):
        logout_components = self.ui_components.get('logout')
        if logout_components and 'hotkey' in logout_components:
            self.settings['logout']['hotkey'] = logout_components['hotkey'].get_hotkey()
        
        self.restart_logout_script()
    def save_command(self, cmd_id):
        try:
            print(f"Saving command {cmd_id}")
            components = self.ui_components.get(cmd_id)
            if not components:
                print(f"No components found for {cmd_id}")
                return
                
            if cmd_id == 'logout':
                self.settings[cmd_id]['hotkey'] = components['hotkey'].get_hotkey()
                self.update_logout_script()
            else:
                self.settings[cmd_id]['text'] = components['text'].text()
                self.settings[cmd_id]['hotkey'] = components['hotkey'].get_hotkey()
                
            self.save_settings()
            
            QTimer.singleShot(500, lambda: self._do_register_commands())
            self.status_bar.showMessage(f"Command '{cmd_id}' saved successfully", 3000)
        except Exception as e:
            print(f"Error saving command {cmd_id}: {e}")
            self.status_bar.showMessage(f"Error saving command: {str(e)}", 3000)
            
    def save_whisper_command(self, cmd_id):
        try:
            print(f"Saving whisper command {cmd_id}")
            components = self.whisper_components.get(cmd_id)
            if not components:
                print(f"No components found for {cmd_id}")
                return
                
            self.whisper_settings[cmd_id]['text'] = components['text'].text()
            self.whisper_settings[cmd_id]['hotkey'] = components['hotkey'].get_hotkey()
            
            self.save_settings()
            
            QTimer.singleShot(500, lambda: self._do_register_commands())
            
            if components['hotkey'].get_hotkey():
                self.status_bar.showMessage(f"Whisper command saved with hotkey: {components['hotkey'].get_hotkey()}", 3000)
            else:
                self.status_bar.showMessage("Whisper command saved (no hotkey assigned)", 3000)
        except Exception as e:
            print(f"Error saving whisper command {cmd_id}: {e}")
            self.status_bar.showMessage(f"Error saving whisper command: {str(e)}", 3000)
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
    def clear_hotkey(self, cmd_id):
        components = self.ui_components.get(cmd_id)
        if components:
            components['hotkey'].set_hotkey("")
    def clear_whisper_hotkey(self, cmd_id):
        components = self.whisper_components.get(cmd_id)
        if components:
            components['hotkey'].set_hotkey("")
    def delayed_startup(self):
        print("Performing startup initialization...")
        try:
            self._do_register_commands()
            
            self.start_logout_script()
            
            QTimer.singleShot(300, self._final_startup_attempt)
            
            print("Initial startup complete")
        except Exception as e:
            print(f"Error in delayed startup: {e}")
            
    def _final_startup_attempt(self):
        print("Performing final hotkey registration...")
        try:
            self.hotkey_manager.register_all_hotkeys()
            print("Final registration complete, hotkeys should be active")
        except Exception as e:
            print(f"Error in final startup attempt: {e}")
    def apply_all_settings(self):
        try:
            print("Applying all settings...")
            
            self.setUpdatesEnabled(False)
            
            for cmd_id, components in self.ui_components.items():
                if cmd_id != 'logout':
                    if 'text' in components:
                        self.settings[cmd_id]['text'] = components['text'].text()
                    self.settings[cmd_id]['hotkey'] = components['hotkey'].get_hotkey()
                else:
                    self.settings[cmd_id]['hotkey'] = components['hotkey'].get_hotkey()
            
            for cmd_id, components in self.whisper_components.items():
                self.whisper_settings[cmd_id]['text'] = components['text'].text()
                self.whisper_settings[cmd_id]['hotkey'] = components['hotkey'].get_hotkey()
            
            self.hotkey_manager.clear_all_hotkeys()
            
            self.save_settings()
            
            self.update_logout_script()
            
            QTimer.singleShot(100, lambda: self._do_register_commands())
            
            self.setUpdatesEnabled(True)
            
            self.status_bar.showMessage("All settings applied successfully", 3000)
            print("All settings applied successfully")
        except Exception as e:
            print(f"Error applying all settings: {e}")
            import traceback
            traceback.print_exc()
            self.setUpdatesEnabled(True)
            self.status_bar.showMessage(f"Error applying all settings: {str(e)}", 3000)
    def discard_changes(self):
        print("Discarding changes...")
        
        self.setUpdatesEnabled(False)
        
        self.hotkey_manager.clear_all_hotkeys()
        
        window_pos = self.pos()
        
        tab_widget = self.findChild(QTabWidget)
        current_tab = 0
        if tab_widget:
            current_tab = tab_widget.currentIndex()
        
        try:
            update_checker.ensure_app_data_dir()
            settings_file = os.path.join(update_checker.APP_DATA_DIR, 'poe_settings.json')
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                    
                    current_logout_hotkey = self.settings.get('logout', {}).get('hotkey', 'f9')
                    
                    self.settings = {}
                    self.whisper_settings = {}
                    
                    self.settings['logout'] = {
                        'label': 'Logout:',
                        'text': 'logout',
                        'hotkey': loaded_settings.get('commands', {}).get('logout', {}).get('hotkey', current_logout_hotkey),
                        'is_editable': True
                    }
                    
                    if 'commands' in loaded_settings:
                        for cmd_id, cmd_data in loaded_settings['commands'].items():
                            if cmd_id != 'logout':
                                self.settings[cmd_id] = {
                                    'label': cmd_data.get('label', ''),
                                    'text': cmd_data.get('text', ''),
                                    'hotkey': cmd_data.get('hotkey', ''),
                                    'is_editable': cmd_data.get('is_editable', True)
                                }
                    
                    if 'whispers' in loaded_settings:
                        for cmd_id, cmd_data in loaded_settings['whispers'].items():
                            self.whisper_settings[cmd_id] = {
                                'label': cmd_data.get('label', ''),
                                'text': cmd_data.get('text', ''),
                                'hotkey': cmd_data.get('hotkey', ''),
                                'is_editable': cmd_data.get('is_editable', True)
                            }
            else:
                self.status_bar.showMessage("No saved settings found to discard to", 3000)
                self.setUpdatesEnabled(True)
                return
        except Exception as e:
            print(f"Error loading settings: {e}")
            import traceback
            traceback.print_exc()
            self.status_bar.showMessage(f"Error loading settings: {str(e)}", 3000)
            self.setUpdatesEnabled(True)
            return
            
        self.recreate_ui()
        
        base_height = 400
        row_height = 40
        spacing = 8
        command_count = len(self.settings) - 1
        whisper_count = len(self.whisper_settings)
        max_count = max(command_count, whisper_count)
        window_height = base_height + (max_count * (row_height + spacing))
        
        self.resize(self.width(), window_height)
        
        QApplication.processEvents()
        
        tab_widget = self.findChild(QTabWidget)
        if tab_widget:
            tab_widget.setCurrentIndex(current_tab)
        
        QTimer.singleShot(100, lambda: self.hotkey_manager.update_settings(self.settings, self.whisper_settings))
        
        self.update_logout_script()
        
        self.setUpdatesEnabled(True)
        
        self.status_bar.showMessage("Changes discarded. Reverted to saved settings.", 3000)
        print("Changes discarded. Reverted to saved settings.")

    def recreate_ui(self):
        """Recreate the UI to reflect updated settings"""
        try:
            if self.layout():
                old_layout = self.layout()
                
                QWidget().setLayout(old_layout)
            
            self.command_ui = CommandUI(self)
            container = self.command_ui.build_ui(
                self.settings,
                self.whisper_settings,
                self.clear_hotkey,
                self.clear_whisper_hotkey,
                self.add_new_command,
                self.add_new_whisper,
                self.delete_bottom_command,
                self.delete_bottom_whisper,
                self.discard_changes,
                self.apply_all_settings,
                self.hide
            )
            
            main_container = QWidget()
            main_container.setObjectName("mainContainer")
            main_container.setStyleSheet("""
                #mainContainer {
                    background-color: #1c1c1c;
                    border-radius: 10px;
                    border: 1px solid #333333;
                }
            """)
            
            title_bar = QWidget()
            title_bar.setObjectName("titleBar")
            title_bar.setFixedHeight(40)
            title_bar.setStyleSheet("""
                #titleBar {
                    background-color: #121212;
                    border-top-left-radius: 10px;
                    border-top-right-radius: 10px;
                    border-bottom: 1px solid #333333;
                }
            """)
            
            title_layout = QHBoxLayout(title_bar)
            title_layout.setContentsMargins(15, 0, 15, 0)
            
            title_label = QLabel("XDDBot")
            title_label.setStyleSheet("font-weight: bold; font-size: 14px; background-color: transparent;")
            
            close_button = QPushButton("×")
            close_button.setObjectName("closeButton")
            close_button.setFixedSize(24, 24)
            close_button.setStyleSheet("""
                #closeButton {
                    background-color: transparent;
                    color: #E0E0E0;
                    font-size: 20px;
                    border: none;
                }
                #closeButton:hover {
                    background-color: #E04040;
                    color: white;
                    border-radius: 12px;
                }
            """)
            close_button.clicked.connect(self.hide)
            
            title_layout.addWidget(title_label)
            title_layout.addStretch()
            title_layout.addWidget(close_button)
            
            container_layout = QVBoxLayout(main_container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            container_layout.addWidget(title_bar)
            container_layout.addWidget(container)
            
            main_layout = QVBoxLayout()
            main_layout.setContentsMargins(10, 10, 10, 10)
            main_layout.addWidget(main_container)
            self.setLayout(main_layout)
            
            title_bar.mousePressEvent = self.title_bar_mouse_press_event
            title_bar.mouseMoveEvent = self.title_bar_mouse_move_event
            title_bar.mouseReleaseEvent = self.title_bar_mouse_release_event
            
            self.ui_components = self.command_ui.ui_components
            self.whisper_components = self.command_ui.whisper_components
            self.status_bar = self.command_ui.status_bar
            
            self.connection_label = getattr(self.command_ui, 'connection_label', None)
            self.connection_image = getattr(self.command_ui, 'connection_image', None)
            self.ping_label = getattr(self.command_ui, 'ping_label', None)
        except Exception as e:
            print(f"Error recreating UI: {e}")
            import traceback
            traceback.print_exc()

    def title_bar_mouse_press_event(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
            
    def title_bar_mouse_move_event(self, event):
        if event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
            
    def title_bar_mouse_release_event(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
            
    def show(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, 
                  (screen.height() - size.height()) // 2)
        
        super().show()

    def update_connection_display(self):
        try:
            connection_info = getattr(logout, 'get_connection_info', lambda: None)()
            if connection_info and "->" in connection_info:
                if hasattr(self, 'connection_image') and self.connection_image:
                    self.connection_image.setVisible(True)
                if hasattr(self, 'connection_label') and self.connection_label:
                    self.connection_label.setText("")
            else:
                if hasattr(self, 'connection_label') and self.connection_label:
                    self.connection_label.setText("")
                if hasattr(self, 'connection_image') and self.connection_image:
                    self.connection_image.setVisible(False)
        except Exception:
            if hasattr(self, 'connection_label') and self.connection_label:
                self.connection_label.setText("")
            if hasattr(self, 'connection_image') and self.connection_image:
                self.connection_image.setVisible(False)

    def update_ping(self):
        """Update the ping display with current latency to Path of Exile servers"""
        try:
            if not hasattr(self, 'ping_label') or self.ping_label is None:
                return
            
            servers = [
                'login.pathofexile.com',
                'www.pathofexile.com',
                'pathofexile.com'
            ]
            
            min_ping = float('inf')
            for server in servers:
                try:
                    result = subprocess.run(['ping', '-n', '1', '-w', '1000', server], 
                                         capture_output=True, text=True)
                    
                    if 'Average = ' in result.stdout:
                        ping_str = result.stdout.split('Average = ')[-1].split('ms')[0].strip()
                        ping = int(ping_str)
                        min_ping = min(min_ping, ping)
                except:
                    continue
            
            if min_ping != float('inf'):
                self.ping_label.setText(f"Ping: {min_ping} ms")
                if min_ping < 100:
                    self.ping_label.setStyleSheet("color: #00FF00;")
                elif min_ping < 200:
                    self.ping_label.setStyleSheet("color: #FFFF00;")
                else:
                    self.ping_label.setStyleSheet("color: #FF0000;")
            else:
                self.ping_label.setText("Ping: -- ms")
                self.ping_label.setStyleSheet("color: #FF0000;")
        except Exception as e:
            print(f"Error updating ping: {e}")
            try:
                if hasattr(self, 'ping_label') and self.ping_label is not None:
                    self.ping_label.setText("Ping: -- ms")
                    self.ping_label.setStyleSheet("color: #FF0000;")
            except:
                pass

def main():
    if not check_single_instance():
        QMessageBox.warning(None, "Already Running", "XDDBot is already running.")
        return sys.exit(1)
        
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app_font = QFont("Segoe UI", 9)
    app.setFont(app_font)
    
    app.setStyleSheet("""
        QWidget {
            background-color: #1c1c1c;
            color: #E0E0E0;
        }
        QMessageBox, QDialog {
            background-color: #1c1c1c;
            color: #E0E0E0;
        }
        QLineEdit {
            font-weight: bold;
        }
    """)
    
    update_result = update_checker.check_for_update_at_startup()
    if update_result == 1:
        return sys.exit(0)
    
    window = CommandHotkeys()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
