import asyncio
import logging
import socket
import struct

log = logging.getLogger("airpux.l2cap")

PSM_AAP = 0x1001

HANDSHAKE = bytes.fromhex("00000400010002000000000000000000")
SET_FEATURES = bytes.fromhex("040004004d00d700000000000000")
REQ_NOTIFICATIONS = bytes.fromhex("040004000f00ffffffffff")

CTRL_HEADER = bytes.fromhex("040004000900")

SIGNATURE_HANDSHAKE_ACK = bytes.fromhex("01000400")
SIGNATURE_FEATURES_ACK = bytes.fromhex("040004002b00")
SIGNATURE_METADATA = bytes.fromhex("040004001d00")
SIGNATURE_BATTERY = bytes.fromhex("040004000400")
SIGNATURE_EAR_DETECTION = bytes.fromhex("040004000600")
SIGNATURE_NOISE = bytes.fromhex("040004000900")


class L2CAPAAPTransport:
    def __init__(self, mac_address: str):
        self.mac = mac_address
        self._sock: socket.socket | None = None
        self._connected = False
        self._handshake_done = False

        self.on_metadata: callable | None = None
        self.on_battery: callable | None = None
        self.on_ear_detection: callable | None = None
        self.on_noise_control: callable | None = None
        self.on_binary_feature: callable | None = None
        self.on_disconnected: callable | None = None
        self.on_unknown: callable | None = None

    @property
    def connected(self) -> bool:
        return self._connected and self._handshake_done

    async def connect(self):
        log.info("Connecting to %s on L2CAP PSM 0x%04X", self.mac, PSM_AAP)
        try:
            self._sock = socket.socket(
                socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP
            )
            self._sock.settimeout(15)
            self._main_loop = asyncio.get_event_loop()
            await asyncio.get_event_loop().run_in_executor(
                None, self._sock.connect, (self.mac, PSM_AAP)
            )
            self._sock.settimeout(None)
            self._connected = True
            log.info("L2CAP connected, starting handshake")
            await self._do_handshake()
        except Exception as e:
            log.error("L2CAP connect failed: %s", e)
            self._connected = False
            raise

    async def _do_handshake(self):
        log.info("Step 1: Sending HANDSHAKE")
        await self._send_raw(HANDSHAKE)
        resp = await self._recv_raw()
        if resp and resp.startswith(SIGNATURE_HANDSHAKE_ACK):
            log.info("Step 2: Got HANDSHAKE_ACK")
        else:
            raise ConnectionError(f"Expected HANDSHAKE_ACK, got: {resp.hex() if resp else 'None'}")

        log.info("Step 3: Sending SET_SPECIFIC_FEATURES")
        await self._send_raw(SET_FEATURES)
        resp = await self._recv_raw()
        if resp and resp.startswith(SIGNATURE_FEATURES_ACK):
            log.info("Step 4: Got FEATURES_ACK (%d bytes)", len(resp))
        else:
            raise ConnectionError(f"Expected FEATURES_ACK, got: {resp.hex() if resp else 'None'}")

        log.info("Step 5: Sending REQUEST_NOTIFICATIONS")
        await self._send_raw(REQ_NOTIFICATIONS)
        resp = await self._recv_raw()
        if resp:
            log.info("Step 6: Got response (%d bytes): %s", len(resp), resp.hex()[:60])
        else:
            raise ConnectionError("No response to REQUEST_NOTIFICATIONS")

        self._handshake_done = True
        log.info("Handshake complete!")

        await self._handle_pending_data(resp)

    async def _handle_pending_data(self, first_resp: bytes):
        self._dispatch(first_resp)
        await asyncio.get_event_loop().run_in_executor(None, self._read_loop)

    def _read_loop(self):
        while self._connected and self._sock:
            try:
                data = self._sock.recv(4096)
                if not data:
                    log.info("L2CAP connection closed")
                    break
                self._main_loop.call_soon_threadsafe(self._dispatch, data)
            except socket.timeout:
                continue
            except Exception as e:
                if self._connected:
                    log.error("L2CAP read error: %s", e)
                break
        if self._connected:
            self._connected = False
            if self.on_disconnected:
                self._main_loop.call_soon_threadsafe(self.on_disconnected)

    def _dispatch(self, data: bytes):
        if not data:
            return

        if data.startswith(SIGNATURE_METADATA):
            self._handle_metadata(data)
        elif data.startswith(SIGNATURE_BATTERY):
            self._handle_battery(data)
        elif data.startswith(SIGNATURE_EAR_DETECTION):
            self._handle_ear_detection(data)
        elif data.startswith(SIGNATURE_NOISE) and len(data) == 11:
            self._handle_noise(data)
        elif data.startswith(CTRL_HEADER) and len(data) == 11:
            self._handle_binary_feature(data)
        elif data.startswith(bytes.fromhex("040004004b00")):
            log.debug("Conversational awareness data: %s", data.hex())
        else:
            log.debug("Unknown packet: %s", data.hex())
            if self.on_unknown:
                self.on_unknown(data)

    def _handle_metadata(self, data: bytes):
        pos = 6
        if pos < len(data) and data[pos] == 0x02:
            marker = data.find(b'\x00\x04\x00', pos)
            if marker != -1:
                pos = marker + 3
        strings = []
        while pos < len(data):
            end = data.find(b'\x00', pos)
            if end == -1:
                break
            if end > pos:
                strings.append(data[pos:end].decode('utf-8', errors='replace'))
            pos = end + 1
        info = {}
        if len(strings) >= 1:
            info["name"] = strings[0]
        if len(strings) >= 2:
            info["model"] = strings[1]
        if len(strings) >= 3:
            info["manufacturer"] = strings[2]
        if len(strings) >= 4:
            info["serial"] = strings[3]
        log.info("Metadata: %s", info)
        if self.on_metadata:
            self.on_metadata(info)

    def _handle_battery(self, data: bytes):
        if len(data) != 22:
            log.debug("Battery packet unexpected length: %d", len(data))
            return
        payload = data[6:]
        count = payload[0]
        bat = {}
        pos = 1
        for _ in range(count):
            if pos + 4 > len(payload):
                break
            comp = payload[pos]
            _spacer = payload[pos + 1]
            level = payload[pos + 2]
            status = payload[pos + 3]
            _end = payload[pos + 4] if pos + 4 < len(payload) else 0
            side_map = {0x02: "right", 0x04: "left", 0x08: "case"}
            side = side_map.get(comp, f"0x{comp:02X}")
            bat[side] = level
            pos += 5
        log.info("Battery: %s", bat)
        if self.on_battery:
            self.on_battery(bat)

    def _handle_ear_detection(self, data: bytes):
        if len(data) < 8:
            return
        primary = data[6]
        secondary = data[7]
        ear = {
            "left": primary == 0x00 if primary in (0x00, 0x01) else None,
            "right": secondary == 0x00 if secondary in (0x00, 0x01) else None,
        }
        log.info("Ear detection: primary=0x%02X secondary=0x%02X", primary, secondary)
        if self.on_ear_detection:
            self.on_ear_detection(ear)

    def _handle_noise(self, data: bytes):
        if len(data) < 8:
            return
        mode = data[7]
        mode_map = {1: "off", 2: "anc", 3: "transparency", 4: "adaptive"}
        label = mode_map.get(mode, f"0x{mode:02X}")
        log.info("Noise control mode: %s", label)
        if self.on_noise_control:
            self.on_noise_control(mode)

    def _handle_binary_feature(self, data: bytes):
        if len(data) < 8:
            return
        feature = data[6]
        value = data[7]
        log.debug("Binary feature 0x%02X = 0x%02X", feature, value)
        if self.on_binary_feature:
            self.on_binary_feature(feature, value)

    async def send_noise_control(self, mode: int):
        mode_map = {"off": 1, "anc": 2, "transparency": 3, "adaptive": 4}
        if isinstance(mode, str):
            mode = mode_map.get(mode, 1)
        pkt = CTRL_HEADER + bytes([0x0D, mode, 0x00, 0x00, 0x00])
        await self._send_raw(pkt)

    async def send(self, data: bytes):
        await self._send_raw(data)

    async def _send_raw(self, data: bytes):
        if not self._sock or not self._connected:
            raise ConnectionError("Not connected")
        await asyncio.get_event_loop().run_in_executor(None, self._sock.send, data)

    async def _recv_raw(self) -> bytes | None:
        if not self._sock:
            return None
        return await asyncio.get_event_loop().run_in_executor(None, self._sock.recv, 4096)

    async def disconnect(self):
        self._connected = False
        self._handshake_done = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        log.info("L2CAP AAP disconnected")
        if self.on_disconnected:
            self.on_disconnected()
