import logging

from bluetooth.l2cap_client import L2CAPAAPTransport
from bluetooth.protocol import (
    parse_battery, model_name, ANC_LABELS, build_noise_control_packet,
    NOISE_MODE_OFF,
)

log = logging.getLogger("airpux.aap")


class AAPClient:
    def __init__(self, mac_address: str):
        self.mac = mac_address
        self._transport = L2CAPAAPTransport(mac_address)
        self._transport.on_metadata = self._on_metadata
        self._transport.on_battery = self._on_battery
        self._transport.on_ear_detection = self._on_ear_detection
        self._transport.on_noise_control = self._on_noise_control
        self._transport.on_disconnected = self._on_disconnected

        self._device_name: str | None = None
        self._model: str | None = None

        self.on_battery: callable | None = None
        self.on_ear_detection: callable | None = None
        self.on_anc_change: callable | None = None
        self.on_device_info: callable | None = None
        self.on_disconnected: callable | None = None

    @property
    def connected(self) -> bool:
        return self._transport.connected

    async def connect(self):
        await self._transport.connect()

    async def disconnect(self):
        await self._transport.disconnect()

    async def request_device_info(self):
        pass

    async def set_noise_control(self, mode: int):
        pkt = build_noise_control_packet(mode)
        await self._transport.send(pkt)

    def _on_metadata(self, info: dict):
        name = info.get("name", "")
        model = info.get("model", "")
        self._device_name = name
        self._model = model
        label = model_name(model)
        log.info("Device: %s — %s (%s)", name, label, model)
        if self.on_device_info:
            payload = {"name": name, "model": model, "model_label": label}
            self.on_device_info(payload)

    def _on_battery(self, bat: dict):
        log.info("Battery: %s", bat)
        if self.on_battery:
            self.on_battery(bat)

    def _on_ear_detection(self, ear: dict):
        log.info("Ear detection: %s", ear)
        if self.on_ear_detection:
            self.on_ear_detection(ear)

    def _on_noise_control(self, mode: int):
        label = ANC_LABELS.get(mode, f"0x{mode:02X}")
        log.info("ANC mode: %s", label)
        if self.on_anc_change:
            self.on_anc_change(mode)

    def _on_disconnected(self):
        log.info("AAP client disconnected")
        if self.on_disconnected:
            self.on_disconnected()
