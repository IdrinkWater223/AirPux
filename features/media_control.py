import logging

from dasbus.connection import SessionMessageBus

MPRIS2_PREFIX = "org.mpris.MediaPlayer2"
MPRIS2_PATH = "/org/mpris/MediaPlayer2"
MPRIS2_PLAYER = "org.mpris.MediaPlayer2.Player"

log = logging.getLogger("airpux.media")


class MediaControl:
    def __init__(self):
        self._bus = SessionMessageBus()
        self._player_name: str | None = None

    def _find_player(self) -> str | None:
        try:
            names = self._bus.get_proxy(
                "org.freedesktop.DBus", "/org/freedesktop/DBus"
            ).ListNames()
            for name in names:
                if name.startswith(MPRIS2_PREFIX) and name != f"{MPRIS2_PREFIX}.playerctld":
                    return name
        except Exception as e:
            log.warning("Could not list DBus names: %s", e)
        return None

    def play(self):
        player = self._find_player()
        if not player:
            log.debug("No MPRIS player found for Play")
            return
        try:
            proxy = self._bus.get_proxy(player, MPRIS2_PATH)
            proxy.Play()
            log.info("Sent Play to %s", player)
        except Exception as e:
            log.warning("MPRIS Play failed: %s", e)

    def pause(self):
        player = self._find_player()
        if not player:
            log.debug("No MPRIS player found for Pause")
            return
        try:
            proxy = self._bus.get_proxy(player, MPRIS2_PATH)
            proxy.Pause()
            log.info("Sent Pause to %s", player)
        except Exception as e:
            log.warning("MPRIS Pause failed: %s", e)

    def play_pause(self):
        player = self._find_player()
        if not player:
            return
        try:
            proxy = self._bus.get_proxy(player, MPRIS2_PATH)
            proxy.PlayPause()
            log.info("Sent PlayPause to %s", player)
        except Exception as e:
            log.warning("MPRIS PlayPause failed: %s", e)

    def next_track(self):
        player = self._find_player()
        if not player:
            return
        try:
            proxy = self._bus.get_proxy(player, MPRIS2_PATH)
            proxy.Next()
        except Exception as e:
            log.warning("MPRIS Next failed: %s", e)

    def previous_track(self):
        player = self._find_player()
        if not player:
            return
        try:
            proxy = self._bus.get_proxy(player, MPRIS2_PATH)
            proxy.Previous()
        except Exception as e:
            log.warning("MPRIS Previous failed: %s", e)
