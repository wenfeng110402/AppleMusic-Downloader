#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
# AppleMusic Downloader — PyInstaller build script
# Usage: bash scripts/build.sh <macos|macos-arm64|macos-x64|windows|linux>
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

PLATFORM="${1:-}"
if [[ -z "$PLATFORM" ]]; then
  echo "Usage: $0 <macos|macos-arm64|macos-x64|windows|linux>"
  exit 1
fi

MAC_ARCH=""
case "$PLATFORM" in
  macos)
    case "$(uname -m)" in
      arm64) MAC_ARCH="arm64" ;;
      x86_64) MAC_ARCH="x64" ;;
      *)
        echo "Unsupported macOS architecture: $(uname -m)"
        exit 1
        ;;
    esac
    ;;
  macos-arm64)
    PLATFORM="macos"
    MAC_ARCH="arm64"
    ;;
  macos-x64)
    PLATFORM="macos"
    MAC_ARCH="x64"
    ;;
  windows|linux) ;;
  *)
    echo "Unsupported platform: $PLATFORM"
    echo "Usage: $0 <macos|macos-arm64|macos-x64|windows|linux>"
    exit 1
    ;;
esac

if [[ "$PLATFORM" == "macos" ]]; then
  HOST_MACHINE="$(uname -m)"
  if [[ "$MAC_ARCH" == "arm64" && "$HOST_MACHINE" != "arm64" ]]; then
    echo "macos-arm64 build requires an arm64 host (got $HOST_MACHINE)"
    exit 1
  fi
  if [[ "$MAC_ARCH" == "x64" && "$HOST_MACHINE" != "x86_64" ]]; then
    echo "macos-x64 build requires an x86_64 host (got $HOST_MACHINE)"
    exit 1
  fi
fi

# On Windows (Git Bash), pwd returns MSYS path like /d/a/... which
# PyInstaller (Python) cannot resolve.  Use pwd -W for native paths.
if [[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* ]]; then
  ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd -W)"
else
  ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
fi
APP_NAME="AppleMusicDownloader"

if [[ "$PLATFORM" == "macos" ]]; then
  echo "═══ Building $APP_NAME for macos-$MAC_ARCH ═══"
else
  echo "═══ Building $APP_NAME for $PLATFORM ═══"
fi

# ── Step 1: Build frontend ─────────────────────────────────────
echo ">>> Building Next.js frontend..."
cd "$ROOT_DIR/src/frontend"

# Copy next.config.ts temporarily without rewrites for export build
cp next.config.ts next.config.ts.bak

if [[ "${AMDL_SKIP_FRONTEND_INSTALL:-0}" == "1" ]]; then
  mkdir -p out
  echo ">>> Skipping npm ci (AMDL_SKIP_FRONTEND_INSTALL=1)"
else
  npm ci
fi

if [[ "${AMDL_SKIP_FRONTEND_BUILD:-0}" == "1" ]]; then
  mkdir -p out
  echo ">>> Skipping Next.js build (AMDL_SKIP_FRONTEND_BUILD=1)"
else
  npm run build
