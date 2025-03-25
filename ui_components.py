from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                         QStatusBar, QToolButton, QSizePolicy, QFrame, QScrollArea, QApplication,
                         QTabWidget, QTabBar, QMenu, QAction, QGridLayout, QLayout)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap, QTransform, QKeySequence, QBrush, QPen, QPainter

_qapp = None
if QApplication.instance() is None and not hasattr(QApplication, '_in_test'):
    import sys
    _qapp = QApplication([sys.argv[0]])
    _qapp.setQuitOnLastWindowClosed(False)
    
__all__ = ['KeyCaptureWidget', 'CommandUI', 'CommandRowCreator']

class KeyCaptureWidget(QLineEdit):
    def __init__(self, initial_hotkey='', parent=None):
        super().__init__(parent)
        self.hotkey = initial_hotkey
        self.setText(initial_hotkey if initial_hotkey else "No key set")
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setCursorPosition(0)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.setCursor(Qt.PointingHandCursor)
        self.setPlaceholderText("Click to capture hotkey...")
        self.setToolTip("Click once to start capturing, then press any key or mouse button")
        self.setFocusPolicy(Qt.ClickFocus)
        self.capturing = False
        self.ignore_next_release = False
        
        font = self.font()
        font.setBold(True)
        self.setFont(font)
        
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.capturing = True
        self.ignore_next_release = True
        self.setText("Press a key...")
        self.selectAll()
        
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.capturing = False
        if not self.hotkey:
            self.setText("No key set")
        else:
            self.setText(self.hotkey)
    
    def mousePressEvent(self, event):
        if not self.capturing:
            super().mousePressEvent(event)
            return
            
        if self.ignore_next_release:
            self.ignore_next_release = False
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
        
        if event.key() == Qt.Key_Escape:
            self.capturing = False
            self.setText(self.hotkey if self.hotkey else "No key set")
            self.clearFocus()
            return
            
        modifiers = []
        if event.modifiers() & Qt.ControlModifier:
            modifiers.append("ctrl")
        if event.modifiers() & Qt.AltModifier:
            modifiers.append("alt")
        if event.modifiers() & Qt.ShiftModifier:
            modifiers.append("shift")
            
        key = event.key()
        key_text = ""
        
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return
        
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
                Qt.Key_Down: "down",
                Qt.Key_Period: ".",
                Qt.Key_Comma: ",",
                Qt.Key_Plus: "+",
                Qt.Key_Minus: "-",
                Qt.Key_Slash: "/",
                Qt.Key_Backslash: "\\",
                Qt.Key_Semicolon: ";",
                Qt.Key_Equal: "="
            }
            key_text = key_map.get(key, "")
            
        if not key_text:
            event.accept()
            return
            
        if modifiers:
            self.hotkey = "+".join(modifiers + [key_text])
        else:
            self.hotkey = key_text
            
        self.setText(self.hotkey)
        self.clearFocus()
        event.accept()
        
    def get_hotkey(self):
        return self.hotkey
        
    def set_hotkey(self, hotkey):
        self.hotkey = hotkey
        self.setText(hotkey if hotkey else "No key set")

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

