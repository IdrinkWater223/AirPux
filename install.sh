#!/usr/bin/env bash
set -euo pipefail

APP_NAME="airpux"
APP_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
DESKTOP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

echo "==> Installing $APP_NAME..."

# --- Detect DE ---
if [ "$XDG_CURRENT_DESKTOP" = "GNOME" ]; then
    DE="GNOME"
elif [ "$XDG_CURRENT_DESKTOP" = "KDE" ]; then
    DE="KDE"
else
    DE="other"
fi

# --- Install Python dependencies ---
echo "--> Installing Python dependencies..."
pip3 install --user --upgrade -r requirements.txt 2>/dev/null || {
    python3 -m venv "$APP_DIR/venv"
    "$APP_DIR/venv/bin/pip" install --upgrade -r requirements.txt
    VENV=1
}

# --- Copy app files ---
echo "--> Copying app files..."
mkdir -p "$APP_DIR"
cp -r bluetooth features ui icons main.py "$APP_DIR/"
mkdir -p "$ICON_DIR"
cp icons/airpux.svg "$ICON_DIR/"

# --- Create launcher ---
if [ -n "${VENV:-}" ]; then
    cat > "$BIN_DIR/airpux" << 'LAUNCHER'
#!/usr/bin/env bash
DIR="$HOME/.local/share/airpux"
cd "$DIR" && exec "$DIR/venv/bin/python" main.py "$@"
LAUNCHER
else
    cat > "$BIN_DIR/airpux" << 'LAUNCHER'
#!/usr/bin/env bash
DIR="$HOME/.local/share/airpux"
cd "$DIR" && exec python3 main.py "$@"
LAUNCHER
fi
chmod +x "$BIN_DIR/airpux"

# --- Create .desktop file ---
echo "--> Creating desktop entry..."
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/airpux.desktop" << DESKTOP
[Desktop Entry]
Name=AirPux
Comment=AirPods Manager for Linux
Exec=$BIN_DIR/airpux
Icon=airpux
Terminal=false
Type=Application
Categories=Utility;Audio;
StartupNotify=false
DESKTOP

# --- Autostart ---
echo "--> Setting up autostart..."
mkdir -p "$AUTOSTART_DIR"
cp "$DESKTOP_DIR/airpux.desktop" "$AUTOSTART_DIR/"

# --- DE-specific instructions ---
case "$DE" in
    GNOME)
        echo ""
        echo "============================================"
        echo "  GNOME detected!"
        echo ""
        echo "  GNOME hides tray icons by default."
        echo "  Install the AppIndicator extension:"
        echo ""
        echo "    sudo apt install gnome-shell-extension-appindicator"
        echo "    # or your distro's equivalent"
        echo ""
        echo "  Then restart GNOME Shell (Alt+F2, 'r', Enter)"
        echo "  and enable the extension in Extensions app."
        echo "============================================"
        ;;
    KDE)
        echo ""
        echo "============================================"
        echo "  KDE Plasma detected — tray should work"
        echo "  out of the box."
        echo ""
        echo "  If the icon is hidden, check the tray"
        echo "  settings and pin AirPux."
        echo "============================================"
        ;;
    *)
        echo ""
        echo "============================================"
        echo "  Desktop: $XDG_CURRENT_DESKTOP"
        echo "  If the tray icon doesn't appear, your DE"
        echo "  may need an AppIndicator/tray extension."
        echo "============================================"
        ;;
esac

echo ""
echo "==> Done! Run 'airpux' to start."
echo "    (or find AirPux in your app launcher)"
echo "    Restart or log out if the icon cache needs updating."
echo ""
echo "    To uninstall: rm -rf $APP_DIR $BIN_DIR/airpux \\
        $ICON_DIR/airpux.svg $DESKTOP_DIR/airpux.desktop \\
        $AUTOSTART_DIR/airpux.desktop"
