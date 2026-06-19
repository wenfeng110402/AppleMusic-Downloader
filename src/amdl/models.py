from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UrlInfo:
    storefront: Optional[str] = None
    type: Optional[str] = None
    id: Optional[str] = None


@dataclass
class DownloadQueue:
    playlist_attributes: Optional[dict] = None
    tracks_metadata: Optional[list[dict]] = None


@dataclass
class Lyrics:
    synced: Optional[str] = None
    unsynced: Optional[str] = None


@dataclass
class StreamInfo:
    stream_url: Optional[str] = None
    widevine_pssh: Optional[str] = None
    playready_pssh: Optional[str] = None
    fairplay_key: Optional[str] = None
    codec: Optional[str] = None
    codec: str = None
