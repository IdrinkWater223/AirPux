import asyncio
import logging
import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
import qasync

from bluetooth.scanner import BlueZScanner
from bluetooth.aap_client import AAPClient
from bluetooth.protocol import ANC_LABELS, supports_anc
from features.battery import BatteryMonitor
from features.ear_detection import EarDetectionHandler
from features.anc_mode import ANCModeController
from features.media_control import MediaControl
from ui.tray import AirPodsTray
from ui.main_window import SettingsWindow, load_config, save_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("airpux")


class AirPodsApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("AirPux")
        self.app.setQuitOnLastWindowClosed(False)

        self._loop = qasync.QEventLoop(self.app)
        asyncio.set_event_loop(self._loop)

        self._cfg = load_config()
        self._scanner = BlueZScanner()
        self._media = MediaControl()
        self._battery = BatteryMonitor()
        self._aap: AAPClient | None = None
        self._anc: ANCModeController | None = None
        self._ear: EarDetectionHandler | None = None

        self._tray = AirPodsTray()
        self._tray.on_quit = self._quit
        self._tray.on_anc_cycle = self._cycle_anc
        self._tray.on_settings = self._open_settings
        self._tray.show()

    def _quit(self):
        log.info("Shutting down")
        if self._aap and self._aap.connected:
            asyncio.ensure_future(self._aap.disconnect())
        self.app.quit()

    def _cycle_anc(self):
        if self._anc:
            self._anc.cycle()

    def _open_settings(self):
        w = SettingsWindow()
        if w.exec() == SettingsWindow.DialogCode.Accepted:
            self._cfg = load_config()
            mac = self._cfg.get("mac_address", "")
            if mac:
                asyncio.ensure_future(self._start_connection(mac))

    def _on_battery(self, data: dict):
        self._battery.update(data)
        self._tray.update_battery(self._battery.summary())

    def _on_ear(self, data: dict):
        if self._ear:
            self._ear.update(data)
        self._tray.update_ear_detection(
            data.get("left", False), data.get("right", False)
        )

    def _on_anc(self, mode: int):
        if self._anc:
            self._anc.update(mode)
        self._tray.update_anc(ANC_LABELS.get(mode, f"0x{mode:02X}"))

    def _on_device_info(self, data: dict):
        name = data.get("name", "AirPods")
        model = data.get("model", "")
        has_anc = self._cfg.get("has_anc", supports_anc(model))
        log.info("Connected to: %s (ANC: %s)", name, "yes" if has_anc else "no")
        self._tray.set_anc_available(has_anc)
        self._tray.show_message("AirPux", f"Connected to {name}")
        self._tray.setToolTip(f"AirPux — {name}")
        if has_anc:
            self._anc = ANCModeController(self._aap)
            self._aap.on_anc_change = self._on_anc

    def _on_disconnected(self):
        log.info("AirPods disconnected")
        self._tray.update_battery("disconnected")
        self._tray.setIcon(self._tray.icon())

    async def _start_connection(self, mac: str):
        if self._aap and self._aap.connected:
            await self._aap.disconnect()

        self._aap = AAPClient(mac)
        self._aap.on_battery = self._on_battery
        self._aap.on_ear_detection = self._on_ear
        self._aap.on_device_info = self._on_device_info
        self._aap.on_disconnected = self._on_disconnected

        self._anc = None
        self._ear = EarDetectionHandler(self._media)

        try:
            await self._aap.connect()
            await self._aap.request_device_info()
            log.info("Connection established to %s", mac)
        except Exception as e:
            log.error("Could not connect to %s: %s", mac, e)
            self._tray.show_message("Connection Failed", str(e))

    async def _auto_connect(self):
        mac = self._cfg.get("mac_address", "")
        if mac:
            log.info("Auto-connecting to %s", mac)
            await self._start_connection(mac)
        else:
            log.info("No MAC configured — scanning for connected AirPods")
            device = self._scanner.get_connected_airpods()
            if device:
                mac = device["address"]
                log.info("Found connected AirPods: %s (%s)", device["name"], mac)
                self._cfg["mac_address"] = mac
                save_config(self._cfg)
                await self._start_connection(mac)
            else:
                log.info("No connected AirPods found. Open Settings to configure.")

    def run(self):
        with self._loop:
            asyncio.ensure_future(self._auto_connect())
            self._loop.run_forever()


def main():
    app = AirPodsApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
