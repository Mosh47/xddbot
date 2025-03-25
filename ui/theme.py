class DarkMinimalTheme:
    def __init__(self):
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
            
            #mainTabs {
                background-color: transparent;
            }
            
            #logoutIndicator {
                background-color: transparent;
                border: none;
            }
            
            #keyBox {
                background-color: #c0392b;
                border-radius: 4px;
            }
        """ 