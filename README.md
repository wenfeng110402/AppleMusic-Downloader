# Apple Music Downloader

一个功能强大的 Apple Music 下载工具，支持下载歌曲、音乐视频和帖子内容。

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/wenfeng110402/AppleMusic-Downloader)](LICENSE)

## 功能特性

- 🎵 **高品质音频下载** - 支持 AAC 256kbps 等多种编码格式
- 🎬 **高清音乐视频** - 支持最高 4K 分辨率下载
- 📝 **同步歌词支持** - 支持 LRC、SRT 和 TTML 格式
- 👤 **艺术家作品批量下载** - 通过艺术家链接下载全部作品
- 🎨 **高度可定制** - 丰富的配置选项满足个性化需求
- 🖥️ **双模式操作** - 支持图形界面和命令行两种使用方式

## 安装方式

### 方法一：使用安装程序（推荐，仅限Windows）

1. 从 [Releases](https://github.com/your-repo/releases) 页面下载最新版本的安装程序
2. 运行 `AppleMusicDownloader_Setup.exe` 并按照提示完成安装
3. 安装完成后，您可以在开始菜单中找到 "Apple Music Downloader"

### 方法三：从源码运行

```bash
git clone https://github.com/your-repo/AppleMusic-Downloader.git
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

