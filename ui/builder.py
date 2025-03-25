from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush, QPen, QFont
from PyQt5.QtCore import Qt

from ui.theme import DarkMinimalTheme

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