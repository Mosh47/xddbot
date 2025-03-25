from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                           QStatusBar, QScrollArea, QFrame, QTabWidget, QSizePolicy, QLayout)
from PyQt5.QtCore import Qt
from ui.command_row import CommandRowCreator
from ui.custom_components import LogoutIndicator

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

class TabLayout:
    def __init__(self):
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