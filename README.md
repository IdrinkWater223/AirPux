# AirPux

Native AirPods manager for Linux — battery levels, ear detection, and ANC in your system tray.

## Quick Install

```bash
git clone https://github.com/IdrinkWater223/AirPux.git
cd AirPux
./install.sh
```

That's it. The script will:

- Install Python dependencies (`PyQt6`, `qasync`, `dasbus`)
- Copy app files to `~/.local/share/airpux/`
- Create a launcher at `~/.local/bin/airpux`
- Add a desktop entry so it appears in your app launcher
- Enable autostart so it runs on login

If `pip install` fails (missing pip or venv), install the dependencies manually:

```bash
# Debian/Ubuntu
sudo apt install python3-pip python3-venv

# Fedora
sudo dnf install python3-pip

# Arch
sudo pacman -S python-pip
```

Then rerun `./install.sh`.

## Manual Install

```bash
pip install --user -r requirements.txt
python main.py
```

## GNOME Users

GNOME hides system tray icons by default. Run this before launching:

```bash
sudo apt install gnome-shell-extension-appindicator   # Debian/Ubuntu
sudo dnf install gnome-shell-extension-appindicator   # Fedora
sudo pacman -S gnome-shell-extension-appindicator     # Arch
```

Then restart GNOME Shell (`Alt+F2`, type `r`, `Enter`) and enable the extension in the Extensions app.

KDE Plasma works out of the box.

## Usage

1. **Launch** — run `airpux` or click AirPux in your app launcher
2. **Set MAC** — right-click the tray icon → Settings → paste your AirPods address
3. **Done** — battery, ear detection, and ANC appear in the tray

### Finding your MAC

```bash
bluetoothctl devices
# Copy the address (e.g., 30:7A:D2:5F:5D:8F)
```

### Disable ANC (non-ANC AirPods)

Open Settings and uncheck "Device supports ANC", or edit `~/.config/airpux/config.json`:

```json
{"mac_address": "30:7A:D2:5F:5D:8F", "has_anc": false}
```

## Features

| Feature | What it does |
|---|---|
| Battery | Shows L / R / Case % in the tray |
| Ear detection | Auto-pauses media when you remove an AirPod, resumes when inserted |
| ANC control | Click to cycle Off → ANC → Transparency → Adaptive |
| Auto-connect | Connects automatically on launch |

## Supported Devices

Any AirPods that speak AAP over L2CAP:

- AirPods Pro 2 (confirmed)
- AirPods 4 (confirmed)
- AirPods Pro 1, AirPods 4 ANC, AirPods Max (likely)

**Not supported**: AirPods 1st/2nd gen (no AAP protocol).

## How It Works

AirPods use **Apple Accessory Protocol (AAP)** over L2CAP PSM 0x1001. AirPux opens a raw Bluetooth socket, performs a handshake, and parses status packets directly — no GATT or RFCOMM needed.

Audio still goes through the system's Bluetooth A2DP profile. AirPux only reads status data.

## Uninstall

```bash
rm -rf ~/.local/share/airpux ~/.local/bin/airpux \
  ~/.local/share/icons/hicolor/scalable/apps/airpux.svg \
  ~/.local/share/applications/airpux.desktop \
  ~/.config/autostart/airpux.desktop
```

## License

promised to me 3000 years ago
