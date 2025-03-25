from PyQt5.QtWidgets import QApplication

_qapp = None
if QApplication.instance() is None and not hasattr(QApplication, '_in_test'):
    import sys
    _qapp = QApplication([sys.argv[0]])
    _qapp.setQuitOnLastWindowClosed(False)

from ui.key_capture import KeyCaptureWidget
from ui.command_row import CommandRowCreator
from ui.command_ui import CommandUI

__all__ = ['KeyCaptureWidget', 'CommandUI', 'CommandRowCreator'] 