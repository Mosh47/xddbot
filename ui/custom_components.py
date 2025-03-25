from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor

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
        """)
        
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setOffset(1, 1)
        shadow_effect.setBlurRadius(2)
        shadow_effect.setColor(QColor(0, 0, 0, 204))
        self.logout_text.setGraphicsEffect(shadow_effect)
        
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
        """)
        
        key_shadow_effect = QGraphicsDropShadowEffect()
        key_shadow_effect.setOffset(1, 1)
        key_shadow_effect.setBlurRadius(2)
        key_shadow_effect.setColor(QColor(0, 0, 0, 127))
        self.key_label.setGraphicsEffect(key_shadow_effect)
        
        key_layout.addWidget(self.key_label)
        
        left_layout.addWidget(self.logout_text)
        left_layout.addWidget(self.key_box)
        left_layout.addStretch(1)
        
        self.layout.addLayout(left_layout, 3) 