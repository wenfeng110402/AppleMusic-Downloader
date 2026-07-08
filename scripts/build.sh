#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# AppleMusic Downloader — PyInstaller build script
# Usage: bash scripts/build.sh <macos|windows|linux>
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

PLATFORM="${1:-}"
if [[ -z "$PLATFORM" ]]; then
  echo "Usage: $0 <macos|windows|linux>"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="AppleMusicDownloader"

echo "═══ Building $APP_NAME for $PLATFORM ═══"

# ── Step 1: Build frontend ─────────────────────────────────────
echo ">>> Building Next.js frontend..."
cd "$ROOT_DIR/src/fronted"

# Copy next.config.ts temporarily without rewrites for export build
cp next.config.ts next.config.ts.bak

npm install
npm run build

# Restore original next.config.ts (keeps rewrites for dev mode)
mv next.config.ts.bak next.config.ts

echo ">>> Frontend built:"
ls -la out/

# ── Step 2: Install Python deps + PyInstaller ──────────────────
echo ">>> Installing Python dependencies..."
cd "$ROOT_DIR"
pip install --upgrade pip
pip install -e ".[desktop]"
pip install pyinstaller

# ── Step 3: Run PyInstaller ────────────────────────────────────
echo ">>> Running PyInstaller..."

PYI_ARGS=(
  --name "$APP_NAME"
  --add-data "src/fronted/out:frontend_out"
  --add-data "$ROOT_DIR/icon.ico:."
  --clean
  --noconfirm
)

# Platform-specific flags
case "$PLATFORM" in
  macos)
    PYI_ARGS+=(--windowed --onedir)
    # macOS code signing identity (optional, set via env)
    if [[ -n "${APPLE_SIGN_IDENTITY:-}" ]]; then
      PYI_ARGS+=(--codesign-identity "$APPLE_SIGN_IDENTITY")
    fi
    # macOS notarization (optional)
    if [[ -n "${APPLE_NOTARIZATION_TEAM:-}" ]]; then
      PYI_ARGS+=(--osx-notarization-team-id "$APPLE_NOTARIZATION_TEAM")
    fi
    ;;
  windows)
    PYI_ARGS+=(--windowed --onefile)
    # Windows icon (optional)
    if [[ -f "$ROOT_DIR/icon.ico" ]]; then
      PYI_ARGS+=(--icon "$ROOT_DIR/icon.ico")
    fi
    ;;
  linux)
    PYI_ARGS+=(--onefile)
    # Linux icon (optional)
    if [[ -f "$ROOT_DIR/assets/icon.png" ]]; then
      PYI_ARGS+=(--icon "$ROOT_DIR/assets/icon.png")
    fi
    ;;
esac

pyinstaller "${PYI_ARGS[@]}" src/amdl/desktop_entry.py

# ── Step 4: Collect output ─────────────────────────────────────
echo ">>> Build complete! Output:"
DIST_DIR="$ROOT_DIR/dist"
mkdir -p "$DIST_DIR"

case "$PLATFORM" in
  macos)
    # onedir --windowed 产出 dist/AppleMusicDownloader.app
    SRC_BUNDLE="$ROOT_DIR/dist/$APP_NAME.app"
    DST_BUNDLE="$DIST_DIR/${APP_NAME}-macos-arm64.app"
    DMG_PATH="$DIST_DIR/${APP_NAME}-macos-arm64.dmg"
    if [[ -d "$SRC_BUNDLE" ]]; then
      mv "$SRC_BUNDLE" "$DST_BUNDLE"
    fi
    # Create DMG for distribution
    if command -v hdiutil &>/dev/null && [[ -d "$DST_BUNDLE" ]]; then
      hdiutil create -volname "$APP_NAME" -srcfolder "$DST_BUNDLE" -ov -format UDZO "$DMG_PATH"
      echo "DMG created: $DMG_PATH"
    fi
    ;;
  windows)
    EXE_PATH="$ROOT_DIR/dist/$APP_NAME.exe"
    if [[ -f "$EXE_PATH" ]]; then
      mv "$EXE_PATH" "$DIST_DIR/${APP_NAME}-windows-x64.exe"
    fi
    ;;
  linux)
    BIN_PATH="$ROOT_DIR/dist/$APP_NAME"
    if [[ -f "$BIN_PATH" ]]; then
      mv "$BIN_PATH" "$DIST_DIR/${APP_NAME}-linux-x64"
    fi
    ;;
esac

echo "═══ Done! Artifacts in $DIST_DIR ═══"
ls -lh "$DIST_DIR"
