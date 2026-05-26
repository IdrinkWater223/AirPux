import logging

from bluetooth.protocol import ANC_LABELS, NOISE_MODE_OFF, NOISE_MODE_ANC, NOISE_MODE_TRANSPARENCY

log = logging.getLogger("airpux.anc")


class ANCModeController:
    def __init__(self, aap_client):
        self._client = aap_client
        self._mode: int | None = None

    @property
    def mode(self) -> int | None:
        return self._mode

    def update(self, mode: int):
        if self._mode != mode:
            self._mode = mode
            label = ANC_LABELS.get(mode, f"Unknown ({mode})")
            log.info("ANC mode changed to: %s", label)

    def cycle(self):
        if self._mode is None:
            return
        next_map = {NOISE_MODE_OFF: NOISE_MODE_ANC, NOISE_MODE_ANC: NOISE_MODE_TRANSPARENCY, NOISE_MODE_TRANSPARENCY: NOISE_MODE_OFF}
        next_mode = next_map.get(self._mode, NOISE_MODE_OFF)
        self.set_mode(next_mode)

    def set_mode(self, mode: int):
        async def _do():
            log.info("Setting ANC mode to: %s (0x%02X)", ANC_LABELS.get(mode, "?"), mode)
            await self._client.set_noise_control(mode)

        import asyncio
        asyncio.ensure_future(_do())

    @staticmethod
    def label(mode: int) -> str:
        return ANC_LABELS.get(mode, f"Unknown (0x{mode:02X})")
