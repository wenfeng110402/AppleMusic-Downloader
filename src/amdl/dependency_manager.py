"""Auto-download & manage platform-specific binaries (ffmpeg, N_m3u8DL-RE, MP4Box).

Binaries are stored in <app_root>/bin/ and auto-downloaded when missing.
Download URLs point to well-known static builds — no build tools needed.
"""

from __future__ import annotations

import io
import logging
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable

logger = logging.getLogger("amdl.dep_mgr")

# ── paths ────────────────────────────────────────────────────
# BASE_DIR — project root (dev) or _MEIPASS (frozen, read-only).
# _DATA_DIR — writable persistent data directory.
# BIN_DIR   — where downloaded binaries live.

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _get_data_dir() -> Path:
    """Return a writable data directory persistent across runs.

    - PyInstaller bundle: uses OS-specific app data dir (read-write).
    - Development / pip install: uses the project root (BASE_DIR).
    """
    if getattr(sys, "frozen", False):
        app = "AppleMusicDownloader"
        if sys.platform == "win32":
            return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / app
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / app
        else:
            return Path.home() / ".local" / "share" / app
    return BASE_DIR


_DATA_DIR = _get_data_dir()
BIN_DIR = _DATA_DIR / "bin"


# Public alias — used by server.py for settings / temp
DATA_DIR = _DATA_DIR


# ── helpers ──────────────────────────────────────────────────
def _arch() -> str:
    m = platform.machine().lower()
    if m in ("aarch64", "arm64"):
        return "arm64"
    if m in ("amd64", "x86_64"):
        return "x64"
    return m


def _os() -> str:
    s = platform.system().lower()
    if s == "darwin":
        return "macos"
    if s == "windows":
        return "windows"
    return "linux"


def _exe(name: str) -> str:
    return f"{name}.exe" if _os() == "windows" else name


def _ensure_bin_dir() -> Path:
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    return BIN_DIR


