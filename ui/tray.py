import logging
import os

from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu

log = logging.getLogger("airpux.tray")


class AirPodsTray(QSystemTrayIcon):
    def __init__(self, parent=None):
        super().__init__(parent)
        icon = QIcon.fromTheme("bluetooth")
        if icon.isNull():
            icon_path = os.path.join(os.path.dirname(__file__), "..", "icons", "airpux.svg")
            if os.path.exists(icon_path):
                icon = QIcon(icon_path)
        self.setIcon(icon)
        self.setToolTip("AirPux")

        self._menu = QMenu()
        self._battery_action = QAction("Battery: --")
        self._battery_action.setEnabled(False)
        self._menu.addAction(self._battery_action)

        self._anc_action = QAction("ANC: --")
        self._anc_action.triggered.connect(self._on_anc_click)
        self._menu.addAction(self._anc_action)

        self._ear_action = QAction("Ear Detection: --")
        self._ear_action.setEnabled(False)
        self._menu.addAction(self._ear_action)

        self._menu.addSeparator()

        self._settings_action = QAction("Settings")
        self._menu.addAction(self._settings_action)

        self._quit_action = QAction("Quit")
        self._menu.addAction(self._quit_action)

        self.setContextMenu(self._menu)

        self.on_anc_cycle: callable | None = None
        self.on_quit: callable | None = None
        self.on_settings: callable | None = None

        self._quit_action.triggered.connect(lambda: self.on_quit() if self.on_quit else None)
        self._settings_action.triggered.connect(lambda: self.on_settings() if self.on_settings else None)

    def _on_anc_click(self):
        if self.on_anc_cycle:
            self.on_anc_cycle()

    def update_battery(self, text: str):
        self._battery_action.setText(f"Battery: {text}")

    def set_anc_available(self, available: bool):
        if available:
            self._anc_action.setText("ANC: --")
            self._anc_action.setEnabled(True)
        else:
            self._anc_action.setText("ANC: N/A")
            self._anc_action.setEnabled(False)

    def update_anc(self, text: str):
        self._anc_action.setText(f"ANC: {text}")

    def update_ear_detection(self, left: bool, right: bool):
        status = f"L={'in' if left else 'out'} R={'in' if right else 'out'}"
        self._ear_action.setText(f"Ears: {status}")

    def show_message(self, title: str, message: str):
        self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)
