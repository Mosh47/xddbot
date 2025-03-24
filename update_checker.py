import os
import json
import requests
import re
import threading
import time
import shutil
import subprocess
import sys
import zipfile
from packaging import version
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

REPO_OWNER = "Mosh47"
REPO_NAME = "xddbot"
APP_DATA_DIR = os.path.join(os.path.expanduser('~'), '.xddbot')
VERSION_FILE = os.path.join(APP_DATA_DIR, "version.json")
DEFAULT_VERSION = "0.0.0"
SETTINGS_FILE = os.path.join(APP_DATA_DIR, "poe_settings.json")

def ensure_app_data_dir():
    if not os.path.exists(APP_DATA_DIR):
        os.makedirs(APP_DATA_DIR, exist_ok=True)

def get_current_version():
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r') as f:
                data = json.load(f)
                return data.get("version", DEFAULT_VERSION)
        except:
            pass
    return DEFAULT_VERSION

def save_current_version(version_str):
    ensure_app_data_dir()
    data = {"version": version_str, "skipped_versions": []}
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r') as f:
                existing_data = json.load(f)
                if "skipped_versions" in existing_data:
                    data["skipped_versions"] = existing_data["skipped_versions"]
        except:
            pass
            
    with open(VERSION_FILE, 'w') as f:
        json.dump(data, f)

def add_skipped_version(version_str):
    ensure_app_data_dir()
    data = {"version": get_current_version(), "skipped_versions": [version_str]}
    
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r') as f:
                existing_data = json.load(f)
                data["version"] = existing_data.get("version", DEFAULT_VERSION)
                skipped = existing_data.get("skipped_versions", [])
                if version_str not in skipped:
                    skipped.append(version_str)
                data["skipped_versions"] = skipped
        except:
            pass
    
    with open(VERSION_FILE, 'w') as f:
        json.dump(data, f)

def is_version_skipped(version_str):
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r') as f:
                data = json.load(f)
                skipped_versions = data.get("skipped_versions", [])
                return version_str in skipped_versions
        except:
            pass
    return False

def get_latest_release():
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        print(f"Requesting releases from {url}")
        
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Response status code: {response.status_code}")
        
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except Exception as e:
        print(f"Error in get_latest_release: {e}")
        return None

def extract_version_from_tag(tag_name):
    if not tag_name:
        return None
    
    match = re.search(r'v?(\d+\.\d+\.\d+)', tag_name)
    if match:
        return match.group(1)
    
    return tag_name

def check_for_updates():
    try:
        latest_release = get_latest_release()
        if not latest_release:
            print("No latest release found")
            return None, None
            
        latest_tag = latest_release.get('tag_name')
        latest_version = extract_version_from_tag(latest_tag)
        
        if not latest_version:
            print(f"Could not extract version from tag: {latest_tag}")
            return None, None
        
        current_version = get_current_version()
        print(f"Current version: {current_version}, Latest version: {latest_version}")
        
        if is_version_skipped(latest_version):
            print(f"Version {latest_version} has been skipped")
            return None, None
            
        try:
            if version.parse(latest_version) > version.parse(current_version):
                print("New version available")
                assets = latest_release.get('assets', [])
                print(f"Found {len(assets)} assets in release")
                
                for asset in assets:
                    asset_name = asset.get('name', '')
                    print(f"Checking asset: {asset_name}")
                    if asset_name.lower().endswith('.zip'):
                        return latest_version, asset.get('browser_download_url')
                
                print("No suitable zip asset found in release")
                return latest_version, None
            else:
                print("No newer version available")
        except Exception as e:
            print(f"Error comparing versions: {e}")
                
        return None, None
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return None, None

def download_file(url, dest_path, progress_callback=None):
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        progress_callback(int(100 * downloaded / total_size))
        
        return True
    except:
        return False

def extract_zip(zip_path, extract_dir):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        return True
    except:
        return False

