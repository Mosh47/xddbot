from PyQt5.QtWidgets import QWidget
from ui.layout import TabLayout
from ui.builder import UIBuilder

class CommandUI:
    def __init__(self, parent):
        self.parent = parent
        self.status_bar = None
        self.ui_components = {}
        self.whisper_components = {}
        
    def build_ui(self, settings, whisper_settings, clear_callback, clear_whisper_callback, add_command_callback, add_whisper_callback, delete_command_callback, delete_whisper_callback, discard_callback, apply_callback, hide_callback):
        container = QWidget(self.parent)
        
        container.setStyleSheet(UIBuilder.setup_default_stylesheet())
        
        layout = TabLayout()
        ui_components, whisper_components, status_bar = layout.build_ui(
            container, 
            settings, 
            whisper_settings, 
            {
                "clear_callback": clear_callback,
                "clear_whisper_callback": clear_whisper_callback,
                "add_command_callback": add_command_callback,
                "add_whisper_callback": add_whisper_callback,
                "delete_command_callback": delete_command_callback,
                "delete_whisper_callback": delete_whisper_callback,
                "discard_callback": discard_callback,
                "apply_callback": apply_callback,
                "hide": hide_callback
            }
        )
        
        self.ui_components = ui_components
        self.whisper_components = whisper_components
        self.status_bar = status_bar
        
        return container 