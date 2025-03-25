from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt
from ui.key_capture import KeyCaptureWidget

class CommandRowCreator:
    @staticmethod
    def create_command_row(cmd_id, cmd_settings, clear_callback):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(5)
        row_layout.setContentsMargins(5, 3, 5, 3)
        
        components = {}
        
        text_input = QLineEdit(cmd_settings['text'])
        if not cmd_settings.get('is_editable', True):
            text_input.setEnabled(False)
        text_input.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        font = text_input.font()
        font.setBold(True)
        text_input.setFont(font)
        
        text_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555555;
                background-color: #202020;
                border-radius: 3px;
                padding: 3px 5px;
            }
            QLineEdit:focus {
                border: 1px solid #b08d57;
                background-color: #252525;
            }
        """)
        row_layout.addWidget(text_input, 3)
        components['text'] = text_input
            
        hotkey_widget = KeyCaptureWidget(cmd_settings['hotkey'])
        hotkey_widget.setFixedWidth(120)
        hotkey_widget.setStyleSheet("""
            KeyCaptureWidget {
                border: 1px solid #555555;
                background-color: #202020;
                border-radius: 3px;
                padding: 3px 5px;
            }
            KeyCaptureWidget:focus {
                border: 1px solid #b08d57;
                background-color: #252525;
            }
        """)
        
        clear_button = QPushButton("×")
        clear_button.setObjectName("clearButton")
        clear_button.setFixedWidth(22)
        clear_button.setFixedHeight(22)
        clear_button.setStyleSheet("""
            QPushButton#clearButton {
                background-color: #303030;
                color: #E07777;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #555555;
                border-radius: 11px;
                padding: 0px;
            }
            QPushButton#clearButton:hover {
                background-color: #404040;
                color: #FF5555;
                border-color: #AA4444;
            }
            QPushButton#clearButton:pressed {
                background-color: #252525;
                color: #FF3333;
            }
        """)
        clear_button.clicked.connect(lambda checked=False, cid=cmd_id: clear_callback(cid))
        
        hotkey_layout = QHBoxLayout()
        hotkey_layout.setSpacing(4)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_layout.addWidget(hotkey_widget)
        hotkey_layout.addWidget(clear_button)
        row_layout.addLayout(hotkey_layout, 1)
        
        row_layout.addSpacing(5)
            
        components['hotkey'] = hotkey_widget
        components['clear'] = clear_button
        components['row_layout'] = row_layout
            
        return row_layout, components

    @staticmethod
    def create_whisper_row(cmd_id, cmd_settings, clear_callback):
        row_layout = QHBoxLayout()
        row_layout.setSpacing(5)
        row_layout.setContentsMargins(5, 3, 5, 3)
        
        components = {}
        
        text_input = QLineEdit(cmd_settings['text'])
        if not cmd_settings.get('is_editable', True):
            text_input.setEnabled(False)
        text_input.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        font = text_input.font()
        font.setBold(True)
        text_input.setFont(font)
        
        text_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555555;
                background-color: #202020;
                border-radius: 3px;
                padding: 3px 5px;
            }
            QLineEdit:focus {
                border: 1px solid #b08d57;
                background-color: #252525;
            }
        """)
            
        hotkey_widget = KeyCaptureWidget(cmd_settings['hotkey'])
        hotkey_widget.setFixedWidth(120)
        hotkey_widget.setStyleSheet("""
            KeyCaptureWidget {
                border: 1px solid #555555;
                background-color: #202020;
                border-radius: 3px;
                padding: 3px 5px;
            }
            KeyCaptureWidget:focus {
                border: 1px solid #b08d57;
                background-color: #252525;
            }
        """)
        
        clear_button = QPushButton("×")
        clear_button.setObjectName("clearButton")
        clear_button.setFixedWidth(22)
        clear_button.setFixedHeight(22)
        clear_button.setStyleSheet("""
            QPushButton#clearButton {
                background-color: #303030;
                color: #E07777;
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #555555;
                border-radius: 11px;
                padding: 0px;
            }
            QPushButton#clearButton:hover {
                background-color: #404040;
                color: #FF5555;
                border-color: #AA4444;
            }
            QPushButton#clearButton:pressed {
                background-color: #252525;
                color: #FF3333;
            }
        """)
        clear_button.clicked.connect(lambda checked=False, cid=cmd_id: clear_callback(cid))
        
        row_layout.addWidget(text_input, 3)
        
        hotkey_layout = QHBoxLayout()
        hotkey_layout.setSpacing(4)
        hotkey_layout.setContentsMargins(0, 0, 0, 0)
        hotkey_layout.addWidget(hotkey_widget)
        hotkey_layout.addWidget(clear_button)
        row_layout.addLayout(hotkey_layout, 1)
        
        row_layout.addSpacing(5)
            
        components['text'] = text_input
        components['hotkey'] = hotkey_widget
        components['clear'] = clear_button
        components['row_layout'] = row_layout
        
        return row_layout, components 