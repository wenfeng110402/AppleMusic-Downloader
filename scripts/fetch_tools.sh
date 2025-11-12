#!/usr/bin/env bash
set -euo pipefail

# fetch_tools.sh <platform_dir> <platform> <arch>
# Expects environment variables (recommended to set via GitHub Actions secrets):
#   FFMPEG_URL, MP4DECRYPT_URL, N_M3U8DL_RE_URL
# If any are missing the script will print instructions and exit non-zero.

PLATFORM_DIR="$1"
PLATFORM="$2"
ARCH="$3"

mkdir -p "$PLATFORM_DIR"

echo "Fetching tools into $PLATFORM_DIR for $PLATFORM/$ARCH"
#!/usr/bin/env bash
set -euo pipefail

# fetch_tools.sh <platform_dir> <platform> <arch>
# Expects environment variables (recommended to set via GitHub Actions secrets):
#   FFMPEG_URL, MP4DECRYPT_URL, N_M3U8DL_RE_URL
# If any are missing the script will print instructions and exit non-zero.

PLATFORM_DIR="$1"
PLATFORM="$2"
ARCH="$3"

mkdir -p "$PLATFORM_DIR"

echo "Fetching tools into $PLATFORM_DIR for $PLATFORM/$ARCH"

if [ -z "${FFMPEG_URL:-}" ]; then
  echo "ERROR: FFMPEG_URL is not set. Please set it as an env var or GitHub secret."
  echo "Example (linux x86_64): https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
  exit 2
fi

if [ -z "${MP4DECRYPT_URL:-}" ]; then
  echo "ERROR: MP4DECRYPT_URL is not set. Please set it as an env var or GitHub secret."
  echo "Example (Bento4): https://github.com/axiomatic-systems/Bento4/releases/download/...(zip)"
  exit 2
fi

if [ -z "${N_M3U8DL_RE_URL:-}" ]; then
  echo "ERROR: N_M3U8DL_RE_URL is not set. Please set it as an env var or GitHub secret."
  echo "Example: https://github.com/nilaoda/N_m3u8DL-RE/releases/download/xxx/N_m3u8DL-RE.zip"
  exit 2
fi

tmpdir=$(mktemp -d)
cleanup() { rm -rf "$tmpdir"; }
trap cleanup EXIT

echo "Downloading ffmpeg from $FFMPEG_URL"
fffile="$tmpdir/ff"
curl -L "$FFMPEG_URL" -o "$fffile"

# try to extract known archive types
if file "$fffile" | grep -q "gzip\|XZ\|tar"; then
  tar -x -f "$fffile" -C "$tmpdir" || true
elif file "$fffile" | grep -q "Zip"; then
  unzip -q "$fffile" -d "$tmpdir"
else
  # if direct binary
  chmod +x "$fffile"
  mv "$fffile" "$PLATFORM_DIR/ffmpeg"
fi

# try to find ffmpeg binary in extracted files
found_ff=""
while IFS= read -r -d '' f; do
  if [ "$(basename "$f")" = "ffmpeg" ] || [ "$(basename "$f")" = "ffmpeg.exe" ]; then
    found_ff="$f"
    break
  fi
done < <(find "$tmpdir" -type f -print0)

if [ -n "$found_ff" ]; then
  cp "$found_ff" "$PLATFORM_DIR/"
  chmod +x "$PLATFORM_DIR/$(basename "$found_ff")"
  echo "ffmpeg placed: $PLATFORM_DIR/$(basename "$found_ff")"
fi

echo "Downloading mp4decrypt from $MP4DECRYPT_URL"
mp4file="$tmpdir/mp4d"
curl -L "$MP4DECRYPT_URL" -o "$mp4file"
if file "$mp4file" | grep -q "Zip\|gzip\|tar"; then
  mkdir -p "$tmpdir/mp4d_ex"
  unzip -q "$mp4file" -d "$tmpdir/mp4d_ex" || tar -xf "$mp4file" -C "$tmpdir/mp4d_ex" || true
  # copy any mp4decrypt binary found
  while IFS= read -r -d '' f; do
    if [ "$(basename "$f")" = "mp4decrypt" ] || [ "$(basename "$f")" = "mp4decrypt.exe" ]; then
      cp "$f" "$PLATFORM_DIR/"
      chmod +x "$PLATFORM_DIR/$(basename "$f")"
      echo "mp4decrypt placed: $PLATFORM_DIR/$(basename "$f")"
      break
    fi
  done < <(find "$tmpdir/mp4d_ex" -type f -print0)
else
  chmod +x "$mp4file"
  mv "$mp4file" "$PLATFORM_DIR/mp4decrypt"
fi

echo "Downloading N_m3u8DL-RE from $N_M3U8DL_RE_URL"
nfile="$tmpdir/nm3u8"
curl -L "$N_M3U8DL_RE_URL" -o "$nfile"
if file "$nfile" | grep -q "Zip\|gzip\|tar"; then
  mkdir -p "$tmpdir/nm_ex"
  unzip -q "$nfile" -d "$tmpdir/nm_ex" || tar -xf "$nfile" -C "$tmpdir/nm_ex" || true
  while IFS= read -r -d '' f; do
    bn=$(basename "$f")
    if [[ "$bn" == N_m3u8DL-RE* ]] || [[ "$bn" == "N_m3u8DL-RE.exe" ]] || [[ "$bn" == "N_m3u8DL-RE" ]]; then
      cp "$f" "$PLATFORM_DIR/"
      chmod +x "$PLATFORM_DIR/$bn"
      echo "N_m3u8DL-RE placed: $PLATFORM_DIR/$bn"
      break
    fi
  done < <(find "$tmpdir/nm_ex" -type f -print0)
else
  chmod +x "$nfile"
  mv "$nfile" "$PLATFORM_DIR/N_m3u8DL-RE"
fi

echo "Finished fetching tools into $PLATFORM_DIR"
ls -la "$PLATFORM_DIR"
