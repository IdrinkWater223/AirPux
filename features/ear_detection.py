import logging

log = logging.getLogger("airpux.ear_detection")


class EarDetectionHandler:
    def __init__(self, media_control):
        self._media = media_control
        self._left_in = False
        self._right_in = False

    def update(self, data: dict):
        left = data.get("left", False)
        right = data.get("right", False)

        any_in = left or right
        was_any_in = self._left_in or self._right_in

        if any_in and not was_any_in:
            log.info("AirPods inserted — resuming playback")
            self._media.play()
        elif was_any_in and not any_in:
            log.info("AirPods removed — pausing playback")
            self._media.pause()

        self._left_in = left
        self._right_in = right
