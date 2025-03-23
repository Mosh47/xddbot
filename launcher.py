import sys
import os
import subprocess
from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt

class NpcapRequiredDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XDDBot - Npcap Required")
        self.setFixedSize(450, 250)
        
        main_layout = QVBoxLayout()
        
        message_layout = QVBoxLayout()
        
        message_label = QLabel(
            "XDDBot requires Npcap to be installed to function properly.\n\n"
            "Npcap is a packet capture library that allows the app to detect\n"
            "and terminate network connections for the logout function.\n\n"
            "Click the button below to download and install Npcap, then restart\n"
            "XDDBot after installation is complete."
        )
        message_label.setAlignment(Qt.AlignCenter)
        message_layout.addWidget(message_label)
        
        main_layout.addLayout(message_layout)
        
        button_layout = QHBoxLayout()
        
        download_button = QPushButton("Download & Install Npcap")
        download_button.clicked.connect(self.download_npcap)
        download_button.setFixedHeight(40)
        button_layout.addWidget(download_button)
        
        exit_button = QPushButton("Exit")
        exit_button.clicked.connect(self.close)
        exit_button.setFixedHeight(40)
        button_layout.addWidget(exit_button)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def download_npcap(self):
        subprocess.Popen(["cmd", "/c", "start", "https://npcap.com/#download"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    if os.path.exists("C:\\Windows\\System32\\Npcap") or os.path.exists("C:\\Program Files\\Npcap"):
        subprocess.Popen([sys.executable, "poe_commands.py"])
        sys.exit(0)
    
    dialog = NpcapRequiredDialog()
    dialog.exec_()
    sys.exit(0) 