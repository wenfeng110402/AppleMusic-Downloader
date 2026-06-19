from __future__ import annotations

import base64
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path
from xml.dom import minidom
from xml.etree import ElementTree

import m3u8
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from .constants import SONG_CODEC_REGEX_MAP, SYNCED_LYRICS_FILE_EXTENSION_MAP
from .downloader import Downloader
from .enums import RemuxMode, SongCodec, SyncedLyricsFormat
from .models import Lyrics, StreamInfo


class DownloaderSong:
    DEFAULT_DECRYPTION_KEY = "32b8ade1769e26b1ffb8986352793fc6"
    MP4_FORMAT_CODECS = ["ec-3"]

    def __init__(
        self,
        downloader: Downloader,
        codec: SongCodec = SongCodec.AAC_LEGACY,
        synced_lyrics_format: SyncedLyricsFormat = SyncedLyricsFormat.LRC,
    ):
        self.downloader = downloader
        self.codec = codec
        self.synced_lyrics_format = synced_lyrics_format

    def get_drm_infos(self, m3u8_data: dict) -> dict | None:
        drm_info_raw = next(
            (
                session_data
                for session_data in m3u8_data["session_data"]
                if session_data["data_id"] == "com.apple.hls.AudioSessionKeyInfo"
            ),
            None,
        )
        if not drm_info_raw:
            return None
        return json.loads(base64.b64decode(drm_info_raw["value"]).decode("utf-8"))

    def get_asset_infos(self, m3u8_data: dict) -> dict | None:
        return json.loads(
            base64.b64decode(
                next(
                    session_data
                    for session_data in m3u8_data["session_data"]
                    if session_data["data_id"] == "com.apple.hls.audioAssetMetadata"
                )["value"]
            ).decode("utf-8")
        )

    def get_playlist_from_codec(self, m3u8_data: dict) -> dict | None:
        m3u8_master_playlists = [
            playlist
            for playlist in m3u8_data["playlists"]
            if re.fullmatch(
                SONG_CODEC_REGEX_MAP[self.codec], playlist["stream_info"]["audio"]
            )
        ]
        if not m3u8_master_playlists:
            return None
        m3u8_master_playlists.sort(key=lambda x: x["stream_info"]["average_bandwidth"])
        return m3u8_master_playlists[-1]

    def get_playlist_from_user(self, m3u8_data: dict) -> dict | None:
        m3u8_master_playlists = [playlist for playlist in m3u8_data["playlists"]]
        choices = [
            Choice(
                name=playlist["stream_info"]["audio"],
                value=playlist,
            )
            for playlist in m3u8_master_playlists
        ]
        selected = inquirer.select(
            message="Select which codec to download:",
            choices=choices,
        ).execute()
        return selected

    def _get_drm_data(
        self,
        drm_infos: dict,
        drm_ids: list,
        drm_key: str,
    ) -> str | None:
        drm_info = next(
            (
                drm_infos[drm_id]
                for drm_id in drm_ids
                if drm_infos[drm_id].get(drm_key) and drm_id != "1"
            ),
            None,
        )
        if not drm_info:
            return None
        return drm_info[drm_key]["URI"]

    def get_widevine_pssh(
        self,
        drm_infos: dict,
        drm_ids: list,
    ) -> str | None:
        return self._get_drm_data(
            drm_infos,
            drm_ids,
            "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed",
        )

    def get_playready_pssh(self, drm_infos: dict, drm_ids: list) -> str | None:
        return self._get_drm_data(
            drm_infos,
            drm_ids,
            "com.microsoft.playready",
        )

    def get_fairplay_key(self, drm_infos: dict, drm_ids: list) -> str | None:
        return self._get_drm_data(
            drm_infos,
            drm_ids,
            "com.apple.streamingkeydelivery",
        )

    def get_stream_info(self, track_metadata: dict, webplayback: dict | None = None) -> StreamInfo:
        m3u8_url = track_metadata["attributes"].get("extendedAssetUrls", {}).get("enhancedHls")
        if m3u8_url:
            result = self._get_stream_info(m3u8_url)
            if result.stream_url and result.widevine_pssh:
                return result

        # Fallback: use webplayback-based stream (legacy codec path)
        # This handles songs where Widevine PSSH is only available via
        # webplayback assets (e.g. CENC `28:ctrp256` flavor), not from
        # the enhancedHls master playlist.
        if webplayback:
            return self._get_stream_info_from_webplayback(webplayback)
        return StreamInfo()

    def _get_stream_info_from_webplayback(self, webplayback: dict) -> StreamInfo:
        stream_info = StreamInfo()
        try:
            assets = webplayback.get("assets", [])
            if not assets:
                return stream_info

            # Try each asset in order — look for one with a usable DRM key
            for asset in assets:
                stream_url = asset.get("URL")
                if not stream_url:
                    continue

                m3u8_obj = m3u8.load(stream_url)
                m3u8_data = m3u8_obj.data

                # Check top-level keys for Widevine (classic keyformat or CENC)
                for key in m3u8_data.get("keys", []):
                    kf = key.get("keyformat")
                    method = key.get("method")
                    uri = key.get("uri")
                    if not uri:
                        continue
                    # Classic Widevine keyformat
                    if kf == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed":
                        stream_info.widevine_pssh = uri
                        break
                    # CENC scheme (ISO-23001-7) — Widevine without explicit keyformat
                    if method and method.upper() == "ISO-23001-7".upper():
                        stream_info.widevine_pssh = uri
                        break

                if stream_info.widevine_pssh:
                    stream_info.stream_url = stream_url
                    stream_info.codec = asset.get("codec") or "aac"
                    break

            # If no Widevine found via top-level keys, try session_data path
            if not stream_info.widevine_pssh:
                for asset in assets:
                    stream_url = asset.get("URL")
                    if not stream_url:
                        continue
                    m3u8_obj = m3u8.load(stream_url)
                    m3u8_data = m3u8_obj.data
                    if m3u8_data.get("session_data"):
                        drm_infos = self.get_drm_infos(m3u8_data)
                        if drm_infos:
                            asset_infos = self.get_asset_infos(m3u8_data)
                            playlist = self.get_playlist_from_codec(m3u8_data)
                            if playlist and asset_infos:
                                variant_id = playlist["stream_info"]["stable_variant_id"]
                                drm_ids = asset_infos[variant_id].get("AUDIO-SESSION-KEY-IDS", [])
                                pssh = self.get_widevine_pssh(drm_infos, drm_ids)
                                if pssh:
                                    stream_info.widevine_pssh = pssh
                                    stream_info.stream_url = m3u8_obj.base_uri + playlist["uri"]
                                    stream_info.codec = playlist["stream_info"]["codecs"]
                                    break

            if not stream_info.stream_url:
                # Last resort: use first asset's URL
                stream_info.stream_url = assets[0].get("URL", "")
                stream_info.codec = assets[0].get("codec") or "aac"
            elif not stream_info.codec:
                stream_info.codec = "aac"
        except Exception:
            pass
        return stream_info

    def _get_stream_info(self, m3u8_url: str) -> StreamInfo:
        stream_info = StreamInfo()
        m3u8_obj = m3u8.load(m3u8_url)
        m3u8_data = m3u8_obj.data
        drm_infos = self.get_drm_infos(m3u8_data)
        asset_infos = self.get_asset_infos(m3u8_data)
        playlist = self.get_playlist_from_codec(m3u8_data)
        if playlist is None:
            return stream_info
        stream_info.stream_url = m3u8_obj.base_uri + playlist["uri"]
        stream_info.codec = playlist["stream_info"]["codecs"]

        if drm_infos and asset_infos:
            # DRM keys in master's session_data (standard path)
            variant_id = playlist["stream_info"]["stable_variant_id"]
            drm_ids = asset_infos[variant_id]["AUDIO-SESSION-KEY-IDS"]
            stream_info.widevine_pssh = self.get_widevine_pssh(drm_infos, drm_ids)
            stream_info.playready_pssh = self.get_playready_pssh(drm_infos, drm_ids)
            stream_info.fairplay_key = self.get_fairplay_key(drm_infos, drm_ids)
        else:
            # Some songs have DRM keys in the media playlist M3U8 itself
            # (no AudioSessionKeyInfo in master's session_data).
            # Load the media playlist with proper auth headers and check keys.
            try:
                resp = self.downloader.apple_music_api.session.get(
                    stream_info.stream_url, timeout=30
                )
                resp.raise_for_status()
                media_m3u8 = m3u8.loads(resp.text)
                for key in media_m3u8.keys:
                    if key.keyformat == "urn:uuid:edef8ba9-79d6-4ace-a3c8-27dcd51d21ed":
                        stream_info.widevine_pssh = key.uri
                    elif key.keyformat == "com.microsoft.playready":
                        stream_info.playready_pssh = key.uri
                    elif key.keyformat == "com.apple.streamingkeydelivery":
                        stream_info.fairplay_key = key.uri
            except Exception:
                pass

        return stream_info

    @staticmethod
    def parse_datetime_obj_from_timestamp_ttml(
        timestamp_ttml: str,
    ) -> datetime.datetime:
        mins_secs_ms = re.findall(r"\d+", timestamp_ttml)
        ms, secs, mins = 0, 0, 0
        if len(mins_secs_ms) == 2 and ":" in timestamp_ttml:
            secs, mins = int(mins_secs_ms[-1]), int(mins_secs_ms[-2])
        elif len(mins_secs_ms) == 1:
            ms = int(mins_secs_ms[-1])
        else:
            secs = float(f"{mins_secs_ms[-2]}.{mins_secs_ms[-1]}")
            if len(mins_secs_ms) > 2:
                mins = int(mins_secs_ms[-3])
        return datetime.datetime.fromtimestamp(
            (mins * 60) + secs + (ms / 1000),
            tz=datetime.timezone.utc,
        )

    def get_lyrics_synced_timestamp_lrc(self, timestamp_ttml: str) -> str:
        datetime_obj = self.parse_datetime_obj_from_timestamp_ttml(timestamp_ttml)
        ms_new = datetime_obj.strftime("%f")[:-3]
        if int(ms_new[-1]) >= 5:
            ms = int(f"{int(ms_new[:2]) + 1}") * 10
            datetime_obj += datetime.timedelta(milliseconds=ms) - datetime.timedelta(
                microseconds=datetime_obj.microsecond
            )
        return datetime_obj.strftime("%M:%S.%f")[:-4]

    def get_lyrics_synced_timestamp_srt(self, timestamp_ttml: str) -> str:
        datetime_obj = self.parse_datetime_obj_from_timestamp_ttml(timestamp_ttml)
        return datetime_obj.strftime("00:%M:%S,%f")[:-3]

    def get_lyrics_synced_line_lrc(self, timestamp_ttml: str, text: str) -> str:
        return f"[{self.get_lyrics_synced_timestamp_lrc(timestamp_ttml)}]{text}"

    def get_lyrics_synced_line_srt(
        self,
        index: int,
        timestamp_ttml_start: str,
        timestamp_ttml_end: str,
        text: str,
    ) -> str:
        timestamp_srt_start = self.get_lyrics_synced_timestamp_srt(timestamp_ttml_start)
        timestamp_srt_end = self.get_lyrics_synced_timestamp_srt(timestamp_ttml_end)
        return f"{index}\n{timestamp_srt_start} --> {timestamp_srt_end}\n{text}\n"

    def get_lyrics(self, track_metadata: dict) -> Lyrics:
        lyrics = Lyrics(synced="", unsynced="")
        if not track_metadata["attributes"]["hasLyrics"]:
            return lyrics
        elif track_metadata.get("relationships") is None:
            track_metadata = self.downloader.apple_music_api.get_song(
                track_metadata["id"]
            )
        if (
            track_metadata["relationships"].get("lyrics")
            and track_metadata["relationships"]["lyrics"].get("data")
            and track_metadata["relationships"]["lyrics"]["data"][0].get("attributes")
        ):
            lyrics = self._get_lyrics(
                track_metadata["relationships"]["lyrics"]["data"][0]["attributes"][
                    "ttml"
                ]
            )
        return lyrics

    def _get_lyrics(self, lyrics_ttml: str) -> Lyrics:
        lyrics = Lyrics("", "")
        lyrics_ttml_et = ElementTree.fromstring(lyrics_ttml)
        index = 1
        for div in lyrics_ttml_et.iter("{http://www.w3.org/ns/ttml}div"):
            for p in div.iter("{http://www.w3.org/ns/ttml}p"):
                if p.text is not None:
                    lyrics.unsynced += p.text + "\n"
                if p.attrib.get("begin"):
                    if self.synced_lyrics_format == SyncedLyricsFormat.LRC:
                        lyrics.synced += f"{self.get_lyrics_synced_line_lrc(p.attrib.get('begin'), p.text)}"
                    elif self.synced_lyrics_format == SyncedLyricsFormat.SRT:
                        lyrics.synced += f"{self.get_lyrics_synced_line_srt(index, p.attrib.get('begin'), p.attrib.get('end'), p.text)}"
                    elif self.synced_lyrics_format == SyncedLyricsFormat.TTML:
                        if not lyrics.synced:
                            lyrics.synced = minidom.parseString(
                                lyrics_ttml
                            ).toprettyxml()
                        continue
                    lyrics.synced += "\n"
                    index += 1
            lyrics.unsynced += "\n"
        lyrics.unsynced = lyrics.unsynced[:-2]
        return lyrics

    def get_tags(self, webplayback: dict, lyrics_unsynced: str) -> dict:
        tags_raw = webplayback["assets"][0]["metadata"]
        tags = {
            "album": tags_raw["playlistName"],
            "album_artist": tags_raw["playlistArtistName"],
            "album_id": int(tags_raw["playlistId"]),
            "album_sort": tags_raw["sort-album"],
            "artist": tags_raw["artistName"],
            "artist_id": int(tags_raw["artistId"]),
            "artist_sort": tags_raw["sort-artist"],
            "comments": tags_raw.get("comments"),
            "compilation": tags_raw["compilation"],
            "composer": tags_raw.get("composerName"),
            "composer_id": (
                int(tags_raw.get("composerId")) if tags_raw.get("composerId") else None
            ),
            "composer_sort": tags_raw.get("sort-composer"),
            "copyright": tags_raw.get("copyright"),
            "date": (
                self.downloader.sanitize_date(tags_raw["releaseDate"])
                if tags_raw.get("releaseDate")
                else None
            ),
            "disc": tags_raw["discNumber"],
            "disc_total": tags_raw["discCount"],
            "gapless": tags_raw["gapless"],
            "genre": tags_raw.get("genre"),
            "genre_id": tags_raw["genreId"],
            "lyrics": lyrics_unsynced if lyrics_unsynced else None,
            "media_type": 1,
            "rating": tags_raw["explicit"],
            "storefront": tags_raw["s"],
            "title": tags_raw["itemName"],
            "title_id": int(tags_raw["itemId"]),
            "title_sort": tags_raw["sort-name"],
            "track": tags_raw["trackNumber"],
            "track_total": tags_raw["trackCount"],
            "xid": tags_raw.get("xid"),
        }
        return tags

    def get_encrypted_path(self, track_id: str) -> Path:
        return self.downloader.temp_path / f"{track_id}_encrypted.m4a"

    def get_decrypted_path(self, track_id: str) -> Path:
        return self.downloader.temp_path / f"{track_id}_decrypted.m4a"

    def get_remuxed_path(self, track_id: str) -> Path:
        return self.downloader.temp_path / f"{track_id}_remuxed.m4a"

    def fix_key_id(self, encrypted_path: Path):
        count = 0
        with open(encrypted_path, "rb+") as file:
            while data := file.read(4096):
                pos = file.tell()
                i = 0
                while True:
                    tenc = data.find(b"tenc", i)
                    if tenc == -1:
                        break
                    kid = tenc + 12
                    file.seek(max(0, pos - 4096) + kid, 0)
                    file.write(bytes.fromhex(f"{count:032}"))
                    count += 1
                    i = tenc + 1
                file.seek(pos, 0)

    def decrypt(
        self,
        encrypted_path: Path,
        decrypted_path: Path,
        decryption_key: str,
        cenc_kid: str | None = None,
    ):
        if cenc_kid:
            # CENC stream: keep original KID, use it directly
            subprocess.run(
                [
                    self.downloader.mp4decrypt_path_full,
                    encrypted_path,
                    "--key",
                    f"{cenc_kid}:{decryption_key}",
                    decrypted_path,
                ],
                check=True,
                **self.downloader.subprocess_additional_args,
            )
        else:
            self.fix_key_id(encrypted_path)
            subprocess.run(
                [
                    self.downloader.mp4decrypt_path_full,
                    encrypted_path,
                    "--key",
                    f"00000000000000000000000000000001:{decryption_key}",
                    "--key",
                    f"00000000000000000000000000000000:{self.DEFAULT_DECRYPTION_KEY}",
                    decrypted_path,
                ],
                check=True,
                **self.downloader.subprocess_additional_args,
            )

    def remux(self, decrypted_path: Path, remuxed_path: Path, codec: str):
        if self.downloader.remux_mode == RemuxMode.MP4BOX:
            self.remux_mp4box(decrypted_path, remuxed_path)
        elif self.downloader.remux_mode == RemuxMode.FFMPEG:
            self.remux_ffmpeg(decrypted_path, remuxed_path, codec)

    def remux_mp4box(self, decrypted_path: Path, remuxed_path: Path):
        subprocess.run(
            [
                self.downloader.mp4box_path_full,
                "-quiet",
                "-add",
                decrypted_path,
                "-itags",
                "artist=placeholder",
                "-keep-utc",
                "-new",
                remuxed_path,
            ],
            check=True,
            **self.downloader.subprocess_additional_args,
        )

    def remux_ffmpeg(
        self,
        decrypted_path: Path,
        remuxed_path: Path,
        codec: str,
    ):
        # Check if the decrypted file is fragmented (contains moof boxes).
        # Scan the entire file — 4 KB is not enough because moof may
        # appear after a large moov box.
        is_fragmented = False
        try:
            with open(decrypted_path, "rb") as _f:
                is_fragmented = b"moof" in _f.read()
        except Exception:
            pass

        if is_fragmented:
            # Fragmented MP4 files from mp4decrypt can't be reliably
            # re-muxed with -c copy — ffmpeg drops priming samples and
            # macOS can't play the output. Re-encode AAC to get a valid file.
            # Use Apple's encoder (aac_at) on macOS for best compatibility.
            aac_encoder = "aac"
            if sys.platform == "darwin":
                aac_encoder = "aac_at"
            subprocess.run(
                [
                    self.downloader.ffmpeg_path_full,
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    decrypted_path,
                    "-c:a",
                    aac_encoder,
                    "-b:a",
                    "256k",
                    "-f",
                    "mp4",
                    "-movflags",
                    "+faststart",
                    remuxed_path,
                ],
                check=True,
                **self.downloader.subprocess_additional_args,
            )
        else:
            use_mp4_format = any(
                codec.startswith(possible_codec)
                for possible_codec in self.MP4_FORMAT_CODECS
            )
            subprocess.run(
                [
                    self.downloader.ffmpeg_path_full,
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    decrypted_path,
                    "-c",
                    "copy",
                    "-f",
                    "mp4" if use_mp4_format else "ipod",
                    "-movflags",
                    "+faststart",
                    remuxed_path,
                ],
                check=True,
                **self.downloader.subprocess_additional_args,
            )

    def get_lyrics_synced_path(self, final_path: Path) -> Path:
        return final_path.with_suffix(
            SYNCED_LYRICS_FILE_EXTENSION_MAP[self.synced_lyrics_format]
        )

    def get_cover_path(self, final_path: Path, file_extension: str) -> Path:
        return final_path.parent / ("Cover" + file_extension)

    def save_lyrics_synced(self, lyrics_synced_path: Path, lyrics_synced: str):
        lyrics_synced_path.parent.mkdir(parents=True, exist_ok=True)
        lyrics_synced_path.write_text(lyrics_synced, encoding="utf8")
