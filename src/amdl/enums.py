"""
Compatibility shim — re-exports gamdl enums.
All downstream code should import from here for a single source of truth.
"""

from gamdl.downloader.enums import DownloadMode, RemuxMode  # noqa: F401
from gamdl.interface.enums import (  # noqa: F401
    CoverFormat,
    MusicVideoCodec,
    SongCodec,
    SyncedLyricsFormat,
    UploadedVideoQuality,
)

# Legacy alias
PostQuality = UploadedVideoQuality
