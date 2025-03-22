import os
import subprocess
import winreg

def check_npcap_registry():
    """Check Windows registry for Npcap installation"""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Npcap") as key:
            return True
    except WindowsError:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Npcap") as key:
                return True
        except WindowsError:
            return False

def check_npcap_service():
    """Check if Npcap service exists and is running"""
    try:
        output = subprocess.check_output("sc query npf", shell=True)
        return b"RUNNING" in output
    except:
        return False

def check_npcap_files():
    """Check for existence of key Npcap files"""
    npcap_files = [
        r"C:\Windows\System32\Npcap\wpcap.dll",
        r"C:\Windows\System32\Npcap\Packet.dll"
    ]
    return all(os.path.exists(file) for file in npcap_files)

def is_npcap_installed():
    """Check if Npcap is installed using multiple methods"""
    return (check_npcap_registry() or 
            check_npcap_service() or 
            check_npcap_files()) 