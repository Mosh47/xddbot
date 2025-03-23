import os, json, requests, re, tempfile, zipfile, subprocess, sys, time, threading
import platform, shutil, hashlib, struct
from packaging import version
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QApplication
from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

REPO_OWNER = "Mosh47"
REPO_NAME = "xddbot"
CURRENT_VERSION = "0.0.1"
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".xddbot")
UPDATES_DIR = os.path.join(APP_DATA_DIR, "updates")
BACKUP_DIR = os.path.join(APP_DATA_DIR, "backup")
SETTINGS_FILE = os.path.join(APP_DATA_DIR, "update_settings.json")
VERSION_FILE = os.path.join(APP_DATA_DIR, "installed_version.txt")

class DownloadThread(QThread):
    progress_signal = pyqtSignal(int)
    complete_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, download_url, version):
        super().__init__()
        self.download_url = download_url
        self.version = version
        os.makedirs(UPDATES_DIR, exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        self.download_path = os.path.join(UPDATES_DIR, f"update_{version}.zip")
        self.extract_path = os.path.join(UPDATES_DIR, version)
        os.makedirs(self.extract_path, exist_ok=True)
    
    def run(self):
        try:
            response = requests.get(self.download_url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            self.progress_signal.emit(int((downloaded / total_size) * 100))
            
            for item in os.listdir(self.extract_path):
                item_path = os.path.join(self.extract_path, item)
                if os.path.isfile(item_path): os.unlink(item_path)
                elif os.path.isdir(item_path): shutil.rmtree(item_path)
                    
            with zipfile.ZipFile(self.download_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_path)
            
            self.progress_signal.emit(100)
            self.complete_signal.emit(self.extract_path)
        except Exception as e:
            self.error_signal.emit(f"Error during download: {str(e)}")

class UpdateDialog(QDialog):
    def __init__(self, latest_version, download_url, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setFixedSize(450, 350)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        self.download_url = download_url
        self.latest_version = latest_version
        self.setModal(True)
        self.is_downloading = False
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_layout = QHBoxLayout()
        title = QLabel(f"<h2>Update Available</h2>")
        title.setTextFormat(Qt.RichText)
        title_layout.addWidget(title)
        layout.addLayout(title_layout)
        
        current_version = get_installed_version()
        version_info = QLabel(f"<b>Current version:</b> {current_version}<br><b>New version:</b> {latest_version}")
        version_info.setTextFormat(Qt.RichText)
        layout.addWidget(version_info)
        
        self.status_label = QLabel("A new version is available with improvements and bug fixes.")
        self.status_label.setAlignment(Qt.AlignLeft)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        info = QLabel("<p><i>The application will close during update and restart automatically.</i></p>")
        info.setTextFormat(Qt.RichText)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        self.auto_update_check = QCheckBox("Automatically download updates in the future")
        layout.addWidget(self.auto_update_check)
        
        self.never_show_check = QCheckBox("Skip this version")
        layout.addWidget(self.never_show_check)
        
        settings = load_update_settings()
        self.auto_update_check.setChecked(settings.get("auto_download", False))
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.remind_btn = QPushButton("Remind Me Later")
        self.remind_btn.setMinimumHeight(40)
        self.remind_btn.clicked.connect(self._on_remind_clicked)
        btn_layout.addWidget(self.remind_btn)
        
        self.skip_btn = QPushButton("Skip This Update")
        self.skip_btn.setMinimumHeight(40)
        self.skip_btn.clicked.connect(self._on_skip_clicked)
        btn_layout.addWidget(self.skip_btn)
        
        self.install_btn = QPushButton("Install Now")
        self.install_btn.setMinimumHeight(40)
        self.install_btn.setDefault(True)
        self.install_btn.clicked.connect(self._on_install_clicked)
        btn_layout.addWidget(self.install_btn)
        
        layout.addLayout(btn_layout)
    
    def _on_remind_clicked(self):
        save_update_settings({"auto_download": self.auto_update_check.isChecked()})
        self.reject()
    
    def _on_install_clicked(self):
        save_update_settings({"auto_download": self.auto_update_check.isChecked(), "skip_version": ""})
        self.start_update()
        
    def _on_skip_clicked(self):
        if self.is_downloading and hasattr(self, 'downloader') and self.downloader is not None:
            self.downloader.terminate()
            self.downloader.wait()
        
        save_update_settings({"auto_download": self.auto_update_check.isChecked()})
        if self.never_show_check.isChecked():
            save_update_settings({"skip_version": self.latest_version})
        self.reject()
        
    def start_update(self):
        if self.is_downloading: return
        
        self.is_downloading = True
        self.status_label.setText("Downloading update...")
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        self.install_btn.setEnabled(False)
        self.skip_btn.setText("Cancel")
        self.remind_btn.setEnabled(False)
        self.never_show_check.setEnabled(False)
        self.auto_update_check.setEnabled(False)
        
        parent = self.parent()
        if parent and hasattr(parent, 'saveAllData'):
            try: parent.saveAllData()
            except: pass
        
        self.downloader = DownloadThread(self.download_url, self.latest_version)
        self.downloader.progress_signal.connect(self.progress_bar.setValue)
        self.downloader.complete_signal.connect(self.download_complete)
        self.downloader.error_signal.connect(self.download_error)
        self.downloader.start()
    
    def download_complete(self, extracted_path):
        try:
            self.status_label.setText("Installing update...")
            QApplication.processEvents()
            time.sleep(0.5)
            install_update(extracted_path, self.latest_version, self)
        except Exception as e:
            self.status_label.setText(f"Error during installation: {str(e)}")
            self.skip_btn.setEnabled(True)
            self.remind_btn.setEnabled(True)
            self.install_btn.setEnabled(True)
            self.skip_btn.setText("Close")
            self.is_downloading = False
            self.never_show_check.setEnabled(True)
            self.auto_update_check.setEnabled(True)
    
    def download_error(self, error_message):
        self.status_label.setText(f"Error: {error_message}")
        self.skip_btn.setEnabled(True)
        self.remind_btn.setEnabled(True)
        self.install_btn.setEnabled(True)
        self.skip_btn.setText("Close")
        self.is_downloading = False
        self.never_show_check.setEnabled(True)
        self.auto_update_check.setEnabled(True)
        
    def closeEvent(self, event):
        if self.is_downloading:
            event.ignore()
        else:
            save_update_settings({
                "auto_download": self.auto_update_check.isChecked(),
                "skip_version": self.latest_version if self.never_show_check.isChecked() else ""
            })
            event.accept()

def save_update_settings(settings):
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    try:
        existing = {}
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                try: existing = json.load(f)
                except: pass
        
        existing.update(settings)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(existing, f)
        log_error(f"Saved settings: {existing}")
    except Exception as e:
        log_error(f"Error saving settings: {str(e)}")

def load_update_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                data = json.load(f)
                log_error(f"Loaded settings: {data}")
                return data
    except Exception as e:
        log_error(f"Error loading settings: {str(e)}")
    return {}

def get_latest_release():
    try:
        url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest"
        headers = {'Accept': 'application/vnd.github.v3+json'}
        response = requests.get(url, timeout=10, headers=headers)
        
        if response.status_code == 404:
            all_releases_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases"
            response = requests.get(all_releases_url, timeout=10, headers=headers)
            
            if response.status_code == 200:
                releases = response.json()
                if releases: return releases[0]
                return None
        elif response.status_code == 200:
            return response.json()
        
        response.raise_for_status()
    except Exception as e:
        log_error(f"Failed to get release info: {str(e)}")
    
    return None

def get_executable_version():
    try:
        if platform.system() == 'Windows' and sys.executable.lower().endswith('.exe'):
            try:
                import win32api
                info = win32api.GetFileVersionInfo(sys.executable, '\\')
                ms = info['FileVersionMS']
                ls = info['FileVersionLS']
                executable_version = "%d.%d.%d" % (win32api.HIWORD(ms), win32api.LOWORD(ms), win32api.HIWORD(ls))
                
                if re.match(r'^\d+\.\d+\.\d+$', executable_version):
                    log_error(f"Got version {executable_version} from executable metadata")
                    return executable_version
            except: pass

        with open(sys.executable, 'rb') as f:
            content = f.read()
            matches = re.findall(b'CURRENT_VERSION\\s*=\\s*["\']([0-9]+\\.[0-9]+\\.[0-9]+)["\']', content)
            if matches:
                version_str = matches[0].decode('utf-8')
                log_error(f"Found version {version_str} in executable binary")
                return version_str
    except Exception as e:
        log_error(f"Error getting executable version: {str(e)}")
    
    return CURRENT_VERSION

def get_installed_version():
    try:
        actual_version = get_executable_version()
        stored_version = None
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                stored_version = f.read().strip()
                
        if stored_version:
            if version.parse(stored_version) > version.parse(actual_version):
                log_error(f"WARNING: Stored version {stored_version} is newer than actual version {actual_version}. Resetting.")
                with open(VERSION_FILE, 'w') as f:
                    f.write(actual_version)
                return actual_version
            else:
                return stored_version
    except: pass
    
    return CURRENT_VERSION

def update_installed_version(new_version):
    try:
        os.makedirs(APP_DATA_DIR, exist_ok=True)
        with open(VERSION_FILE, 'w') as f:
            f.write(new_version)
        return True
    except: pass
    return False

def check_for_updates(force_check=False):
    try:
        latest_release = get_latest_release()
        if not latest_release: return None, None
            
        latest_tag = latest_release.get('tag_name', '')
        latest_version_match = re.search(r'v?(\d+\.\d+\.\d+)', latest_tag)
        
        if not latest_version_match: return None, None
            
        latest_version = latest_version_match.group(1)
        installed_version = get_installed_version()
        log_error(f"Current installed version: {installed_version}, Latest available: {latest_version}")
        
        settings = load_update_settings()
        skip_version = settings.get("skip_version", "")
        if not force_check and skip_version == latest_version:
            log_error(f"Skipping version {latest_version} as requested by user")
            return None, None
            
        if not force_check and not version.parse(latest_version) > version.parse(installed_version):
            log_error(f"No update needed - {latest_version} <= {installed_version}")
            return None, None
        
        if force_check:
            log_error(f"Force checking for updates: {latest_version}")
            
        download_url = None
        for asset in latest_release.get('assets', []):
            if asset.get('name', '').endswith('.zip'):
                download_url = asset.get('browser_download_url')
                break
        
        if not download_url and latest_release.get('zipball_url'):
            download_url = latest_release.get('zipball_url')
        
        if download_url:
            log_error(f"Update available: {latest_version}")
            if not force_check and settings.get("auto_download", False):
                log_error("Auto-download enabled, downloading update in background")
            return latest_version, download_url
        
        return None, None
    except Exception as e:
        log_error(f"Error checking for updates: {str(e)}")
        return None, None

def check_write_permissions():
    try:
        current_exe = sys.executable
        current_dir = os.path.dirname(current_exe)
        test_file = os.path.join(current_dir, "update_test_write.tmp")
        
        with open(test_file, "w") as f:
            f.write("test")
            
        os.unlink(test_file)
        return True
    except: return False

def is_admin():
    try:
        if platform.system() == 'Windows':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except: return False

def request_admin_privileges(script_path):
    try:
        if platform.system() == 'Windows':
            import ctypes
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, script_path, None, 0)
            return True
    except: pass
    return False

def clean_old_files():
    try:
        for file_type, pattern in [
            ("zip", lambda f: f.endswith('.zip')),
            ("dir", lambda d: os.path.isdir(os.path.join(UPDATES_DIR, d)) and not d.startswith('.')),
            ("bat", lambda f: f.startswith('updater_') and f.endswith('.bat')),
            ("vbs", lambda f: f.startswith('updater_') and f.endswith('.vbs')),
            ("py", lambda f: f.startswith('admin_updater') and f.endswith('.py') 
                           and (time.time() - os.path.getmtime(os.path.join(UPDATES_DIR, f)) > 3600))
        ]:
            items = [f for f in os.listdir(UPDATES_DIR) if pattern(f)]
            if len(items) > 2:
                items.sort(key=lambda i: os.path.getmtime(os.path.join(UPDATES_DIR, i)), reverse=True)
                for old_item in items[2:]:
                    path = os.path.join(UPDATES_DIR, old_item)
                    if os.path.isdir(path): shutil.rmtree(path)
                    else: os.unlink(path)
    except: pass

def log_error(message):
    try:
        os.makedirs(UPDATES_DIR, exist_ok=True)
        with open(os.path.join(UPDATES_DIR, "update_error.log"), "a") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
            import traceback
            traceback.print_exc(file=f)
    except: pass

def verify_executable(exe_path):
    if not os.path.exists(exe_path) or os.path.getsize(exe_path) < 1024 * 1024:
        return False
    
    if platform.system() == 'Windows':
        try:
            with open(exe_path, 'rb') as f:
                return f.read(2) == b'MZ'
        except: return False
    else:
        return os.access(exe_path, os.X_OK)

def install_update(extracted_path, version_str, parent_dialog=None):
    try:
        clean_old_files()
        update_installed_version(version_str)
        log_error(f"Updating to version: {version_str}")
        
        current_exe = sys.executable
        log_error(f"Current executable: {current_exe}")
        
        new_exe = None
        for root, dirs, files in os.walk(extracted_path):
            for file in files:
                if file.endswith('.exe'):
                    new_exe = os.path.join(root, file)
                    break
            if new_exe: break
        
        if not new_exe or not verify_executable(new_exe):
            log_error(f"No valid executable found in {extracted_path}")
            if parent_dialog:
                parent_dialog.status_label.setText("Error: No valid update found")
            return False
            
        log_error(f"New executable: {new_exe}")
        log_error(f"New exe exists: {os.path.exists(new_exe)}, size: {os.path.getsize(new_exe)}")
        
        backup_exe = os.path.join(BACKUP_DIR, f"{os.path.basename(current_exe)}.backup")
        os.makedirs(os.path.dirname(backup_exe), exist_ok=True)
        try:
            log_error(f"Creating backup at {backup_exe}")
            shutil.copy2(current_exe, backup_exe)
            log_error(f"Backup successful: {os.path.exists(backup_exe)}, size: {os.path.getsize(backup_exe)}")
        except Exception as e:
            log_error(f"Backup failed: {e}")
        
        need_admin = not check_write_permissions()
        
        if platform.system() == 'Windows':
            timestamp = int(time.time())
            
            if need_admin:
                updater_path = os.path.join(UPDATES_DIR, f"admin_updater_{timestamp}.py")
                updater_type = "admin python"
            else:
                bat_path = os.path.join(UPDATES_DIR, f"updater_{timestamp}.bat")
                updater_type = "batch file"
                
            current_size = os.path.getsize(current_exe) if os.path.exists(current_exe) else 0
            new_size = os.path.getsize(new_exe) if os.path.exists(new_exe) else 0
            log_error(f"Current exe size: {current_size}, New exe size: {new_size}")
            
            if parent_dialog and hasattr(parent_dialog.parent(), 'collectAppData'):
                try:
                    app_data = parent_dialog.parent().collectAppData()
                    if app_data:
                        save_path = os.path.join(UPDATES_DIR, f"appdata_backup_{timestamp}.json")
                        log_error(f"Saving app data to {save_path}")
                        with open(save_path, 'w') as f:
                            json.dump(app_data, f)
                except Exception as e:
                    log_error(f"Failed to save app data: {e}")
            
            if not need_admin:
                with open(bat_path, 'w') as f:
                    f.write('@echo off\n')
                    f.write('echo Updater batch file starting > "%TEMP%\\xddbot_update_bat.log"\n')
                    f.write(f'taskkill /F /IM {os.path.basename(current_exe)} /T\n')
                    f.write('timeout /t 5\n')
                    f.write(f'attrib -R -H -S "{current_exe}"\n')
                    f.write(f'del /F /Q "{current_exe}"\n')
                    f.write(f'copy /Y /B "{new_exe}" "{current_exe}"\n')
                    f.write('timeout /t 2\n')
                    f.write(f'start "" "{current_exe}" --updated\n')
                    f.write('exit\n')
                updater_path = bat_path
            
            if need_admin:
                with open(updater_path, 'w') as f:
                    f.write(f"""import os, sys, subprocess, time, shutil, json

try:
    def log_error(msg):
        with open(os.path.join("{UPDATES_DIR}", "admin_update_log.txt"), "a") as log:
            log.write(f"{{time.strftime('%Y-%m-%d %H:%M:%S')}} - {{msg}}\\n")

    log_error("Admin updater starting")
    current_exe = "{current_exe}"
    updater_exe = "{new_exe}"
    process_name = "{os.path.basename(current_exe)}"
    
    log_error(f"Current EXE: {{current_exe}}")
    log_error(f"Updater EXE: {{updater_exe}}")
    
    subprocess.call(['taskkill', '/F', '/IM', process_name, '/T'], 
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        subprocess.call(['wmic', 'process', 'where', f'ExecutablePath="{current_exe}"', 'delete'],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass
    time.sleep(5)
    
    if os.path.exists(updater_exe):
        log_error(f"Updater file size: {{os.path.getsize(updater_exe)}}")
        if os.path.exists(current_exe):
            log_error(f"Current file size: {{os.path.getsize(current_exe)}}")
        
        backup_path = os.path.join("{BACKUP_DIR}", os.path.basename(current_exe) + ".backup")
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        try:
            shutil.copy2(current_exe, backup_path)
            log_error(f"Backup created: {{os.path.exists(backup_path)}}")
        except Exception as backup_err:
            log_error(f"Backup error: {{backup_err}}")
            
        try:
            if os.path.exists(current_exe):
                os.chmod(current_exe, 0o777)
                temp_bak = current_exe + ".old"
                if os.path.exists(temp_bak): os.unlink(temp_bak)
                os.rename(current_exe, temp_bak)
                shutil.copy2(updater_exe, current_exe)
                try:
                    if os.path.exists(temp_bak): os.unlink(temp_bak)
                except: pass
            else:
                shutil.copy2(updater_exe, current_exe)
        except Exception as copy_err:
            log_error(f"Primary file replacement failed: {{copy_err}}")
            try:
                shutil.copy2(updater_exe, current_exe)
            except Exception as fallback_err:
                log_error(f"Fallback copy also failed: {{fallback_err}}")
                try:
                    subprocess.call(f'copy "{{updater_exe}}" "{{current_exe}}" /Y', shell=True)
                except Exception as shell_err:
                    log_error(f"Windows COPY also failed: {{shell_err}}")
            
        version_file = os.path.join("{APP_DATA_DIR}", "installed_version.txt")
        try:
            with open(version_file, 'w') as f:
                f.write("{version_str}")
        except Exception as ver_err:
            log_error(f"Failed to write version file: {{ver_err}}")
            
        time.sleep(2)
        
        if os.path.exists(current_exe):
            curr_size = os.path.getsize(current_exe)
            log_error(f"Updated file exists, size: {{curr_size}}")
            
            if curr_size > 1000000:
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(None, "open", current_exe, "--updated", None, 1)
            else:
                if os.path.exists(backup_path):
                    shutil.copy2(backup_path, current_exe)
                    time.sleep(1)
                    import ctypes
                    ctypes.windll.shell32.ShellExecuteW(None, "open", current_exe, "--update-failed", None, 1)
        else:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, current_exe)
                time.sleep(1)
                import ctypes
                ctypes.windll.shell32.ShellExecuteW(None, "open", current_exe, "--update-failed", None, 1)
except Exception as e:
    with open(os.path.join("{UPDATES_DIR}", "admin_update_error.log"), "w") as log:
        log.write(f"Error: {{e}}\\n")
        import traceback
        traceback.print_exc(file=log)
""")
            
            if parent_dialog:
                parent_dialog.status_label.setText("Installing update and restarting...")
                QApplication.processEvents()
            
            log_error(f"Starting {updater_type} updater: {updater_path}")
            try:
                if need_admin:
                    request_admin_privileges(updater_path)
                else:
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags = subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0
                    
                    subprocess.Popen(
                        ["cmd.exe", "/c", updater_path],
                        startupinfo=startupinfo,
                        shell=False,
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS | subprocess.HIGH_PRIORITY_CLASS,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        close_fds=True
                    )
                
                log_error("Exiting application to allow update...")
                time.sleep(1)
                if parent_dialog and hasattr(parent_dialog, 'parent') and parent_dialog.parent():
                    parent = parent_dialog.parent()
                    if hasattr(parent, 'close_application'):
                        parent.close_application()
                QApplication.quit()
                os._exit(0)
                return True
            except Exception as e:
                log_error(f"Error launching updater: {e}")
                if parent_dialog:
                    parent_dialog.status_label.setText(f"Error launching updater: {str(e)}")
                    parent_dialog.skip_btn.setEnabled(True)
                    parent_dialog.install_btn.setEnabled(True)
                    parent_dialog.skip_btn.setText("Close")
                    parent_dialog.is_downloading = False
                return False
        
        return False
    except Exception as e:
        log_error(f"Update failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def show_update_dialog(parent=None, force_check=False):
    try:
        if not force_check:
            settings = load_update_settings()
            if "skip_version" in settings:
                settings.pop("skip_version")
                save_update_settings(settings)
        
        latest_version, download_url = check_for_updates(force_check=force_check)
        
        if latest_version and download_url:
            dialog = UpdateDialog(latest_version, download_url, parent)
            
            if parent:
                center = parent.geometry().center()
                dialog_rect = dialog.frameGeometry()
                dialog_rect.moveCenter(center)
                dialog.move(dialog_rect.topLeft())
            
            return dialog.exec_()
        elif force_check and parent:
            QMessageBox.information(parent, "No Updates Available", 
                                  f"You are running the latest version ({get_installed_version()}).")
        
        return False
    except Exception as e:
        log_error(f"Error showing update dialog: {str(e)}")
        return False

def reset_update_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            settings = load_update_settings()
            if "skip_version" in settings:
                settings.pop("skip_version")
                save_update_settings(settings)
            return True
    except: pass
    return False

def test_vbs_generation():
    try:
        timestamp = int(time.time())
        vbs_updater_path = os.path.join(os.getcwd(), f"test_updater_{timestamp}.vbs")
        
        current_exe = os.path.join("C:\\Program Files\\TestApp", "test.exe").replace('\\', '\\\\')
        new_exe = os.path.join("C:\\Downloads\\TestApp", "test.exe").replace('\\', '\\\\')
        backup_dir = os.path.join("C:\\Backups").replace('\\', '\\\\')
        backup_exe = os.path.join(backup_dir, "test.exe.backup").replace('\\', '\\\\')
        log_path = os.path.join("C:\\Temp", "update.log").replace('\\', '\\\\')
        
        with open(vbs_updater_path, 'w') as f:
            f.write('On Error Resume Next\n')
            f.write('Dim WshShell, fso, objFile\n')
            f.write('Set WshShell = CreateObject("WScript.Shell")\n')
            f.write('Set fso = CreateObject("Scripting.FileSystemObject")\n\n')
            
            f.write('Sub LogMessage(msg)\n')
            f.write('    On Error Resume Next\n')
            f.write(f'    Set objFile = fso.OpenTextFile("{log_path}", 8, True)\n')
            f.write('    If Err.Number <> 0 Then\n')
            f.write('        Err.Clear\n')
            f.write('        Exit Sub\n')
            f.write('    End If\n')
            f.write('    objFile.WriteLine(Now & " - " & msg)\n')
            f.write('    objFile.Close\n')
            f.write('End Sub\n\n')
            
            f.write('LogMessage "Updater starting"\n')
            f.write('LogMessage "Killing process: test.exe"\n')
            f.write('WshShell.Run "taskkill /F /IM test.exe /T", 0, True\n')
            f.write('WScript.Sleep 3000\n\n')
            
            f.write('LogMessage "Starting file replacement"\n')
            f.write(f'If fso.FileExists("{current_exe}") Then\n')
            
            f.write(f'    If Not fso.FileExists("{backup_exe}") Then\n')
            f.write('        LogMessage "Creating backup"\n')
            f.write(f'        fso.CreateFolder "{backup_dir}"\n')
            f.write(f'        fso.CopyFile "{current_exe}", "{backup_exe}", True\n')
            f.write('    End If\n\n')
            
            f.write('    LogMessage "Setting file attributes to normal"\n')
            f.write('    On Error Resume Next\n')
            f.write(f'    WshShell.Run "attrib -R -H -S " & Chr(34) & "{current_exe}" & Chr(34), 0, True\n')
            
            f.write('    LogMessage "Force copying new file over existing one"\n')
            f.write(f'    WshShell.Run "cmd.exe /c copy /Y /B " & Chr(34) & "{new_exe}" & Chr(34) & " " & Chr(34) & "{current_exe}" & Chr(34), 0, True\n')
            f.write('    WScript.Sleep 2000\n')
            
            f.write('    LogMessage "Attempting direct deletion if needed"\n')
            f.write('    On Error Resume Next\n')
            f.write(f'    fso.DeleteFile "{current_exe}"\n')
            f.write('    If Err.Number <> 0 Then\n')
            f.write('        LogMessage "Direct deletion failed: " & Err.Description\n')
            f.write('        Err.Clear\n')
            
            f.write('        LogMessage "Trying rename method"\n')
            f.write(f'        fso.MoveFile "{current_exe}", "{current_exe}.old"\n')
            f.write('        If Err.Number <> 0 Then\n')
            f.write('            LogMessage "Rename failed: " & Err.Description\n')
            f.write('            Err.Clear\n')
            
            f.write('            LogMessage "Using shell COPY command with Chr(34)"\n')
            f.write(f'            WshShell.Run "cmd.exe /c copy /Y /B " & Chr(34) & "{new_exe}" & Chr(34) & " " & Chr(34) & "{current_exe}" & Chr(34), 0, True\n')
            f.write('        Else\n')
            f.write(f'            fso.CopyFile "{new_exe}", "{current_exe}", True\n')
            f.write(f'            fso.DeleteFile "{current_exe}.old"\n')
            f.write('        End If\n')
            f.write('    Else\n')
            f.write('        LogMessage "Direct deletion successful"\n')
            f.write(f'        fso.CopyFile "{new_exe}", "{current_exe}", True\n')
            f.write('    End If\n')
            f.write('End If\n\n')
            
            f.write('WScript.Sleep 1000\n')
            f.write('LogMessage "Verifying file copy"\n')
            f.write(f'If fso.FileExists("{current_exe}") Then\n')
            f.write('    LogMessage "File exists, launching application"\n')
            f.write(f'    CreateObject("Shell.Application").ShellExecute "{current_exe}", "--updated", "", "open", 1\n')
            f.write('Else\n')
            f.write('    LogMessage "File not found, restoring from backup"\n')
            f.write(f'    If fso.FileExists("{backup_exe}") Then\n')
            f.write(f'        fso.CopyFile "{backup_exe}", "{current_exe}", True\n')
            f.write(f'        CreateObject("Shell.Application").ShellExecute "{current_exe}", "--update-failed", "", "open", 1\n')
            f.write('    End If\n')
            f.write('End If\n')
        
        print(f"Test VBS file written to: {vbs_updater_path}")
        return vbs_updater_path
    except Exception as e:
        print(f"Error generating test VBS: {e}")
        return None