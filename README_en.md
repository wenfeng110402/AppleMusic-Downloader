# AppleMusic Downloader
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/wenfeng110402/AppleMusic-Downloader/total?style=social&logo=GitHub)


Quick links:

- [中文 README](README.md)

Donate (non-profit, no tax)
[Here!](https://hcb.hackclub.com/donations/start/amdl)

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)](https://github.com/wenfeng110402/AppleMusic-Downloader)
![GitHub License](https://img.shields.io/github/license/wenfeng110402/AppleMusic-Downloader?style=social)


## Acknowledgments

This project utilizes code from [gamdl (Glomatico&#39;s Apple Music Downloader)](https://github.com/glomatico/gamdl) and [yt-dlp](https://github.com/yt-dlp/yt-dlpa). We sincerely thank all contributors to gamdl yt-dlp for their outstanding work in the open-source community.

## Features

- **High Quality** - Supports AAC 256kbps, ALAC, Atmos and more
- **MV Download** - Up to 1080p
- **Batch download of artist works** - Download via multiple links or album/playlist links
- **GUI & CLI** - Beautiful Fluent Design GUI + powerful command-line interface
- **Cross-Platform** - Windows, macOS, Linux
- **Customizable** - A wide range of configuration options to meet individual needs

## Installation

### Prerequisites

- **Python 3.9+**
- **pip** (Python package manager)

### Run from PyPi

```bash
pip install applemusic-dl
```

### Run from Source Code

```bash
git clone https://github.com/wenfeng110402/AppleMusic-Downloader.git
cd AppleMusic-Downloader
pip install -r requirements.txt
pip install -e .
```

### Launch GUI

```bash
python -m amdl
```

### Quick CLI usage

```bash
# See the help
amdl --help

amdl -c /path/to/cookies.txt "https://music.apple.com/..."
```

## Environmental requirements

### Required

- **Valid Apple Music subscription**
- **Netscape format cookies file**
- **FFmpeg** — install via your package manager:
  - macOS: `brew install ffmpeg`
  - Linux: `apt install ffmpeg` / `pacman -S ffmpeg`
  - Windows: download from [ffmpeg.org](https://ffmpeg.org/)

Get Cookies Files:

- **Firefox User**: Use [Export Cookies](https://addons.mozilla.org/firefox/addon/export-cookies-txt/) Extension
- **Chromium User**: Use [Open Cookies.txt](https://github.com/wenfeng110402/AppleMusic-Downloader/releases/download/v2.3.2/OpenCookies.txt.crx) Extension

### Optional dependencies

- [mp4decrypt](https://www.bento4.com/downloads/): required for song codecs and music videos
- [MP4Box](https://gpac.io/downloads/gpac-nightly-builds/): alternative remux mode
- [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE/releases/latest): alternative download mode

## Supported Link Types

- Singles
- Albums
- Playlists
- Music Videos
- Artist Profiles
- Post Videos

## Disclaimer

This tool is for educational and research purposes only. Any use that violates laws or infringes on the rights of others is strictly prohibited.

1. This project does not directly provide or store any copyrighted content. Users must independently provide vaild credentials (e.g., a valid Apple Music subscription and cookie files) to use its features.
2. I (or the development team) assume no responsibility for how users use this tool.Any legal or copyright disputes arising from its use are the sole responsibility of the user.
3. This project is implemented based on code from [yt-dlp](https://github.com/yt-dlp/yt-dlp) and is not directly affiliated with the original project's authors. If there are any objections, please contact me for assistance.
4. Users must ensure compliance with local laws and regulations when using this tool.

By using this tool, you agree to comply with all applicable laws and assume full responsibility for your actions.