def _make_executable(path: Path) -> None:
    if _os() != "windows":
        st = path.stat()
        path.chmod(st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


# ── dependency definitions ───────────────────────────────────

class DependencyDef:
    """Describes one binary: how to detect, where to download."""

    __slots__ = ("name", "exe_name", "download_urls", "archive_type", "extract_filter")

    def __init__(
        self,
        name: str,
        exe_name: str,
        download_urls: list[str],
        archive_type: str = "zip",
        extract_filter: Callable[[str], bool] | None = None,
    ) -> None:
        self.name = name
        self.exe_name = exe_name
        self.download_urls = download_urls
        self.archive_type = archive_type
        self.extract_filter = extract_filter


# ── Cloudflare R2 CDN mirror ─────────────────────────────────
# User-hosted binaries on R2 — faster than GitHub worldwide.
_R2_BASE = "https://pub-e4955324bbd043d79465a5231bec51f6.r2.dev"


# ── PyInstaller / frozen detection ──────────────────────────
def _is_frozen() -> bool:
    """Are we running inside a PyInstaller bundle?"""
    return getattr(sys, "frozen", False)


def _bundle_dir() -> Path | None:
    """Return the PyInstaller _MEIPASS / sys.executable parent dir."""
    if _is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return None


# ── URL builders per platform ────────────────────────────────

_FFMPEG_RELEASE = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest"


def _ffmpeg_url() -> str:
    os_ = _os()
    arch = _arch()
    if os_ == "macos":
        return f"{_FFMPEG_RELEASE}/ffmpeg-master-latest-macos-{arch}-gpl.zip"
    if os_ == "windows":
        return f"{_FFMPEG_RELEASE}/ffmpeg-master-latest-win64-gpl.zip"
    return f"{_FFMPEG_RELEASE}/ffmpeg-master-latest-linux64-gpl.tar.xz"


def _ffmpeg_filter(path: str) -> bool:
    name = Path(path).name
    return name == _exe("ffmpeg") or name == _exe("ffprobe")


_NM3U8DLRE_RELEASE = "https://github.com/nilaoda/N_m3u8DL-RE/releases/latest/download"


def _nm3u8dlre_urls() -> list[str]:
    """Return [primary, fallback] URLs for N_m3u8DL-RE."""
    os_ = _os()
    arch = _arch()
    urls: list[str] = []

    # 1) R2 direct download (Windows .exe only — macOS/Linux not hosted)
    if os_ == "windows":
        urls.append(f"{_R2_BASE}/N_m3u8DL-RE.exe")

    # 2) GitHub fallback (all platforms)
    ext = ".tar.gz" if os_ != "windows" else ".zip"
    urls.append(f"{_NM3U8DLRE_RELEASE}/N_m3u8DL-RE_{os_}-{arch}{ext}")

    return urls


def _nm3u8dlre_filter(path: str) -> bool:
    return Path(path).name == _exe("N_m3u8DL-RE")


_MP4BOX_RELEASE = "https://github.com/gpac/gpac/releases/latest/download"


def _mp4box_url() -> str:
    os_ = _os()
    arch = _arch()
    if os_ == "macos":
        return f"{_MP4BOX_RELEASE}/gpac_{arch}-macos.dmg"
    if os_ == "windows":
        return f"{_MP4BOX_RELEASE}/gpac_{arch}-win64.zip"
    # Linux — gpac is almost always available via system package, but provide fallback
    return f"{_MP4BOX_RELEASE}/gpac_{arch}-linux.tar.gz"


def _mp4box_filter(path: str) -> bool:
    """Extract MP4Box binary from gpac archive."""
    name = Path(path).name
    return name == _exe("MP4Box")


# ── known deps ───────────────────────────────────────────────

def _get_defs() -> list[DependencyDef]:
    """Return list of dependency definitions, best-effort per platform."""
    os_ = _os()
    arch = _arch()
    is_win = os_ == "windows"
    return [
        DependencyDef(
            name="ffmpeg",
            exe_name=_exe("ffmpeg"),
            download_urls=[_ffmpeg_url()],
            archive_type="zip" if os_ != "linux" else "tarxz",
            extract_filter=_ffmpeg_filter,
        ),
        DependencyDef(
            name="N_m3u8DL-RE",
            exe_name=_exe("N_m3u8DL-RE"),
            # R2 direct .exe (Windows) or archive (others), then GitHub fallback
            download_urls=_nm3u8dlre_urls(),
            archive_type="" if is_win else "targz",  # raw .exe on Windows
            extract_filter=_nm3u8dlre_filter,
        ),
        # MP4Box is optional — skipped on macOS (DMG impractical).
    ]


# ── winget support (Windows only) ────────────────────────────

_WINGET_PACKAGES: dict[str, str] = {
    "ffmpeg": "Gyan.FFmpeg",
    "MP4Box": "GPAC.GPAC",
    # N_m3u8DL-RE is NOT on winget — keep GitHub download
}


def _winget_available() -> bool:
    """Check if winget CLI is available on this system."""
    if _os() != "windows":
        return False
    try:
        subprocess.run(
            ["winget", "--version"],
            capture_output=True,
            timeout=10,
        )
        return True
    except Exception:
        return False


def _try_winget_install(name: str) -> bool:
    """Try to install a dependency via winget.

    Returns True if the binary is now findable in PATH after install.
    """
    pkg_id = _WINGET_PACKAGES.get(name)
    if not pkg_id:
        return False

    logger.info("Attempting winget install for %s (%s) …", name, pkg_id)
    _progress.update(name, "winget", 0)

    try:
        # ── check if already installed ──
        check = subprocess.run(
            ["winget", "list", "--exact", "--id", pkg_id, "--accept-source-agreements"],
            capture_output=True, text=True, timeout=30,
        )
        if pkg_id.lower() in check.stdout.lower():
            logger.info("%s already installed via winget, skipping", name)
            _progress.update(name, "ok", 100)
            return True

        # ── install (user scope — no admin needed) ──
        result = subprocess.run(
            [
                "winget", "install", "--exact", "--id", pkg_id,
                "--scope", "user",
                "--silent", "--accept-package-agreements",
                "--accept-source-agreements", "--disable-interactivity",
            ],
            capture_output=True, text=True, timeout=120,
        )

        if result.returncode == 0:
            _progress.update(name, "ok", 100)
            logger.info("winget installed %s successfully", name)
            return True

        # winget may return 0 even if it thinks it's done but return 0 for
        # "already installed" — we already handled that above with winget list.
        # Non-zero exit means installation failed.
        logger.warning("winget install for %s failed (exit %d): %s",
                       name, result.returncode, result.stderr[:200])
        _progress.update(name, "error", 0, f"winget failed (exit {result.returncode})")
        return False

    except subprocess.TimeoutExpired:
        logger.warning("winget install for %s timed out", name)
        _progress.update(name, "error", 0, "winget timed out")
        return False
    except Exception as e:
        logger.warning("winget install for %s error: %s", name, e)
        _progress.update(name, "error", 0, str(e))
        return False


# ── download engine ──────────────────────────────────────────

class DownloadProgress:
    """Tracks download progress across all dependencies."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._status: dict[str, dict] = {}  # name → {status, progress, error}

    def update(self, name: str, status: str, progress: float = 0, error: str = "") -> None:
        with self._lock:
            self._status[name] = {"status": status, "progress": progress, "error": error}

    def get(self) -> dict:
        with self._lock:
            return dict(self._status)

    def all_done(self) -> bool:
        with self._lock:
            if not self._status:
                return True
            return all(
                s["status"] in ("ok", "skipped", "error")
                for s in self._status.values()
            )


_progress = DownloadProgress()


def get_progress() -> dict:
    """Get current download progress (thread-safe)."""
    return _progress.get()


# ── download + extract ───────────────────────────────────────

class _DownloadReport:
    def __init__(self, ok: bool, bin_path: Path | None = None, error: str = "") -> None:
        self.ok = ok
        self.bin_path = bin_path
        self.error = error


def _download_and_extract(dep: DependencyDef) -> _DownloadReport:
    """Try each URL in dep.download_urls until one works."""
    exe_name = dep.exe_name
    dest = _ensure_bin_dir() / exe_name

    if dest.exists():
        logger.info("%s already exists at %s, skipping download", dep.name, dest)
        return _DownloadReport(True, dest)

    for url in dep.download_urls:
        logger.info("Downloading %s from %s …", dep.name, url)
        _progress.update(dep.name, "downloading", 0)

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "amdl/2.0"})
            resp = urllib.request.urlopen(req, timeout=120)
            total = int(resp.headers.get("Content-Length", 0))
            chunk_size = 64 * 1024
            buf = io.BytesIO()
            downloaded = 0
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                buf.write(chunk)
                downloaded += len(chunk)
                if total:
                    _progress.update(dep.name, "downloading", min(downloaded / total * 100, 99))

            _progress.update(dep.name, "extracting", 90)
            data = buf.getvalue()

            if dep.archive_type == "zip":
                _extract_from_zip(data, dep, dest)
            elif dep.archive_type in ("targz", "tarxz"):
                _extract_from_tar(data, dep, dest)
            elif dep.archive_type == "dmg":
                return _DownloadReport(False, error=f"DMG extraction not supported: {url}")
            else:
                # raw binary (e.g. N_m3u8DL-RE.exe from R2)
                dest.write_bytes(data)
                _make_executable(dest)

            if dest.exists():
                _progress.update(dep.name, "ok", 100)
                logger.info("Downloaded %s → %s", dep.name, dest)
                return _DownloadReport(True, dest)

        except Exception as e:
            logger.warning("Failed to download from %s: %s", url, e)
            _progress.update(dep.name, "downloading", 0, f"Retrying… ({type(e).__name__})")
            continue  # try next URL

    _progress.update(dep.name, "error", 0, "All download sources failed")
    return _DownloadReport(False, error="All download sources failed")


def _extract_from_zip(data: bytes, dep: DependencyDef, dest: Path) -> None:
    """Extract a member from a zip archive."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            p = Path(name)
            if dep.extract_filter and dep.extract_filter(name):
                member = zf.read(name)
                dest.write_bytes(member)
                _make_executable(dest)
                return
            # fallback: match by filename
            if p.name == dep.exe_name:
                member = zf.read(name)
                dest.write_bytes(member)
                _make_executable(dest)
                return


def _extract_from_tar(data: bytes, dep: DependencyDef, dest: Path, mode: str = "r:gz") -> None:
    """Extract a member from a tar archive."""
    if dep.archive_type == "tarxz":
        mode = "r:xz"
    with tarfile.open(fileobj=io.BytesIO(data), mode=mode) as tf:
        for member in tf.getmembers():
            if dep.extract_filter and dep.extract_filter(member.name):
                tf.extract(member, path=dest.parent)
                extracted = dest.parent / member.name
                if extracted != dest:
                    extracted.rename(dest)
                _make_executable(dest)
                return
            if Path(member.name).name == dep.exe_name:
                tf.extract(member, path=dest.parent)
                extracted = dest.parent / member.name
                if extracted != dest:
                    extracted.rename(dest)
                _make_executable(dest)
                return


# ── public API ───────────────────────────────────────────────

def find_bundled(name: str) -> Path | None:
    """Look for a binary in BIN_DIR or inside a PyInstaller bundle."""
    exe = _exe(name)

    # 1) BIN_DIR (auto-downloaded or runtime-placed)
    p = BIN_DIR / exe
    if p.exists():
        return p

    # 2) PyInstaller bundle (_MEIPASS/bin/)
    bd = _bundle_dir()
    if bd:
        p = bd / "bin" / exe
        if p.exists():
            return p

    return None


def ensure_dependencies_async() -> None:
    """Check and download missing dependencies in a background thread."""
    thread = threading.Thread(target=_ensure_dependencies_sync, daemon=True)
    thread.start()


def _ensure_dependencies_sync() -> None:
    """Synchronous dependency check & download."""
    _ensure_bin_dir()
    defs = _get_defs()
    use_winget = _winget_available() if _os() == "windows" else False

    for dep in defs:
        exe_name = dep.exe_name
        dest = BIN_DIR / exe_name

        # ── already in BIN_DIR? ──────────────────────
        if dest.exists():
            _progress.update(dep.name, "ok", 100)
            logger.info("%s found at %s", dep.name, dest)
            continue

        # ── bundled in PyInstaller? copy to BIN_DIR ──
        bd = _bundle_dir()
        if bd:
            src = bd / "bin" / exe_name
            if src.exists():
                _progress.update(dep.name, "ok", 100)
                shutil.copy2(str(src), str(dest))
                _make_executable(dest)
                logger.info("Copied bundled %s → %s", dep.name, dest)
                continue

        # ── Windows: try winget first ─────────────────────
        if use_winget and dep.name in _WINGET_PACKAGES:
            logger.info("Trying winget for %s …", dep.name)
            if _try_winget_install(dep.name):
                # winget succeeded — binary should now be in PATH
                continue
            # winget failed — fall through to GitHub download
            logger.info("winget failed for %s, falling back to GitHub download", dep.name)

        # skip MP4Box on macOS — DMG extraction is impractical
        if dep.name == "MP4Box" and _os() == "macos":
            _progress.update(dep.name, "skipped", 0, "Use 'brew install gpac' or download manually")
            logger.info("Skipping MP4Box auto-download on macOS — use 'brew install gpac'")
            continue

        # skip N_m3u8DL-RE on macOS arm64 if URL not available (pre-release)
        if dep.name == "N_m3u8DL-RE" and _os() == "macos" and _arch() not in ("arm64", "x64"):
            _progress.update(dep.name, "skipped", 0, "No prebuilt binary for this platform")
            continue

        result = _download_and_extract(dep)
        if not result.ok:
            logger.warning("Auto-download failed for %s: %s", dep.name, result.error)
