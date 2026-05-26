import logging

log = logging.getLogger("airpux.battery")


class BatteryMonitor:
    def __init__(self):
        self.left: int | None = None
        self.right: int | None = None
        self.case: int | None = None

    def update(self, data: dict):
        changed = False
        for key in ("left", "right", "case"):
            val = data.get(key)
            if val is not None and getattr(self, key) != val:
                setattr(self, key, val)
                changed = True
        if changed:
            log.info(
                "Battery updated  L:%s%%  R:%s%%  Case:%s%%",
                self.left, self.right, self.case,
            )

    def summary(self) -> str:
        parts = []
        if self.left is not None:
            parts.append(f"L:{self.left}%")
        if self.right is not None:
            parts.append(f"R:{self.right}%")
        if self.case is not None:
            parts.append(f"Case:{self.case}%")
        return " | ".join(parts) if parts else "No data"
