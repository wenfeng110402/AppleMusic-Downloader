# Apple Music 下载器

初中生写的一个功能强大的 Apple Music 下载工具，支持下载歌曲、音乐视频和帖子内容。
I will create a multi-language version soon!

捐助链接（非盈利组织免税）Support me Donate me（non-porfit,no tax)
[here！](https://hcb.hackclub.com/donations/start/amdl)

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/wenfeng110402/AppleMusic-Downloader)](LICENSE)

## 功能特性

- 🎵 **高品质音频下载** - 支持 AAC 256kbps 等多种编码格式
- 🎬 **高清音乐视频** - 支持最高 1080p 分辨率下载
- 👤 **艺术家作品批量下载** - 通过多个链接或专辑歌单链接下载
- 🎨 **高度可定制** - 丰富的配置选项满足个性化需求

## 安装方式

### 方法一：使用安装程序（推荐，仅限Windows）

1. 从 [Releases](https://github.com/wenfeng110402/AppleMusic-Downloader/releases) 页面下载最新版本的安装程序
2. 运行 `AppleMusicDownloader_Setup.exe` 并按照提示完成安装
3. 安装完成后，您可以在开始菜单中找到 "Apple Music Downloader"

### 方法二：从源码运行

```bash
git clone https://github.com/wenfeng110402/AppleMusic-Downloader.git
cd AppleMusic-Downloader
pip install -r requirements.txt
```

## 环境要求

### 必需组件

- **Python 3.9 或更高版本**
- **有效的 Apple Music 订阅**
- **Netscape 格式的 Cookies 文件**
- **FFmpeg**

获取 Cookies 文件：

- **Firefox 用户**：使用 [Export Cookies](https://addons.mozilla.org/firefox/addon/export-cookies-txt/) 扩展
- **Chromium 内核浏览器用户**：使用 [Open Cookies.txt](https://chromewebstore.google.com/detail/open-cookiestxt/gdocmgbfkjnnpapoeobnolbbkoibbcif) 扩展

### 可选工具

以下工具为特定功能所需：

- [mp4decrypt](https://www.bento4.com/downloads/)：用于音乐视频下载和实验性音频编码
- [MP4Box](https://gpac.io/downloads/gpac-nightly-builds/)：替代混流模式
- [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE/releases/latest)：替代下载模式

## 支持的链接类型

- 单曲
- 专辑
- 播放列表
- 音乐视频
- 艺术家主页
- 帖子视频

## 致谢 / Acknowledgments

本项目使用了 [gamdl (Glomatico's Apple Music Downloader)](https://github.com/glomatico/gamdl) 的代码。我们衷心感谢 [Glomatico](https://github.com/glomatico) 和所有 gamdl 的贡献者们为开源社区所做的杰出工作。

This project utilizes code from [gamdl (Glomatico's Apple Music Downloader)](https://github.com/glomatico/gamdl). We sincerely thank [Glomatico](https://github.com/glomatico) and all contributors to gamdl for their outstanding work in the open-source community.
