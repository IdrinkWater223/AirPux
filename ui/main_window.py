import logging
import json
import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QHBoxLayout, QMessageBox, QCheckBox,
)
from PyQt6.QtCore import Qt

CONFIG_DIR = os.path.expanduser("~/.config/airpux")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

log = logging.getLogger("airpux.settings")


def load_config() -> dict:
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"mac_address": ""}


def save_config(cfg: dict):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    log.info("Config saved to %s", CONFIG_PATH)


class SettingsWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AirPux Settings")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        cfg = load_config()
        self._mac_input = QLineEdit(cfg.get("mac_address", ""))
        self._mac_input.setPlaceholderText("XX:XX:XX:XX:XX:XX")
        form.addRow("AirPods MAC:", self._mac_input)

        self._anc_check = QCheckBox("Device supports ANC / noise control")
        self._anc_check.setChecked(cfg.get("has_anc", True))
        form.addRow(self._anc_check)

        layout.addLayout(form)

        info = QLabel("Find your AirPods MAC in Bluetooth settings or run bluetoothctl")
        info.setWordWrap(True)
        info.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(info)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

    def _save(self):
        mac = self._mac_input.text().strip()
        has_anc = self._anc_check.isChecked()
        save_config({"mac_address": mac, "has_anc": has_anc})
        QMessageBox.information(self, "Saved", f"MAC address set to {mac}")
        self.accept()
