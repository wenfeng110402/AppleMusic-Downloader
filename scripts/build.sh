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

# ── Step 2: Download N_m3u8DL-RE for bundling (best-effort) ──
echo ">>> Downloading N_m3u8DL-RE for $PLATFORM..."
BIN_DIR="$ROOT_DIR/bin"
mkdir -p "$BIN_DIR"
BINARY_FLAG=""

# Temporarily disable set -e so a failed download doesn't kill the build.
# The binary will be auto-downloaded at runtime via dependency_manager.py.
set +e
set +o pipefail

case "$PLATFORM" in
  windows)
    DEST="$BIN_DIR/N_m3u8DL-RE.exe"
    if [[ ! -f "$DEST" ]]; then
      curl -#fL "https://pub-e4955324bbd043d79465a5231bec51f6.r2.dev/N_m3u8DL-RE.exe" -o "$DEST" 2>&1
    fi
    if [[ -f "$DEST" ]]; then
      BINARY_FLAG="bin/N_m3u8DL-RE.exe;bin"
    fi
    ;;
  macos)
    DEST="$BIN_DIR/N_m3u8DL-RE"
    if [[ ! -f "$DEST" ]]; then
      # R2 only has Windows exe — macOS goes straight to GitHub
      GHLATEST=$(curl -sL https://api.github.com/repos/nilaoda/N_m3u8DL-RE/releases/latest)
      GHURL=$(echo "$GHLATEST" | grep browser_download_url | grep -E 'macos-(arm64|x64)\.tar\.gz' | head -1 | cut -d'"' -f4)
      if [[ -n "$GHURL" ]]; then
        curl -#fL "$GHURL" -o "/tmp/N_m3u8DL-RE.tar.gz" 2>&1
      fi
      if [[ -f "/tmp/N_m3u8DL-RE.tar.gz" ]]; then
        tar xzf "/tmp/N_m3u8DL-RE.tar.gz" -C "$BIN_DIR" 2>/dev/null
        rm -f "/tmp/N_m3u8DL-RE.tar.gz"
      fi
    fi
    if [[ -f "$DEST" ]]; then
      chmod +x "$DEST"
      BINARY_FLAG="bin/N_m3u8DL-RE:bin"
    fi
    ;;
  linux)
    DEST="$BIN_DIR/N_m3u8DL-RE"
    if [[ ! -f "$DEST" ]]; then
      GHLATEST=$(curl -sL https://api.github.com/repos/nilaoda/N_m3u8DL-RE/releases/latest)
      GHURL=$(echo "$GHLATEST" | grep browser_download_url | grep 'linux-x64.tar.gz' | head -1 | cut -d'"' -f4)
      if [[ -n "$GHURL" ]]; then
        curl -#fL "$GHURL" -o "/tmp/N_m3u8DL-RE.tar.gz" 2>&1
      fi
      if [[ -f "/tmp/N_m3u8DL-RE.tar.gz" ]]; then
        tar xzf "/tmp/N_m3u8DL-RE.tar.gz" -C "$BIN_DIR" 2>/dev/null
        rm -f "/tmp/N_m3u8DL-RE.tar.gz"
      fi
    fi
    if [[ -f "$DEST" ]]; then
      chmod +x "$DEST"
      BINARY_FLAG="bin/N_m3u8DL-RE:bin"
    fi
    ;;
esac

set -o pipefail
set -e

if [[ -n "$BINARY_FLAG" ]]; then
  echo ">>> N_m3u8DL-RE bundled: $(ls -lh "$BIN_DIR"/N_m3u8DL-RE* 2>/dev/null | awk '{print $5, $NF}')"
else
  echo ">>> N_m3u8DL-RE skipped (will be auto-downloaded at runtime)"
fi

# ── Step 3: Install Python deps + PyInstaller ──────────────────
echo ">>> Installing Python dependencies..."
cd "$ROOT_DIR"
pip install --upgrade pip
pip install -e ".[desktop]"
pip install pyinstaller

# ── Step 4: Run PyInstaller ────────────────────────────────────
echo ">>> Running PyInstaller..."

PYI_ARGS=(
  --name "$APP_NAME"
  --add-data "src/fronted/out:frontend_out"
  --add-data "$ROOT_DIR/icon.ico:."
  --add-data "$ROOT_DIR/icon.png:."
  --add-data "$ROOT_DIR/icon.icns:."
  --clean
  --noconfirm
)

# Only add --add-binary if we successfully downloaded N_m3u8DL-RE
if [[ -n "$BINARY_FLAG" ]]; then
  PYI_ARGS+=(--add-binary "$BINARY_FLAG")
fi

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
    if [[ -f "$ROOT_DIR/icon.ico" ]]; then
      PYI_ARGS+=(--icon "$ROOT_DIR/icon.ico")
    fi
    ;;
  linux)
    PYI_ARGS+=(--onefile)
    if [[ -f "$ROOT_DIR/icon.png" ]]; then
      PYI_ARGS+=(--icon "$ROOT_DIR/icon.png")
    fi
    ;;
esac

pyinstaller "${PYI_ARGS[@]}" src/amdl/desktop_entry.py

# ── Step 5: Collect output ─────────────────────────────────────
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
      # 设置 macOS 图标（.icns）
      if [[ -f "$ROOT_DIR/icon.icns" ]]; then
        cp "$ROOT_DIR/icon.icns" "$DST_BUNDLE/Contents/Resources/"
        plist="$DST_BUNDLE/Contents/Info.plist"
        /usr/libexec/PlistBuddy -c "Set :CFBundleIconFile icon.icns" "$plist" 2>/dev/null || true
      fi
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