fi

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
    DEST="$BIN_DIR/N_m3u8DL-RE-$MAC_ARCH"
    if [[ ! -f "$DEST" ]]; then
      # R2 only has Windows exe — macOS goes straight to GitHub
      GHLATEST=$(curl -sL https://api.github.com/repos/nilaoda/N_m3u8DL-RE/releases/latest)
      GHURL=$(echo "$GHLATEST" | grep browser_download_url | grep -E "macos-${MAC_ARCH}\.tar\.gz" | head -1 | cut -d'"' -f4)
      if [[ -n "$GHURL" ]]; then
        curl -#fL "$GHURL" -o "/tmp/N_m3u8DL-RE.tar.gz" 2>&1
      fi
      if [[ -f "/tmp/N_m3u8DL-RE.tar.gz" ]]; then
        tar xzf "/tmp/N_m3u8DL-RE.tar.gz" -C "$BIN_DIR" 2>/dev/null
        rm -f "/tmp/N_m3u8DL-RE.tar.gz"
        # GitHub tar is N_m3u8DL-RE/N_m3u8DL-RE (subdir) — move file up
        if [[ -f "$BIN_DIR/N_m3u8DL-RE/N_m3u8DL-RE" ]]; then
          mv "$BIN_DIR/N_m3u8DL-RE/N_m3u8DL-RE" "$DEST"
          rmdir "$BIN_DIR/N_m3u8DL-RE" 2>/dev/null || true
        fi
      fi
    fi
    if [[ -f "$DEST" ]]; then
      # Keep the bundled/runtime path stable across architectures.
      BUNDLED_DEST="$BIN_DIR/N_m3u8DL-RE"
      cp "$DEST" "$BUNDLED_DEST"
      chmod +x "$BUNDLED_DEST"
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
        # GitHub tar is N_m3u8DL-RE/N_m3u8DL-RE (subdir) — move file up
        if [[ -f "$BIN_DIR/N_m3u8DL-RE/N_m3u8DL-RE" ]]; then
          mv "$BIN_DIR/N_m3u8DL-RE/N_m3u8DL-RE" "$DEST"
          rmdir "$BIN_DIR/N_m3u8DL-RE" 2>/dev/null || true
        fi
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
if [[ "${AMDL_SKIP_PYTHON_INSTALL:-0}" == "1" ]]; then
  echo ">>> Skipping Python dependency install (AMDL_SKIP_PYTHON_INSTALL=1)"
else
  python -m pip install --upgrade pip
  python -m pip install -e ".[desktop]"
  python -m pip install pyinstaller
fi

# ── Step 4: Run PyInstaller ────────────────────────────────────
echo ">>> Running PyInstaller..."

# PyInstaller --add-data / --add-binary separator is platform-dependent:
#   Unix: ":"   Windows: ";"
if [[ "$PLATFORM" == "windows" ]]; then
  SEP=";"
else
  SEP=":"
fi

PYI_ARGS=(
  --name "$APP_NAME"
  --add-data "src/frontend/out${SEP}frontend_out"
  --add-data "icon.ico${SEP}."
  --add-data "icon.png${SEP}."
  --add-data "icon.icns${SEP}."
  --collect-all gamdl
  --collect-binaries gamdl
  --collect-all yt_dlp
  --collect-all pywebview
  --hidden-import amdl.dependency_manager
  --hidden-import gamdl._ammuxer
  --hidden-import gamdl.api.apple_music
  --hidden-import gamdl.downloader.amdecrypt
  --hidden-import gamdl.downloader.song
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
    PYI_ARGS+=(--windowed --onedir --codesign-identity "-")
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
    if [[ -f "icon.ico" ]]; then
      PYI_ARGS+=(--icon "icon.ico")
    fi
    ;;
  linux)
    PYI_ARGS+=(--onefile)
    if [[ -f "icon.png" ]]; then
      PYI_ARGS+=(--icon "icon.png")
    fi
    ;;
esac

# On Windows (Git Bash/MSYS), disable automatic POSIX→Windows path conversion
# for arguments passed to native Windows programs (pyinstaller.exe).
# Without this, MSYS mangles paths like D:/a/... into \d\a\... (invalid).
if [[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* ]]; then
  export MSYS_NO_PATHCONV=1
fi

if [[ "${AMDL_SKIP_PYINSTALLER:-0}" == "1" ]]; then
  mkdir -p "$ROOT_DIR/dist/$APP_NAME.app/Contents/MacOS" "$ROOT_DIR/dist/$APP_NAME.app/Contents/Resources"
  printf '#!/bin/sh\nexit 0\n' > "$ROOT_DIR/dist/$APP_NAME.app/Contents/MacOS/$APP_NAME"
  chmod +x "$ROOT_DIR/dist/$APP_NAME.app/Contents/MacOS/$APP_NAME"
  cp "$ROOT_DIR/icon.icns" "$ROOT_DIR/dist/$APP_NAME.app/Contents/Resources/" 2>/dev/null || true
  cp "$ROOT_DIR/src/frontend/out/index.html" "$ROOT_DIR/dist/$APP_NAME.app/Contents/Resources/index.html" 2>/dev/null || true
  cat > "$ROOT_DIR/dist/$APP_NAME.app/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>CFBundleShortVersionString</key><string>0.0.0</string><key>CFBundleVersion</key><string>0.0.0</string></dict></plist>
PLIST
  echo ">>> Skipping PyInstaller (AMDL_SKIP_PYINSTALLER=1)"
else
  pyinstaller "${PYI_ARGS[@]}" src/amdl/desktop_entry.py
fi

# ── Step 5: Collect output ─────────────────────────────────────
echo ">>> Build complete! Output:"
DIST_DIR="$ROOT_DIR/dist"
mkdir -p "$DIST_DIR"

case "$PLATFORM" in
  macos)
    # onedir --windowed 产出 dist/AppleMusicDownloader.app
    SRC_BUNDLE="$ROOT_DIR/dist/$APP_NAME.app"
    DST_BUNDLE="$DIST_DIR/${APP_NAME}-macos-${MAC_ARCH}.app"
    DMG_PATH="$DIST_DIR/${APP_NAME}-macos-${MAC_ARCH}.dmg"
    if [[ -d "$SRC_BUNDLE" ]]; then
      mv "$SRC_BUNDLE" "$DST_BUNDLE"
      # 设置 macOS 图标（.icns）
      if [[ -f "$ROOT_DIR/icon.icns" ]]; then
        cp "$ROOT_DIR/icon.icns" "$DST_BUNDLE/Contents/Resources/"
        plist="$DST_BUNDLE/Contents/Info.plist"
        /usr/libexec/PlistBuddy -c "Set :CFBundleIconFile icon.icns" "$plist" 2>/dev/null || true
      fi
      # Keep the bundle metadata in sync with the single application version source.
      APP_VERSION="$(sed -n 's/^__version__ = "\(.*\)"/\1/p' "$ROOT_DIR/src/amdl/__init__.py")"
      if [[ -n "$APP_VERSION" ]]; then
        /usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $APP_VERSION" "$DST_BUNDLE/Contents/Info.plist" 2>/dev/null || true
        /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $APP_VERSION" "$DST_BUNDLE/Contents/Info.plist" 2>/dev/null || true
      fi
      # 清除框架签名冲突（Anaconda Python 自带 Team ID 跟 ad-hoc 冲突）
      if [[ -d "$DST_BUNDLE/Contents/Frameworks/Python.framework" ]]; then
        codesign --remove-signature "$DST_BUNDLE/Contents/Frameworks/Python.framework" 2>/dev/null || true
      fi
      # 统一 ad-hoc 重签整个 .app
      codesign --deep --force --sign - "$DST_BUNDLE" 2>/dev/null || true
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