def find_exe_in_dir(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.exe'):
                return os.path.join(root, file)
    return None

def create_update_script(current_exe, new_exe, extract_dir, zip_path):
    ensure_app_data_dir()
    batch_path = os.path.join(APP_DATA_DIR, "update.bat")
    
    with open(batch_path, 'w') as f:
        f.write(f'''@echo off
echo Updating xddbot...

:: Kill all running instances
echo Closing application...
taskkill /F /IM xddbot.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul

:: Update version file FIRST to prevent update loop
echo Updating version information...
echo {{{{"version": "999.999.999", "skipped_versions": []}}}} > "{VERSION_FILE}"

:: Forcibly delete and replace EXE
echo Replacing executable...
del /F "{current_exe}" >nul 2>&1
copy /Y "{new_exe}" "{current_exe}" >nul 2>&1

:: Check if copy succeeded
if exist "{current_exe}" (
    echo Starting updated application...
    start "" "{current_exe}"
) else (
    echo Copy failed! Starting from extract location instead...
    start "" "{new_exe}"
)

:: Clean up files
echo Cleaning up...
timeout /t 2 /nobreak >nul
if exist "{zip_path}" del /F "{zip_path}" >nul 2>&1

:: Self-delete this batch file
(goto) 2>nul & del "%~f0"
''')
    
    subprocess.Popen(
        ["cmd.exe", "/c", batch_path],
        shell=True,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    
    return True

class UpdateDialog(QDialog):
    def __init__(self, latest_version, download_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setFixedWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.download_url = download_url
        self.latest_version = latest_version
        self.result_code = 0
        
        layout = QVBoxLayout(self)
        
        message = QLabel(
            f"<h3>A new version is available</h3>"
            f"<p>Your version: {get_current_version()}</p>"
            f"<p>Latest version: {latest_version}</p>"
            f"<p>Would you like to install the update?</p>"
        )
        message.setTextFormat(Qt.RichText)
        message.setWordWrap(True)
        layout.addWidget(message)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        button_layout = QVBoxLayout()
        
        self.install_btn = QPushButton("Install Update")
        self.install_btn.setMinimumHeight(40)
        self.install_btn.clicked.connect(self.download_update)
        button_layout.addWidget(self.install_btn)
        
        self.skip_btn = QPushButton("Skip This Time")
        self.skip_btn.clicked.connect(self.skip_update)
        button_layout.addWidget(self.skip_btn)
        
        self.skip_always_btn = QPushButton("Skip and Don't Ask Again")
        self.skip_always_btn.clicked.connect(self.skip_always)
        button_layout.addWidget(self.skip_always_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        QApplication.processEvents()
        
    def set_status(self, message):
        self.status_label.setText(message)
        self.status_label.setVisible(True)
        QApplication.processEvents()
    
    def download_update(self):
        self.install_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.skip_always_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        try:
            self.set_status("Downloading update...")
            
            ensure_app_data_dir()
            app_dir = APP_DATA_DIR
            zip_path = os.path.join(app_dir, "xddbot_update.zip")
            extract_dir = os.path.join(app_dir, "update_extract")
            
            if os.path.exists(extract_dir):
                shutil.rmtree(extract_dir, ignore_errors=True)
            os.makedirs(extract_dir, exist_ok=True)
            
            if not download_file(self.download_url, zip_path, self.update_progress):
                self.set_status("Failed to download update")
                self.restore_buttons()
                return
                
            self.set_status("Extracting update...")
            if not extract_zip(zip_path, extract_dir):
                self.set_status("Failed to extract update")
                self.restore_buttons()
                return
            
            self.set_status("Locating new executable...")
            new_exe = find_exe_in_dir(extract_dir)
            if not new_exe:
                self.set_status("No executable found in update package")
                self.restore_buttons()
                return
            
            self.set_status("Starting update...")
            current_exe = sys.executable
            update_script = create_update_script(current_exe, new_exe, extract_dir, zip_path)
            
            subprocess.Popen(
                [sys.executable, update_script],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            self.result_code = 1
            self.accept()
            sys.exit(0)
            
        except Exception as e:
            self.set_status(f"Error: {str(e)}")
            self.restore_buttons()
    
    def restore_buttons(self):
        self.install_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.skip_always_btn.setEnabled(True)
    
    def skip_update(self):
        self.result_code = 2
        self.reject()
    
    def skip_always(self):
        add_skipped_version(self.latest_version)
        self.result_code = 2
        self.reject()

def check_for_update_at_startup():
    """
    Checks for updates at application startup.
    Returns:
        0 if no update is available
        1 if updated and should exit
        2 if update was skipped
    """
    latest_version, download_url = check_for_updates()
    
    if (latest_version and download_url):
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        dialog = UpdateDialog(latest_version, download_url)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            return 1  # Update installed
        else:
            return 2  # Update skipped
    
    return 0  # No update available

def reset_version_info():
    ensure_app_data_dir()
    if os.path.exists(VERSION_FILE):
        os.remove(VERSION_FILE)
    save_current_version("0.0.0")
    return True

def force_update_check():
    """Force check for updates by resetting version info first"""
    print("Forcing update check...")
    reset_version_info()  # Reset to version 0.0.0
    return check_for_update_at_startup()

# Keep only this at the end of update_checker.py 
ensure_app_data_dir()
if not os.path.exists(VERSION_FILE):
    save_current_version(DEFAULT_VERSION)