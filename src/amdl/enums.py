from enum import Enum


class DownloadMode(Enum):
    YTDLP = "ytdlp"
    NM3U8DLRE = "nm3u8dlre"


class RemuxMode(Enum):
    FFMPEG = "ffmpeg"
    MP4BOX = "mp4box"


class SongCodec(Enum):
    AAC_LEGACY = "aac-legacy"
    ATMOS = "atmos"


class SyncedLyricsFormat(Enum):
    LRC = "lrc"
    SRT = "srt"
    TTML = "ttml"


class MusicVideoCodec(Enum):
    H264 = "h264"
    H265 = "h265"
    ASK = "ask"


class PostQuality(Enum):
    BEST = "best"
    ASK = "ask"


class CoverFormat(Enum):
    JPG = "jpg"
    PNG = "png"
    RAW = "raw"
