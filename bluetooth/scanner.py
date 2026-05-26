import logging
from dasbus.connection import SystemMessageBus
from dasbus.loop import EventLoop

BLUEZ_SERVICE = "org.bluez"
ADAPTER_INTERFACE = "org.bluez.Adapter1"
DEVICE_INTERFACE = "org.bluez.Device1"
OBJECT_MANAGER = "org.freedesktop.DBus.ObjectManager"
PROPERTIES = "org.freedesktop.DBus.Properties"

AIRPODS_PATTERNS = ("AirPods", "AirPods Pro", "Beats")

log = logging.getLogger("airpux.scanner")


class BlueZScanner:
    def __init__(self):
        self.bus = SystemMessageBus()
        self._adapter_path = None

    def _find_adapter(self) -> str | None:
        objects = self.bus.get_proxy(BLUEZ_SERVICE, "/").GetManagedObjects()
        for path, interfaces in objects.items():
            if ADAPTER_INTERFACE in interfaces:
                self._adapter_path = path
                log.info("Using BT adapter: %s", path)
                return path
        log.warning("No Bluetooth adapter found")
        return None

    def start_discovery(self):
        if not self._adapter_path:
            if not self._find_adapter():
                return
        adapter = self.bus.get_proxy(BLUEZ_SERVICE, self._adapter_path)
        try:
            adapter.StartDiscovery()
            log.info("Discovery started")
        except Exception as e:
            log.warning("Discovery may already be running: %s", e)

    def stop_discovery(self):
        if not self._adapter_path:
            return
        adapter = self.bus.get_proxy(BLUEZ_SERVICE, self._adapter_path)
        try:
            adapter.StopDiscovery()
            log.info("Discovery stopped")
        except Exception:
            pass

    def get_connected_devices(self) -> list[dict]:
        objects = self.bus.get_proxy(BLUEZ_SERVICE, "/").GetManagedObjects()
        devices = []
        for path, interfaces in objects.items():
            if DEVICE_INTERFACE not in interfaces:
                continue
            props = interfaces[DEVICE_INTERFACE]
            name = props.get("Name", "") or ""
            if any(p in name for p in AIRPODS_PATTERNS):
                devices.append({
                    "path": path,
                    "name": name,
                    "address": props.get("Address", ""),
                    "connected": bool(props.get("Connected", False)),
                    "paired": bool(props.get("Paired", False)),
                })
        return devices

    def get_connected_airpods(self) -> dict | None:
        for d in self.get_connected_devices():
            if d["connected"]:
                return d
        return None

    def connect_device(self, device_path: str) -> bool:
        device = self.bus.get_proxy(BLUEZ_SERVICE, device_path)
        try:
            device.Connect()
            log.info("Connecting to %s", device_path)
            return True
        except Exception as e:
            log.error("Connect failed: %s", e)
            return False

    def disconnect_device(self, device_path: str):
        device = self.bus.get_proxy(BLUEZ_SERVICE, device_path)
        try:
            device.Disconnect()
            log.info("Disconnected %s", device_path)
        except Exception as e:
            log.error("Disconnect failed: %s", e)
