#!/usr/bin/env bash
set -euo pipefail

# fetch_tools.sh <platform_dir> <platform> <arch>
# Expects environment variables (recommended to set via GitHub Actions secrets):
#   FFMPEG_URL, MP4DECRYPT_URL, N_M3U8DL_RE_URL
# Optional checksum env vars: FFMPEG_SHA256, MP4DECRYPT_SHA256, N_M3U8DL_RE_SHA256

PLATFORM_DIR="$1"
PLATFORM="$2"
ARCH="$3"

mkdir -p "$PLATFORM_DIR"

echo "Fetching tools into $PLATFORM_DIR for $PLATFORM/$ARCH"

require_var() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "ERROR: $name is not set. Please set it as an env var or GitHub secret."
    exit 2
  fi
}

require_var FFMPEG_URL
require_var MP4DECRYPT_URL
require_var N_M3U8DL_RE_URL

tmpdir=$(mktemp -d)
cleanup() { rm -rf "$tmpdir"; }
trap cleanup EXIT

compute_sha256() {
  local file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file" | awk '{print $1}'
  else
    shasum -a 256 "$file" | awk '{print $1}'
  fi
}

verify_checksum_if_provided() {
  local file="$1" expected_var_name="$2"
  local expected=${!expected_var_name:-}
  if [ -n "$expected" ]; then
    echo "Verifying checksum for $file against $expected_var_name"
    got=$(compute_sha256 "$file")
    if [ "${got,,}" != "${expected,,}" ]; then
      echo "Checksum mismatch: expected $expected but got $got"
      return 1
    fi
    echo "Checksum OK"
  fi
}

echo "Downloading ffmpeg from $FFMPEG_URL"
fffile="$tmpdir/ff"
curl -L "$FFMPEG_URL" -o "$fffile"
verify_checksum_if_provided "$fffile" FFMPEG_SHA256 || exit 3

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
  bn=$(basename "$f")
  if [ "$bn" = "ffmpeg" ] || [ "$bn" = "ffmpeg.exe" ]; then
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
verify_checksum_if_provided "$mp4file" MP4DECRYPT_SHA256 || exit 3
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
verify_checksum_if_provided "$nfile" N_M3U8DL_RE_SHA256 || exit 3
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
