from __future__ import annotations

import functools
import re
import time
import typing
from http.cookiejar import MozillaCookieJar
from pathlib import Path

import requests

from .utils import raise_response_exception


class AppleMusicApi:
    APPLE_MUSIC_HOMEPAGE_URL = "https://beta.music.apple.com"
    AMP_API_URL = "https://amp-api.music.apple.com"
    WEBPLAYBACK_API_URL = (
        "https://play.itunes.apple.com/WebObjects/MZPlay.woa/wa/webPlayback"
    )
    LICENSE_API_URL = "https://play.itunes.apple.com/WebObjects/MZPlay.woa/wa/acquireWebPlaybackLicense"
    WAIT_TIME = 2

    def __init__(
        self,
        cookies_path: Path | None = Path("./cookies.txt"),
        storefront: None | str = None,
        language: str = "en-US",
    ):
        self.cookies_path = cookies_path
        self.storefront = storefront
        self.language = language
        self._set_session()

    def _set_session(self):
        self.session = requests.Session()
        if self.cookies_path:
            cookies = MozillaCookieJar(self.cookies_path)
            cookies.load(ignore_discard=True, ignore_expires=True)
            self.session.cookies.update(cookies)
            cookies_dict = self.session.cookies.get_dict()
            # 使用 get 避免 KeyError，当 cookie 中缺少字段时保持原有 storefront 或使用空字符串
            self.storefront = cookies_dict.get("itua", self.storefront)
            media_user_token = cookies_dict.get("media-user-token", "")
        else:
            media_user_token = ""
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "content-type": "application/json",
                "Media-User-Token": media_user_token,
                "x-apple-renewal": "true",
                "DNT": "1",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
                "origin": self.APPLE_MUSIC_HOMEPAGE_URL,
            }
        )
        # 添加重试机制获取主页
        max_retries = 3
        for attempt in range(max_retries):
            try:
                home_page = self.session.get(self.APPLE_MUSIC_HOMEPAGE_URL, timeout=30).text
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e

        # 有时主页中 index js 的命名会变化，使用多个候选正则按优先级查找
        index_patterns = [
            r"/(assets/index(?:-legacy)?[^/\'\"]+\.js)",
            r"/(assets/[^/\'\"]+index[^/\'\"]+\.js)",
        ]
        index_js_uri = None
        for pat in index_patterns:
            m = re.search(pat, home_page)
            if m:
                index_js_uri = m.group(1)
                break
        if not index_js_uri:
            # 无法找到 index js，抛出可调试的异常，包含主页片段
            snippet = home_page[:1000] if home_page else ""
            raise Exception(f"无法从 Apple Music 主页提取 index js 路径，页面片段: {snippet!r}")
        
        # 添加重试机制获取JS文件
        for attempt in range(max_retries):
            try:
                index_js_page = self.session.get(
                    f"{self.APPLE_MUSIC_HOMEPAGE_URL}/{index_js_uri}",
                    timeout=30
                ).text
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e
                    
        # token 有时以 eyJh 开头（Base64 JWT），使用更宽松的匹配并进行空值检查
        token_match = re.search(r"(eyJh[^\"\'\s]+)", index_js_page)
        if not token_match:
            # 若未匹配到 token，抛出包含 JS 片段的异常以便调试
            snippet = index_js_page[:1000] if index_js_page else ""
            raise Exception(f"无法从 index js 中提取授权 token，JS 片段: {snippet!r}")
        token = token_match.group(1)
        self.session.headers.update({"authorization": f"Bearer {token}"})
        self.session.params = {"l": self.language}

    def _check_amp_api_response(self, response: requests.Response):
        try:
            response.raise_for_status()
            response_dict = response.json()
            assert response_dict.get("data") or response_dict.get("results") is not None
        except (
            requests.HTTPError,
            requests.exceptions.JSONDecodeError,
            AssertionError,
        ) as e:
            raise_response_exception(response)
        except Exception as e:
            # 处理其他可能的异常
            raise Exception(f"检查API响应时发生未知错误: {str(e)}")

    def get_artist(
        self,
        artist_id: str,
        include: str = "albums,music-videos",
        limit: int = 100,
        fetch_all: bool = True,
    ) -> dict:
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.AMP_API_URL}/v1/catalog/{self.storefront}/artists/{artist_id}",
                    params={
                        "include": include,
                        **{f"limit[{_include}]": limit for _include in include.split(",")},
                    },
                    timeout=30  # 添加超时设置
                )
                
                self._check_amp_api_response(response)
                artist = response.json()["data"][0]
                if fetch_all:
                    for _include in include.split(","):
                        for additional_data in self._extend_api_data(
                            artist["relationships"][_include],
                            limit,
                        ):
                            artist["relationships"][_include]["data"].extend(additional_data)
                return artist
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e

    def get_song(
        self,
        song_id: str,
        extend: str = "extendedAssetUrls",
        include: str = "lyrics,albums",
    ) -> dict:
        # 验证song_id是否为数字
        if not song_id.isdigit():
            raise Exception(f"无效的歌曲ID: {song_id}，必须为数字")
            
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.AMP_API_URL}/v1/catalog/{self.storefront}/songs/{song_id}",
                    params={
                        "include": include,
                        "extend": extend,
                    },
                    timeout=30  # 添加超时设置
                )
                self._check_amp_api_response(response)
                return response.json()["data"][0]
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e

    def get_music_video(
        self,
        music_video_id: str,
        include: str = "albums",
    ) -> dict:
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.AMP_API_URL}/v1/catalog/{self.storefront}/music-videos/{music_video_id}",
                    params={
                        "include": include,
                    },
                    timeout=30  # 添加超时设置
                )
                self._check_amp_api_response(response)
                return response.json()["data"][0]
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e

    def get_post(
        self,
        post_id: str,
    ) -> dict:
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.AMP_API_URL}/v1/catalog/{self.storefront}/uploaded-videos/{post_id}",
                    timeout=30  # 添加超时设置
                )
                self._check_amp_api_response(response)
                return response.json()["data"][0]
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e

    @functools.lru_cache()
    def get_album(
        self,
        album_id: str,
        include: str = "tracks",
    ) -> dict:
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.AMP_API_URL}/v1/catalog/{self.storefront}/albums/{album_id}",
                    params={
                        "include": include,
                    },
                    timeout=30  # 添加超时设置
                )
                self._check_amp_api_response(response)
                return response.json()["data"][0]
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e

    @functools.lru_cache()
    def get_playlist(
        self,
        playlist_id: str,
        include: str = "tracks",
    ) -> dict:
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.AMP_API_URL}/v1/catalog/{self.storefront}/playlists/{playlist_id}",
                    params={
                        "include": include,
                    },
                    timeout=30  # 添加超时设置
                )
                self._check_amp_api_response(response)
                return response.json()["data"][0]
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e

    def search(
        self,
        term: str,
        types: str = "songs,albums,artists,playlists",
        limit: int = 25,
        offset: int = 0,
    ) -> dict:
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    f"{self.AMP_API_URL}/v1/catalog/{self.storefront}/search",
                    params={
                        "term": term,
                        "types": types,
                        "limit": limit,
                        "offset": offset,
                    },
                    timeout=30  # 添加超时设置
                )
                self._check_amp_api_response(response)
                return response.json()["results"]
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e

    def _extend_api_data(
        self,
        api_response: dict,
        limit: int,
    ) -> typing.Generator[list[dict], None, None]:
        next_uri = api_response.get("next")
        while next_uri:
            playlist_next = self._get_next_uri_response(next_uri, limit)
            yield playlist_next["data"]
            next_uri = playlist_next.get("next")
            time.sleep(self.WAIT_TIME)

    def _get_next_uri_response(self, next_uri: str, limit: int) -> dict:
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    self.AMP_API_URL + next_uri,
                    params={
                        "limit": limit,
                    },
                    timeout=30  # 添加超时设置
                )
                self._check_amp_api_response(response)
                return response.json()
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e

    def get_webplayback(
        self,
        track_id: str,
    ) -> dict:
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    self.WEBPLAYBACK_API_URL,
                    json={
                        "salableAdamId": track_id,
                        "language": self.language,
                    },
                    timeout=30  # 添加超时设置
                )
                try:
                    response.raise_for_status()
                    response_dict = response.json()
                    webplayback = response_dict.get("songList")
                    assert webplayback
                except (
                    requests.HTTPError,
                    requests.exceptions.JSONDecodeError,
                    AssertionError,
                ):
                    raise_response_exception(response)
                return webplayback[0]
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e

    def get_widevine_license(
        self,
        track_id: str,
        track_uri: str,
        challenge: str,
    ) -> str:
        # 添加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    self.LICENSE_API_URL,
                    json={
                        "challenge": challenge,
                        "key-system": "com.widevine.alpha",
                        "uri": track_uri,
                        "adamId": track_id,
                        "isLibrary": False,
                        "user-initiated": True,
                    },
                    timeout=30  # 添加超时设置
                )
                try:
                    response.raise_for_status()
                    response_dict = response.json()
                    widevine_license = response_dict.get("license")
                    assert widevine_license
                except (
                    requests.HTTPError,
                    requests.exceptions.JSONDecodeError,
                    AssertionError,
                ):
                    raise_response_exception(response)
                return widevine_license
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise e