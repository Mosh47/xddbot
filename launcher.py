import os
import sys
import npcap_detector
from PyQt5.QtWidgets import QApplication, QMessageBox, QVBoxLayout, QLabel, QPushButton, QDialog
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices

def launch_main_app():
    try:
        import main
        main.main()
    except Exception as e:
        print(f"Error launching main app: {e}")
        QMessageBox.critical(None, "Error", f"Failed to start the application: {e}")

class NpcapRequiredDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Npcap Required")
        self.setFixedWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        
        message = QLabel(
            "<h3>Npcap is required to run this application</h3>"
            "<p>PoE Tools needs Npcap to enable the logout functionality.</p>"
            "<p>Please download and install Npcap with default settings:</p>"
            "<ol>"
            "<li>Click the download button below</li>"
            "<li>Run the downloaded installer</li>"
            "<li>Click 'Next' at each step (accept the DEFAULT options)</li>"
            "<li>Click 'Finish' to complete installation</li>"
            "<li>Restart Logout Bot AFTER installation is complete</li>"
            "</ol>"
        )
        message.setTextFormat(Qt.RichText)
        message.setWordWrap(True)
        layout.addWidget(message)
        
        download_btn = QPushButton("Download Npcap")
        download_btn.setMinimumHeight(40)
        download_btn.clicked.connect(self.download_npcap)
        layout.addWidget(download_btn)
        
        exit_btn = QPushButton("Exit")
        exit_btn.clicked.connect(self.reject)
        layout.addWidget(exit_btn)
        
        self.setLayout(layout)
    
    def download_npcap(self):
        QDesktopServices.openUrl(QUrl("https://npcap.com/dist/npcap-1.81.exe"))

def main():
    app = QApplication(sys.argv)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--main":
        import main as main_module
        return main_module.main()
    
    if npcap_detector.is_npcap_installed():
        launch_main_app()
        return
    
    dialog = NpcapRequiredDialog()
    dialog.exec_()      
    sys.exit(0)

if __name__ == "__main__":
    main() 