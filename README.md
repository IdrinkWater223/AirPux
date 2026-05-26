# AirPux
Native AirPods manager for Linux — battery levels, ear detection, and ANC in your system tray.
I lowkey vibe coded it, along with using ai for this readme, but if it works dont fix it
## Installation
### Dependencies
| Package | Install command |
|---|---|
| Python 3.10+ | pre-installed on most distros |
| PyQt6 | `pip install PyQt6` |
| qasync | `pip install qasync` |
| dasbus | `pip install dasbus` |
### Quick install
```bash
git clone https://github.com/YOUR_USER/airpux.git
cd airpux
chmod +x install.sh
./install.sh
```
This installs dependencies, copies files to `~/.local/share/airpux`, creates a desktop entry, and sets up autostart.
### Manual install
```bash
pip install --user -r requirements.txt
python main.py
```
### KDE Plasma
Works out of the box. The tray icon appears natively.
### GNOME
GNOME hides tray icons by default. You need the **AppIndicator extension**:
```bash
# Debian/Ubuntu
sudo apt install gnome-shell-extension-appindicator
# Fedora
sudo dnf install gnome-shell-extension-appindicator
# Arch
sudo pacman -S gnome-shell-extension-appindicator
```
Restart GNOME Shell (`Alt+F2`, type `r`, `Enter`) and enable the extension in the Extensions app.
## Usage
1. **Launch** — run `airpux` or find it in your app launcher
2. **Configure** — right-click the tray icon → Settings → enter your AirPods MAC
3. **Auto-detect** — if no MAC is saved, AirPux finds already-connected AirPods automatically
### Finding your MAC
```bash
bluetoothctl devices
# Copy the address, e.g. 30:7A:D2:5F:5D:8F
```
### Configuration
`~/.config/airpux/config.json`:
```json
{
  "mac_address": "30:7A:D2:5F:5D:8F",
  "has_anc": true
}
```
Set `"has_anc": false` to hide ANC controls (AirPods 4, etc.).
## Features
| Feature | Description |
|---|---|
| Battery | L / R / Case percentages in tray |
| Ear detection | Auto pause/play media on remove/insert |
| ANC control | Cycle Off / ANC / Transparency / Adaptive |
| Auto-connect | Reconnects on launch |
## Supported devices
Any AirPods that speak AAP over L2CAP. Confirmed:
- AirPods Pro 2 (A3050)
- AirPods 4 (A3053)
Likely compatible with all AirPods Pro, AirPods 4 ANC, AirPods Max, and select Beats.
**Not supported**: AirPods 1st/2nd gen (no AAP).
## How it works
AirPods use **Apple Accessory Protocol (AAP)** over L2CAP PSM 0x1001. The app opens a raw Bluetooth socket, performs a handshake, and parses status packets directly — no GATT or RFCOMM involved.
Audio uses the system's A2DP profile; AirPux only reads status data.
## License
promised to me 3000 years ago
