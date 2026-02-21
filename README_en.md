# AppleMusic Downloader

Donate (non-profit, no tax)
[Here!](https://hcb.hackclub.com/donations/start/amdl)

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/wenfeng110402/AppleMusic-Downloader)](LICENSE)

## Acknowledgments

This project utilizes code from [gamdl (Glomatico's Apple Music Downloader)](https://github.com/glomatico/gamdl) and [yt-dlp](https://github.com/yt-dlp/yt-dlpa). We sincerely thank all contributors to gamdl yt-dlp for their outstanding work in the open-source community.

## Features

- **High Quailty** - Supports AAC 256kbps and so on.
- **MV Download** - Up to 1080p
- **Batch download of artist works** - Download via multiple links or album playlist links
- **Customizable** - A wide range of configuration options to meet individual needs

## Installation

### Method 1: Use the installer (Recommended, Windows only)

1. From [Releases](https://github.com/wenfeng110402/AppleMusic-Downloader/releases)
page download the latest version of the installer.
2. Run `AppleMusicDownloader.exe`

### Method 2: Run from Source Code

```bash
git clone https://github.com/wenfeng110402/AppleMusic-Downloader.git
cd AppleMusic-Downloader
pip install -r requirements.txt
pip install -e .
```

This project uses a `src` layout. If you don't install it as an editable package, run it with:

```bash
PYTHONPATH=src python -c "from amdl.cli import main; main(args=['--help'], standalone_mode=False)"
```

### Quick CLI usage

```bash
amdl --help
amdl --cookies-path /path/to/cookies.txt "https://music.apple.com/..."
```

### Mac?
Try this [am-downloader-mac](https://github.com/aki4nvr/am-downloader-mac)

## Environmental requirements

### Required components

- **Python 3.9 or Higher**
- **Valid Apple Music subscription**
- **Netscape format cookies file**
- **FFmpeg**

Get Cookies Files:

- **FireFox User**: Use [Export Cookies](https://addons.mozilla.org/firefox/addon/export-cookies-txt/) Extension
- **Chromium User**: Use [Open Cookies.txt](https://github.com/wenfeng110402/AppleMusic-Downloader/releases/download/v2.3.2/OpenCookies.txt.crx) Extension

### Optional dependencies

The following tools are required for specific functions:

- [mp4decrypt](https://www.bento4.com/downloads/):Used for music and video downloads and experimental audio encoding.
- [MP4Box](https://gpac.io/downloads/gpac-nightly-builds/):Alternative Mixed Flow Mode
- [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE/releases/latest):Alternative Mixed Flow Mode

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