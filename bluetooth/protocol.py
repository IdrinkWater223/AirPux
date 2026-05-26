CTRL_HEADER = bytes.fromhex("040004000900")

NOISE_MODE_OFF = 1
NOISE_MODE_ANC = 2
NOISE_MODE_TRANSPARENCY = 3
NOISE_MODE_ADAPTIVE = 4

ANC_LABELS = {
    NOISE_MODE_OFF: "Off",
    NOISE_MODE_ANC: "ANC",
    NOISE_MODE_TRANSPARENCY: "Transparency",
    NOISE_MODE_ADAPTIVE: "Adaptive",
}

MODEL_MAP = {
    "A2564": "AirPods Pro (2nd gen, Lightning)",
    "A2565": "AirPods Pro (2nd gen, Lightning)",
    "A2566": "AirPods Pro (2nd gen, Lightning)",
    "A2698": "AirPods Pro (2nd gen, USB-C)",
    "A2699": "AirPods Pro (2nd gen, USB-C)",
    "A2700": "AirPods Pro (2nd gen, USB-C)",
    "A2931": "AirPods Pro (2nd gen)",
    "A3050": "AirPods Pro 2 (Lightning)",
    "A3053": "AirPods 4",
    "A3056": "AirPods 4 ANC",
    "A3184": "AirPods Max (USB-C)",
    "A3064": "AirPods Pro 3",
}


NO_ANC_MODELS = {"A3053", "A2564"}  # AirPods 4, etc.


def model_name(model_id: str) -> str:
    return MODEL_MAP.get(model_id, f"Unknown ({model_id})")


def supports_anc(model_id: str) -> bool:
    return model_id not in NO_ANC_MODELS


def build_noise_control_packet(mode: int) -> bytes:
    return CTRL_HEADER + bytes([0x0D, mode, 0x00, 0x00, 0x00])


def parse_battery(payload: bytes) -> dict:
    if len(payload) < 1:
        return {}
    count = payload[0]
    bat = {}
    pos = 1
    for _ in range(count):
        if pos + 4 > len(payload):
            break
        comp = payload[pos]
        level = payload[pos + 2]
        side_map = {0x02: "right", 0x04: "left", 0x08: "case"}
        side = side_map.get(comp, f"0x{comp:02X}")
        bat[side] = level
        pos += 5
    return bat
