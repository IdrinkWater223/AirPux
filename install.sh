#!/usr/bin/env bash
set -euo pipefail

APP_NAME="airpux"
APP_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
DESKTOP_DIR="$HOME/.local/share/applications"
AUTOSTART_DIR="$HOME/.config/autostart"

echo "==> Installing $APP_NAME..."

# --- Check python3 ---
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install it first."
    exit 1
fi

# --- Install Python dependencies ---
echo "--> Installing Python dependencies..."
if command -v pip3 &>/dev/null; then
    pip3 install --user --upgrade -r requirements.txt 2>&1 || {
        echo "pip install failed. Trying venv fallback..."
        python3 -m venv "$APP_DIR/venv"
        "$APP_DIR/venv/bin/pip" install --upgrade -r requirements.txt
        VENV=1
    }
elif python3 -m pip --version &>/dev/null; then
    python3 -m pip install --user --upgrade -r requirements.txt 2>&1 || {
        echo "pip install failed. Trying venv fallback..."
        python3 -m venv "$APP_DIR/venv"
        "$APP_DIR/venv/bin/pip" install --upgrade -r requirements.txt
        VENV=1
    }
else
    echo "pip not found. Creating venv..."
    python3 -m venv "$APP_DIR/venv"
    "$APP_DIR/venv/bin/pip" install --upgrade -r requirements.txt
    VENV=1
fi

# --- Copy app files ---
echo "--> Copying app files..."
mkdir -p "$APP_DIR"
cp -r bluetooth features ui icons main.py "$APP_DIR/"
mkdir -p "$ICON_DIR"
cp icons/airpux.svg "$ICON_DIR/"

# --- Create launcher ---
mkdir -p "$BIN_DIR"
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

# Warn if ~/.local/bin not in PATH
case ":$PATH:" in
    *:"$BIN_DIR":*) ;;
    *)
        echo "NOTE: Add $BIN_DIR to your PATH or run:"
        echo "  export PATH=\"\$PATH:$BIN_DIR\""
        echo "  (add that line to ~/.bashrc or ~/.zshrc)"
        ;;
esac

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

# --- Desktop detection ---
DE="other"
if [ "$XDG_CURRENT_DESKTOP" = "GNOME" ] || [ "$XDG_CURRENT_DESKTOP" = "gnome" ]; then
    DE="GNOME"
elif [ "$XDG_CURRENT_DESKTOP" = "KDE" ] || [ "$XDG_CURRENT_DESKTOP" = "KDE" ]; then
    DE="KDE"
fi

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
        echo ""
        echo "  Then restart GNOME Shell (Alt+F2, 'r', Enter)"
        echo "============================================"
        ;;
    KDE)
        echo ""
        echo "============================================"
        echo "  KDE Plasma detected — tray should work"
        echo "  out of the box. If hidden, check your"
        echo "  system tray settings and pin AirPux."
        echo "============================================"
        ;;
    *)
        if [ -n "${XDG_CURRENT_DESKTOP:-}" ]; then
            echo ""
            echo "============================================"
            echo "  Desktop: $XDG_CURRENT_DESKTOP"
            echo "  If the tray icon doesn't appear, your DE"
            echo "  may need an AppIndicator extension."
            echo "============================================"
        fi
        ;;
esac

echo ""
echo "==> Done!"
echo "    Run: airpux"
echo "    Or find AirPux in your app launcher."
echo ""
echo "    Uninstall:"
echo "      rm -rf $APP_DIR $BIN_DIR/airpux \\"
echo "        $ICON_DIR/airpux.svg $DESKTOP_DIR/airpux.desktop \\"
echo "        $AUTOSTART_DIR/airpux.desktop"
