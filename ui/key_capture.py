from PyQt5.QtWidgets import QLineEdit, QApplication
from PyQt5.QtCore import Qt

class KeyCaptureWidget(QLineEdit):
    def __init__(self, initial_hotkey='', parent=None):
        super().__init__(parent)
        self.hotkey = initial_hotkey
        self.setText(initial_hotkey if initial_hotkey else "No key set")
        self.setReadOnly(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setCursorPosition(0)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.setCursor(Qt.PointingHandCursor)
        self.setPlaceholderText("Click to capture hotkey...")
        self.setToolTip("Click once to start capturing, then press any key or mouse button")
        self.setFocusPolicy(Qt.ClickFocus)
        self.capturing = False
        self.ignore_next_release = False
        
        font = self.font()
        font.setBold(True)
        self.setFont(font)
        
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.capturing = True
        self.ignore_next_release = True
        self.setText("Press a key...")
        self.selectAll()
        
    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.capturing = False
        if not self.hotkey:
            self.setText("No key set")
        else:
            self.setText(self.hotkey)
    
    def mousePressEvent(self, event):
        if not self.capturing:
            super().mousePressEvent(event)
            return
            
        if self.ignore_next_release:
            self.ignore_next_release = False
            super().mousePressEvent(event)
            return
            
        button_map = {
            Qt.LeftButton: "mouse1",
            Qt.RightButton: "mouse2",
            Qt.MiddleButton: "mouse3",
            Qt.BackButton: "mouse4",
            Qt.ForwardButton: "mouse5"
        }
        
        modifiers = []
        if QApplication.keyboardModifiers() & Qt.ControlModifier:
            modifiers.append("ctrl")
        if QApplication.keyboardModifiers() & Qt.AltModifier:
            modifiers.append("alt")
        if QApplication.keyboardModifiers() & Qt.ShiftModifier:
            modifiers.append("shift")
            
        button_text = button_map.get(event.button(), "")
        
        if button_text:
            if modifiers:
                self.hotkey = "+".join(modifiers + [button_text])
            else:
                self.hotkey = button_text
                
            self.setText(self.hotkey)
            self.clearFocus()
        else:
            super().mousePressEvent(event)
            
    def keyPressEvent(self, event):
        if not self.capturing:
            return super().keyPressEvent(event)
        
        if event.key() == Qt.Key_Escape:
            self.capturing = False
            self.setText(self.hotkey if self.hotkey else "No key set")
            self.clearFocus()
            return
            
        modifiers = []
        if event.modifiers() & Qt.ControlModifier:
            modifiers.append("ctrl")
        if event.modifiers() & Qt.AltModifier:
            modifiers.append("alt")
        if event.modifiers() & Qt.ShiftModifier:
            modifiers.append("shift")
            
        key = event.key()
        key_text = ""
        
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return
        
        if Qt.Key_F1 <= key <= Qt.Key_F12:
            key_text = f"f{key - Qt.Key_F1 + 1}"
        elif Qt.Key_A <= key <= Qt.Key_Z:
            key_text = chr(key).lower()
        elif Qt.Key_0 <= key <= Qt.Key_9:
            key_text = chr(key)
        else:
            key_map = {
                Qt.Key_Escape: "esc",
                Qt.Key_Tab: "tab",
                Qt.Key_Space: "space",
                Qt.Key_Return: "enter",
                Qt.Key_Backspace: "backspace",
                Qt.Key_Delete: "delete",
                Qt.Key_Home: "home",
                Qt.Key_End: "end",
                Qt.Key_PageUp: "pageup",
                Qt.Key_PageDown: "pagedown",
                Qt.Key_Insert: "insert",
                Qt.Key_Left: "left",
                Qt.Key_Right: "right",
                Qt.Key_Up: "up",
                Qt.Key_Down: "down",
                Qt.Key_Period: ".",
                Qt.Key_Comma: ",",
                Qt.Key_Plus: "+",
                Qt.Key_Minus: "-",
                Qt.Key_Slash: "/",
                Qt.Key_Backslash: "\\",
                Qt.Key_Semicolon: ";",
                Qt.Key_Equal: "="
            }
            key_text = key_map.get(key, "")
            
        if not key_text:
            event.accept()
            return
            
        if modifiers:
            self.hotkey = "+".join(modifiers + [key_text])
        else:
            self.hotkey = key_text
            
        self.setText(self.hotkey)
        self.clearFocus()
        event.accept()
        
    def get_hotkey(self):
        return self.hotkey
        
    def set_hotkey(self, hotkey):
        self.hotkey = hotkey
        self.setText(hotkey if hotkey else "No key set") 