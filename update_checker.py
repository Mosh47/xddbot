import os
import json
import requests
import re
from packaging import version
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices

# GitHub repository information
REPO_OWNER = "Mosh47"
REPO_NAME = "xddbot"

# Current version - modify this when releasing updates
CURRENT_VERSION = "0.0.1"

def get_latest_release():
    """Fetch the latest release information from GitHub"""
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching latest release: {e}")
        return None

def extract_version_from_tag(tag_name):
    """Extract version number from a tag like 'v1.0.0' or similar"""
    if not tag_name:
        return None
    
    # Try to extract version using regex
    match = re.search(r'v?(\d+\.\d+\.\d+)', tag_name)
    if match:
        return match.group(1)
    
    return tag_name  # Return as is if regex doesn't match

def check_for_updates():
    """Check if updates are available, returns (latest_version, download_url) or (None, None)"""
    try:
        latest_release = get_latest_release()
        if not latest_release:
            return None, None
            
        latest_tag = latest_release.get('tag_name')
        latest_version = extract_version_from_tag(latest_tag)
        
        if not latest_version:
            return None, None
            
        # Check if the latest version is newer than current version
        if version.parse(latest_version) > version.parse(CURRENT_VERSION):
            # Construct direct download URL to the zip file in the repository
            # This uses the raw.githubusercontent.com URL format for the main branch
            download_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/raw/main/dist/xddbot.zip"
            
            # Alternative: if you're using versioned zips with different names per version
            # You can use tag-based URL: (uncomment if needed)
            # download_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/raw/{latest_tag}/dist/xddbot.zip"
            
            return latest_version, download_url
                
        return None, None  # No update needed
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return None, None

class UpdateAvailableDialog(QDialog):
    def __init__(self, latest_version, download_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setFixedWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.download_url = download_url
        
        layout = QVBoxLayout(self)
        
        # Update message
        message = QLabel(
            f"<h3>A new version is available!</h3>"
            f"<p>Your version: {CURRENT_VERSION}</p>"
            f"<p>Latest version: {latest_version}</p>"
            f"<p>Would you like to download the update?</p>"
            f"<p><small>Note: The download will be a ZIP file. Extract the executable after downloading.</small></p>"
        )
        message.setTextFormat(Qt.RichText)
        message.setWordWrap(True)
        layout.addWidget(message)
        
        # Button layout
        button_layout = QVBoxLayout()
        
        # Download button
        download_btn = QPushButton("Download Update")
        download_btn.setMinimumHeight(40)
        download_btn.clicked.connect(self.download_update)
        button_layout.addWidget(download_btn)
        
        # Skip button
        skip_btn = QPushButton("Skip This Update")
        skip_btn.clicked.connect(self.reject)
        button_layout.addWidget(skip_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def download_update(self):
        if self.download_url:
            QDesktopServices.openUrl(QUrl(self.download_url))
        self.accept()

def show_update_dialog(parent=None):
    """Check for updates and show dialog if available"""
    latest_version, download_url = check_for_updates()
    
    if latest_version and download_url:
        dialog = UpdateAvailableDialog(latest_version, download_url, parent)
        return dialog.exec_()
    
    return False 