class CustomTitleBar(QWidget):
    def __init__(self, parent=None, title="", minimize_callback=None, close_callback=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setObjectName("titleBar")
        self.parent = parent
        self.oldPos = None
        self.close_callback = close_callback or (lambda: None)
        
        self.setStyleSheet("""
            #titleBar {
                background-color: #1c1c1c;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            #titleLabel {
                color: #b08d57;
                font-weight: bold;
            }
            #closeButton {
                background-color: transparent;
                color: #AAAAAA;
                font-weight: bold;
                border: none;
            }
            #closeButton:hover {
                background-color: #FF3030;
                color: #FFFFFF;
            }
        """)
        
        self.setMouseTracking(True)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("titleLabel")
        layout.addWidget(self.title_label)
        
        layout.addStretch()
        
        self.close_button = QPushButton("✕")
        self.close_button.setObjectName("closeButton")
        self.close_button.setFixedSize(30, 26)
        self.close_button.clicked.connect(self.close_callback)
        layout.addWidget(self.close_button)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos and event.buttons() & Qt.LeftButton:
            toplevel = self.window()
            delta = QPoint(event.globalPos() - self.oldPos)
            toplevel.move(toplevel.pos() + delta)
            self.oldPos = event.globalPos()
            
    def mouseReleaseEvent(self, event):
        self.oldPos = None

class CollapsibleSection(QWidget):
    def __init__(self, title, parent=None):
        super(CollapsibleSection, self).__init__(parent)
        
        self.button_stylesheet = """
            QPushButton {
                text-align: left;
                padding: 8px;
                border: none;
                background-color: #121212;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
            }
        """
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.toggle_button = QPushButton(title)
        self.toggle_button.setStyleSheet(self.button_stylesheet)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.clicked.connect(self.toggle_section)
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self.toggle_button)
        
        self.content_area = QWidget()
        self.content_area.setVisible(False)
        
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 1, 0, 1)
        self.content_layout.setSpacing(2)
        
        self.main_layout.addLayout(button_layout)
        self.main_layout.addWidget(self.content_area)
        
        self.add_button_container = QWidget()
        self.add_button_layout = QHBoxLayout(self.add_button_container)
        self.add_button_layout.setContentsMargins(0, 1, 0, 1)
        
        self.add_button_layout.addStretch()
        self.add_row_button = QPushButton("+")
        self.add_row_button.setFixedSize(24, 24)
        self.add_row_button.setStyleSheet("""
            QPushButton {
                border-radius: 12px;
                background-color: #2a2a2a;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
        self.add_button_layout.addWidget(self.add_row_button)
        self.add_button_layout.addStretch()
        
        self.content_layout.addWidget(self.add_button_container)
        self.add_button_container.setVisible(False)
        
    def toggle_section(self):
        self.content_area.setVisible(not self.content_area.isVisible())
        
        self.add_button_container.setVisible(self.content_area.isVisible())
        
        font = self.toggle_button.font()
        if self.content_area.isVisible():
            self.toggle_button.setText("▼ " + self.toggle_button.text().replace("▶ ", ""))
        else:
            self.toggle_button.setText("▶ " + self.toggle_button.text().replace("▼ ", ""))
        self.toggle_button.setFont(font)
        
    def add_widget(self, widget):
        self.content_layout.insertWidget(self.content_layout.count() - 1, widget)
    
    def add_layout(self, layout):
        layout.setSpacing(2)
        self.content_layout.insertLayout(self.content_layout.count() - 1, layout)

class LogoutIndicator(QFrame):
    def __init__(self, logout_settings):
        super().__init__()
        self.setObjectName("logoutIndicator")
        self.hotkey = logout_settings['hotkey']
        self.text = logout_settings['text']
        
        self.setFixedHeight(36)
        
        self.setStyleSheet("""
            #logoutIndicator {
                background-color: transparent;
                border-radius: 4px;
                padding: 0px;
            }
            QLabel {
                color: white;
            }
        """)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 0, 8, 0)
        self.layout.setSpacing(5)
        
        left_layout = QHBoxLayout()
        left_layout.setSpacing(5)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.logout_text = QLabel("LOGOUT:")
        self.logout_text.setStyleSheet("""
            font-weight: bold; 
            font-size: 16px;
            color: #b08d57;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8);
        """)
        
        self.key_box = QFrame()
        self.key_box.setObjectName("keyBox")
        self.key_box.setStyleSheet("""
            #keyBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #e74c3c, stop:1 #c0392b);
                border-radius: 3px;
                border: 1px solid #a52a2a;
                border-bottom: 2px solid #8b0000;
            }
        """)
        self.key_box.setFixedWidth(120)
        
        key_layout = QHBoxLayout(self.key_box)
        key_layout.setContentsMargins(8, 2, 8, 2)
        key_layout.setSpacing(0)
        
        self.key_label = QLabel(self.hotkey.upper())
        self.key_label.setStyleSheet("""
            font-weight: bold; 
            font-size: 16px;
            color: white;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
        """)
        key_layout.addWidget(self.key_label)
        
        left_layout.addWidget(self.logout_text)
        left_layout.addWidget(self.key_box)
        left_layout.addStretch(1)
        
        self.layout.addLayout(left_layout, 3)


class BaseLayout:
    def __init__(self):
        self.name = "base"
        self.description = "Base Layout"
    
    def build_ui(self, parent, settings, whisper_settings, callbacks):
        pass

class CompactAccordionLayout(BaseLayout):
    def __init__(self):
        super().__init__()
        self.name = "compact_accordion"
        self.description = "Compact Accordion Layout with Collapsible Sections"
        
    def build_ui(self, parent, settings, whisper_settings, callbacks):
        if parent.layout() is not None:
            while parent.layout().count():
                item = parent.layout().takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            
            parent.layout().deleteLater()
        
        parent.setAttribute(Qt.WA_TranslucentBackground)
        parent.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        content_container = QWidget()
        content_container.setObjectName("contentContainer")
        content_container.setStyleSheet("""
            #contentContainer {
                background-color: #1c1c1c;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }
        """)
        
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(0)
        
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        logout_settings = settings.get('logout', {
            'label': 'Logout:',
            'text': 'logout',
            'hotkey': 'f9',
            'is_editable': False
        })
        logout_indicator = LogoutIndicator(logout_settings)
        
        apply_button = QPushButton("Apply")
        apply_button.setObjectName("applyButton")
        apply_button.setFixedSize(60, 24)
        apply_button.clicked.connect(callbacks.get("apply_callback", lambda: None))
        
        discard_button = QPushButton("Discard")
        discard_button.setObjectName("discardButton")
        discard_button.setFixedSize(60, 24)
        discard_button.clicked.connect(callbacks.get("discard_callback", lambda: None))
        
        right_layout = QHBoxLayout()
        right_layout.addStretch(1)
        right_layout.addWidget(discard_button)
        right_layout.addWidget(apply_button)
        
        logout_indicator.layout.addLayout(right_layout, 5)
        
        content_layout.addWidget(logout_indicator)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        
        commands_section = CollapsibleSection("GAME COMMANDS")
        whispers_section = CollapsibleSection("WHISPER COMMANDS")
        
        commands_section.add_row_button.clicked.connect(callbacks.get("add_command_callback", lambda: None))
        whispers_section.add_row_button.clicked.connect(callbacks.get("add_whisper_callback", lambda: None))
        
        ui_components = {}
        for key, command in settings.items():
            if key == 'logout':
                row_layout, components = CommandRowCreator.create_command_row(
                    key, 
                    command, 
                    callbacks.get("clear_callback", lambda x: None)
                )
                ui_components[key] = components
                continue
                
            row_layout, components = CommandRowCreator.create_command_row(
                key,
                command,
                callbacks.get("clear_callback", lambda x: None)
            )
            
            row_container = QWidget()
            row_container.setStyleSheet("background-color: #3d3d3d; border-radius: 4px;")
            container_layout = QVBoxLayout(row_container)
            container_layout.setContentsMargins(5, 5, 5, 5)
            container_layout.addLayout(row_layout)
            
            commands_section.add_widget(row_container)
            ui_components[key] = components
        
        whisper_components = {}
        for key, whisper in whisper_settings.items():
            row_layout, components = CommandRowCreator.create_whisper_row(
                key, 
                whisper, 
                callbacks.get("clear_whisper_callback", lambda x: None)
            )
            
            row_container = QWidget()
            row_container.setStyleSheet("background-color: #3d3d3d; border-radius: 4px;")
            container_layout = QVBoxLayout(row_container)
            container_layout.setContentsMargins(5, 5, 5, 5)
            container_layout.addLayout(row_layout)
            
            whispers_section.add_widget(row_container)
            whisper_components[key] = components
        
        scroll_layout.addWidget(commands_section)
        scroll_layout.addWidget(whispers_section)
        
        scroll_area.setWidget(scroll_content)
        content_layout.addWidget(scroll_area)
        
        main_layout.addWidget(content_container, 1)
        
        status_bar = QStatusBar()
        status_bar.setSizeGripEnabled(False)
        status_bar.setStyleSheet("color: white; background: transparent;")
        
        parent.setLayout(main_layout)
        
        parent.setMinimumSize(600, 300)
        commands_section.toggle_section()
        
        return ui_components, whisper_components, status_bar

class BaseTheme:
    def __init__(self):
        self.name = "base_theme"
        self.description = "Base Theme"
    
    def get_stylesheet(self):
        return ""

class DarkMinimalTheme(BaseTheme):
    def __init__(self):
        super().__init__()
        self.name = "dark_minimal"
        self.description = "Dark Minimalist with Subtle Accents"
        
    def get_stylesheet(self):
        return """
            QWidget {
                background-color: transparent;
                color: #E0E0E0;
                font-family: 'Helvetica', sans-serif;
                font-size: 10pt;
            }
            
            QLabel {
                color: #E0E0E0;
                background-color: transparent;
            }
            
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                background-color: #2c2c2c;
                border-radius: 3px;
            }
            
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #333333, stop:1 #222222);
                border: 1px solid #444444;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 150px;
                padding: 10px 15px;
                margin-right: 2px;
                font-weight: bold;
                font-size: 12px;
                color: #a0a0a0;
            }
            
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #444444, stop:1 #333333);
                border-bottom: 3px solid #907347;
                color: #e0e0e0;
            }
            
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #3a3a3a, stop:1 #2a2a2a);
                color: #c0c0c0;
            }
            
            QLineEdit, QComboBox {
                background-color: #1c1c1c;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 5px;
                color: #E0E0E0;
            }
            
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #b08d57;
                background-color: #252525;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #3a3a3a, stop:1 #2a2a2a);
                color: #E0E0E0;
                padding: 6px 12px;
                border: 1px solid #555555;
                border-radius: 3px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #454545, stop:1 #353535);
                border: 1px solid #b08d57;
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #252525, stop:1 #353535);
                padding-top: 7px;
                padding-bottom: 5px;
            }
            
            QPushButton#clearButton {
                background-color: transparent;
                color: #B0B0B0;
                font-weight: bold;
                min-width: 20px;
                max-width: 20px;
                border: 1px solid #444444;
                border-radius: 10px;
                padding: 0px;
            }
            
            QPushButton#clearButton:hover {
                background-color: #252525;
                color: #FF4444;
                border-color: #FF4444;
            }
            
            QPushButton#clearButton:pressed {
                background-color: #333333;
                color: #FF0000;
            }
            
            QPushButton#deleteButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #3a3a3a, stop:1 #2a2a2a);
                color: #E07777;
                font-weight: bold;
                font-size: 24pt;
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
                border: 1px solid #AA4444;
                border-bottom: 3px solid #883333;
                border-radius: 20px;
                padding: 0px;
            }
            
            QPushButton#deleteButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #4a3a3a, stop:1 #3a2a2a);
                color: #FFFFFF;
                border-color: #CC4444;
                border-bottom: 3px solid #AA4444;
            }
            
            QPushButton#deleteButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #2a2a2a, stop:1 #3a3a3a);
                padding-top: 3px;
                padding-bottom: -3px;
                border-bottom: 1px solid #AA4444;
            }
            
            QPushButton#addButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #3a3a3a, stop:1 #2a2a2a);
                color: #77B877;
                font-weight: bold;
                font-size: 24pt;
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
                border: 1px solid #44AA44;
                border-bottom: 3px solid #338833;
                border-radius: 20px;
                padding: 0px;
            }
            
            QPushButton#addButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #3a4a3a, stop:1 #2a3a2a);
                color: #FFFFFF;
                border-color: #66CC66;
                border-bottom: 3px solid #44AA44;
            }
            
            QPushButton#addButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #2a2a2a, stop:1 #3a3a3a);
                padding-top: 2px;
                padding-bottom: -2px;
                border-bottom: 1px solid #44AA44;
            }
            
            /* Improved style for apply button with 3D effect */
            QPushButton#applyButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #3a3a3a, stop:1 #2a2a2a);
                color: #b08d57;
                font-weight: bold;
                font-size: 11pt;
                padding: 5px 10px;
                min-width: 100px;
                border-radius: 4px;
                border: 1px solid #907347;
                border-bottom: 3px solid #705327;
            }
            
            QPushButton#applyButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #4a4a4a, stop:1 #3a3a3a);
                color: #c09d67;
                border: 1px solid #b08d57;
                border-bottom: 3px solid #907347;
            }
            
            QPushButton#applyButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #2a2a2a, stop:1 #3a3a3a);
                padding-top: 7px;
                padding-bottom: 3px;
                border-bottom: 1px solid #907347;
            }
            
            /* Improved style for discard button with 3D effect */
            QPushButton#discardButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #3a3a3a, stop:1 #2a2a2a);
                color: #E07777;
                font-weight: bold;
                font-size: 11pt;
                padding: 5px 10px;
                min-width: 100px;
                border-radius: 4px;
                border: 1px solid #AA4444;
                border-bottom: 3px solid #883333;
            }
            
            QPushButton#discardButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #4a4a4a, stop:1 #3a3a3a);
                color: #F09999;
                border: 1px solid #CC5555;
                border-bottom: 3px solid #AA4444;
            }
            
            QPushButton#discardButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                           stop:0 #2a2a2a, stop:1 #3a3a3a);
                padding-top: 7px;
                padding-bottom: 3px;
                border-bottom: 1px solid #AA4444;
            }
            
            QLabel#logoutLabel {
                color: #b08d57;
                font-weight: bold;
                font-size: 16pt;
            }
            
            KeyCaptureWidget {
                background-color: #1c1c1c;
                color: #E0E0E0;
                border: 1px solid #3a3a3a;
                padding: 5px;
                border-radius: 4px;
            }
            
            KeyCaptureWidget:focus {
                border: 1px solid #b08d57;
                background-color: #252525;
            }
            
            QFrame#separator {
                background-color: #3a3a3a;
                min-height: 1px;
                max-height: 1px;
            }
            
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QStatusBar {
                background-color: #1c1c1c;
                color: #E0E0E0;
                border-top: 1px solid #3a3a3a;
            }
            
            #titleBar {
                border-bottom: 1px solid #3a3a3a;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                background-color: transparent;
            }
            
            #titleLabel {
                color: #b08d57;
                font-weight: bold;
                background-color: transparent;
            }
            
            #minimizeButton, #closeButton {
                background-color: transparent;
                color: #AAAAAA;
                font-weight: bold;
                border: none;
            }
            
            #minimizeButton:hover, #closeButton:hover {
                background-color: #252525;
                color: #FFFFFF;
            }
            
            #closeButton:hover {
                background-color: #FF3030;
            }
            
            #mainContainer {
                background-color: transparent;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
            }
            
            #contentContainer {
                background-color: transparent;
            }
            
            #logoutContainer {
                background-color: transparent;
                border: 1px solid #3a3a3a;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
            }
            
            #statusBarContainer {
                background-color: transparent;
                border-top: 1px solid #3a3a3a;
                border-bottom-left-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            
            /* Additional styles for the tab interface */
            #mainTabs {
                background-color: transparent;
            }
            
            /* Style for logout indicator */
            #logoutIndicator {
                background-color: transparent;
                border: none;
            }
            
            #keyBox {
                background-color: #c0392b;
                border-radius: 4px;
            }
        """

class UIBuilder:
    @staticmethod
    def create_app_icon():
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
    
    @staticmethod
    def setup_default_stylesheet():
        theme = DarkMinimalTheme()
        return theme.get_stylesheet()
    
    @staticmethod
    def create_tab_widget():
        tab_widget = QTabWidget()
        tab_widget.setObjectName("mainTabs")
        tab_widget.setDocumentMode(True)
        
        tab_bar = tab_widget.tabBar()
        tab_bar.setExpanding(False)
        
        return tab_widget

class CommandUI:
    def __init__(self, parent):
        self.parent = parent
        self.status_bar = None
        self.ui_components = {}
        self.whisper_components = {}
        
    def build_ui(self, settings, whisper_settings, clear_callback, clear_whisper_callback, add_command_callback, add_whisper_callback, delete_command_callback, delete_whisper_callback, discard_callback, apply_callback, hide_callback):
        container = QWidget(self.parent)
        
        container.setStyleSheet(UIBuilder.setup_default_stylesheet())
        
        layout = TabLayout()
        ui_components, whisper_components, status_bar = layout.build_ui(
            container, 
            settings, 
            whisper_settings, 
            {
                "clear_callback": clear_callback,
                "clear_whisper_callback": clear_whisper_callback,
                "add_command_callback": add_command_callback,
                "add_whisper_callback": add_whisper_callback,
                "delete_command_callback": delete_command_callback,
                "delete_whisper_callback": delete_whisper_callback,
                "discard_callback": discard_callback,
                "apply_callback": apply_callback,
                "hide": hide_callback
            }
        )
        
        self.ui_components = ui_components
        self.whisper_components = whisper_components
        self.status_bar = status_bar
        
        return container

def safe_update_geometry(widget):
    """Safely update geometry of a widget if it exists and is valid"""
    try:
        if widget and not widget.isDestroyed():
            widget.updateGeometry()
    except (RuntimeError, Exception) as e:
        print(f"Error updating geometry: {e}")
        pass

def create_safe_discard_callback(original_callback):
    """Create a wrapper around discard callback that handles potential UI issues safely"""
    def safe_discard_wrapper(*args, **kwargs):
        try:
            if hasattr(original_callback, '__self__'):
                result = original_callback()
            else:
                result = original_callback(*args, **kwargs)
            return result
        except RuntimeError as e:
            if "has been deleted" in str(e):
                print(f"Warning: Attempted to access deleted widget: {e}")
                pass
            else:
                raise
    return safe_discard_wrapper

class TabLayout(BaseLayout):
    def __init__(self):
        super().__init__()
        self.name = "tab_layout"
        self.description = "Tab-based Layout with Game Commands and Whisper Tabs"
        
    def build_ui(self, parent, settings, whisper_settings, callbacks):
        if parent.layout() is not None:
            while parent.layout().count():
                item = parent.layout().takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            
            parent.layout().deleteLater()
        
        parent.setAttribute(Qt.WA_TranslucentBackground)
        parent.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        main_layout = QVBoxLayout(parent)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        main_widget = QWidget()
        main_widget.setObjectName("mainWidget")
        main_widget.setStyleSheet("""
            #mainWidget {
                background-color: #1c1c1c;
                border-radius: 5px;
                border: 1px solid #3a3a3a;
            }
        """)
        
        widget_layout = QVBoxLayout(main_widget)
        widget_layout.setContentsMargins(10, 10, 10, 10)
        widget_layout.setSpacing(10)
        
        logout_settings = settings.get('logout', {
            'label': 'Logout:',
            'text': 'logout',
            'hotkey': 'f9',
            'is_editable': True
        })
        logout_indicator = LogoutIndicator(logout_settings)
        
        tab_widget = QTabWidget()
        tab_widget.setObjectName("mainTabs")
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3a3a3a;
                background-color: #2c2c2c;
                border-radius: 3px;
            }
            
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #333333, stop:1 #222222);
                border: 1px solid #444444;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                min-width: 150px;
                padding: 10px 15px;
                margin-right: 2px;
                font-weight: bold;
                font-size: 12px;
                color: #a0a0a0;
            }
            
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #444444, stop:1 #333333);
                border-bottom: 3px solid #907347;
                color: #e0e0e0;
            }
            
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #3a3a3a, stop:1 #2a2a2a);
                color: #c0c0c0;
            }
        """)
        
        game_content = QWidget()
        game_layout = QVBoxLayout(game_content)
        game_layout.setContentsMargins(10, 10, 10, 10)
        game_layout.setSpacing(8)
        
        game_scroll = QScrollArea()
        game_scroll.setWidgetResizable(True)
        game_scroll.setFrameShape(QFrame.NoFrame)
        game_scroll.setWidget(game_content)
        game_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        game_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        whisper_content = QWidget()
        whisper_layout = QVBoxLayout(whisper_content)
        whisper_layout.setContentsMargins(10, 10, 10, 10)
        whisper_layout.setSpacing(8)
        
        whisper_scroll = QScrollArea()
        whisper_scroll.setWidgetResizable(True)
        whisper_scroll.setFrameShape(QFrame.NoFrame)
        whisper_scroll.setWidget(whisper_content)
        whisper_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        whisper_scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        tab_widget.addTab(game_scroll, "GAME COMMANDS")
        tab_widget.addTab(whisper_scroll, "WHISPER COMMANDS")
        
        footer = QWidget()
        footer.setObjectName("footer")
        footer.setFixedHeight(60)
        footer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        footer.setStyleSheet("""
            #footer {
                background-color: #1c1c1c;
                border-top: 1px solid #3a3a3a;
            }
        """)
        
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        footer_layout.addStretch(1)
        
        discard_button = QPushButton("Discard")
        discard_button.setObjectName("discardButton")
        discard_button.setFixedSize(100, 30)
        
        original_discard_callback = callbacks.get("discard_callback", lambda: None)
        safe_discard_callback = create_safe_discard_callback(original_discard_callback)
        discard_button.clicked.connect(safe_discard_callback)
        
        apply_button = QPushButton("Apply")
        apply_button.setObjectName("applyButton")
        apply_button.setFixedSize(100, 30)
        apply_button.clicked.connect(callbacks.get("apply_callback", lambda: None))
        
        footer_layout.addWidget(discard_button)
        footer_layout.addSpacing(10)
        footer_layout.addWidget(apply_button)
        
        widget_layout.addWidget(logout_indicator)
        widget_layout.addWidget(tab_widget, 1)
        
        main_layout.addWidget(main_widget, 1)
        main_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(footer)
        
        parent.layout().setSizeConstraint(QLayout.SetMinimumSize)

        parent.setMinimumHeight(400)
        
        ui_components = {}
        whisper_components = {}
        
        def sort_command_keys(cmd_id):
            if cmd_id == 'logout':
                return -1
            try:
                if cmd_id.startswith('command'):
                    return int(cmd_id.replace('command', ''))
                elif cmd_id.startswith('whisper'):
                    return int(cmd_id.replace('whisper', ''))
                return 0
            except ValueError:
                return 0
        
        for key in sorted([k for k in settings.keys() if k != 'logout'], key=sort_command_keys):
            command = settings[key]
            row_layout, components = CommandRowCreator.create_command_row(
                key,
                command,
                callbacks.get("clear_callback", lambda x: None)
            )
            
            row_container = QWidget()
            row_container.setObjectName(f"command_container_{key}")
            row_container.setStyleSheet("background-color: #3d3d3d; border-radius: 4px;")
            container_layout = QVBoxLayout(row_container)
            container_layout.setContentsMargins(5, 5, 5, 5)
            container_layout.addLayout(row_layout)
            
            game_layout.addWidget(row_container)
            ui_components[key] = components
        
        if 'logout' in settings:
            row_layout, components = CommandRowCreator.create_command_row(
                'logout', 
                settings['logout'], 
                callbacks.get("clear_callback", lambda x: None)
            )
            ui_components['logout'] = components
            
        game_add_container = QWidget()
        game_add_layout = QHBoxLayout(game_add_container)
        game_add_layout.setContentsMargins(5, 5, 5, 5)
        
        game_add_layout.addStretch()
        add_command_button = QPushButton("+")
        add_command_button.setObjectName("addButton")
        add_command_button.setToolTip("Add new command")
        add_command_button.setFixedSize(40, 40)
        add_command_button.setStyleSheet("""
            QPushButton#addButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #454545, stop:1 #353535);
                color: #CCCCCC; 
                font-weight: bold;
                font-size: 18pt;
                border: 1px solid #555555;
                border-bottom: 3px solid #444444;
                border-radius: 4px;
            }
            QPushButton#addButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #505050, stop:1 #404040);
                color: #FFFFFF;
                border-color: #666666;
            }
            QPushButton#addButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #353535, stop:1 #454545);
                padding-top: 2px;
                color: #FFFFFF;
                border-bottom: 1px solid #444444;
            }
        """)
        add_command_button.clicked.connect(callbacks.get("add_command_callback", lambda: None))
        
        remove_command_button = QPushButton("-")
        remove_command_button.setObjectName("deleteButton")
        remove_command_button.setToolTip("Remove last command")
        remove_command_button.setFixedSize(40, 40)
        remove_command_button.setStyleSheet("""
            QPushButton#deleteButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #454545, stop:1 #353535);
                color: #CCCCCC;
                font-weight: bold;
                font-size: 18pt;
                border: 1px solid #555555;
                border-bottom: 3px solid #444444;
                border-radius: 4px;
            }
            QPushButton#deleteButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #505050, stop:1 #404040);
                color: #FFFFFF;
                border-color: #666666;
            }
            QPushButton#deleteButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #353535, stop:1 #454545);
                padding-top: 2px;
                color: #FFFFFF;
                border-bottom: 1px solid #444444;
            }
        """)
        remove_command_button.clicked.connect(callbacks.get("delete_command_callback", lambda: None))
        
        game_add_layout.addWidget(add_command_button)
        game_add_layout.addSpacing(10)
        game_add_layout.addWidget(remove_command_button)
        game_add_layout.addStretch()
        
        game_layout.addWidget(game_add_container)
        game_layout.addStretch()
        
        for key in sorted(whisper_settings.keys(), key=sort_command_keys):
            whisper = whisper_settings[key]
            row_layout, components = CommandRowCreator.create_whisper_row(
                key, 
                whisper, 
                callbacks.get("clear_whisper_callback", lambda x: None)
            )
            
            row_container = QWidget()
            row_container.setObjectName(f"whisper_container_{key}")
            row_container.setStyleSheet("background-color: #3d3d3d; border-radius: 4px;")
            container_layout = QVBoxLayout(row_container)
            container_layout.setContentsMargins(5, 5, 5, 5)
            container_layout.addLayout(row_layout)
            
            whisper_layout.addWidget(row_container)
            whisper_components[key] = components
            
        whisper_add_container = QWidget()
        whisper_add_layout = QHBoxLayout(whisper_add_container)
        whisper_add_layout.setContentsMargins(5, 5, 5, 5)
        
        whisper_add_layout.addStretch()
        add_whisper_button = QPushButton("+")
        add_whisper_button.setObjectName("addButton")
        add_whisper_button.setToolTip("Add new whisper")
        add_whisper_button.setFixedSize(40, 40)
        add_whisper_button.setStyleSheet("""
            QPushButton#addButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #454545, stop:1 #353535);
                color: #CCCCCC; 
                font-weight: bold;
                font-size: 18pt;
                border: 1px solid #555555;
                border-bottom: 3px solid #444444;
                border-radius: 4px;
            }
            QPushButton#addButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #505050, stop:1 #404040);
                color: #FFFFFF;
                border-color: #666666;
            }
            QPushButton#addButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #353535, stop:1 #454545);
                padding-top: 2px;
                color: #FFFFFF;
                border-bottom: 1px solid #444444;
            }
        """)
        add_whisper_button.clicked.connect(callbacks.get("add_whisper_callback", lambda: None))
        
        remove_whisper_button = QPushButton("-")
        remove_whisper_button.setObjectName("deleteButton")
        remove_whisper_button.setToolTip("Remove last whisper")
        remove_whisper_button.setFixedSize(40, 40)
        remove_whisper_button.setStyleSheet("""
            QPushButton#deleteButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #454545, stop:1 #353535);
                color: #CCCCCC;
                font-weight: bold;
                font-size: 18pt;
                border: 1px solid #555555;
                border-bottom: 3px solid #444444;
                border-radius: 4px;
            }
            QPushButton#deleteButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #505050, stop:1 #404040);
                color: #FFFFFF;
                border-color: #666666;
            }
            QPushButton#deleteButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #353535, stop:1 #454545);
                padding-top: 2px;
                color: #FFFFFF;
                border-bottom: 1px solid #444444;
            }
        """)
        remove_whisper_button.clicked.connect(callbacks.get("delete_whisper_callback", lambda: None))
        
        whisper_add_layout.addWidget(add_whisper_button)
        whisper_add_layout.addSpacing(10)
        whisper_add_layout.addWidget(remove_whisper_button)
        whisper_add_layout.addStretch()
        
        whisper_layout.addWidget(whisper_add_container)
        whisper_layout.addStretch()
        
        status_bar = QStatusBar()
        status_bar.setSizeGripEnabled(False)
        status_bar.setFixedHeight(30)
        status_bar.setStyleSheet("color: white; background: #2c2c2c; border-top: 1px solid #3a3a3a;")
        
        parent.setMinimumSize(650, 530)
        
        parent.findChild = lambda x, name=None: {
            QTabWidget: tab_widget,
            "game_layout": game_layout,
            "whisper_layout": whisper_layout,
            "footer": footer
        }.get(x if name is None else name)
        
        return ui_components, whisper_components, status_bar