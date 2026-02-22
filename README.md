# Apple Music 下载器

Donate（non-porfit,no tax)
[here！](https://hcb.hackclub.com/donations/start/amdl)

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/wenfeng110402/AppleMusic-Downloader)](LICENSE)

## 致谢 / Acknowledgments

本项目使用了[gamdl（Glomatico的Apple Music下载器）](https://github.com/glomatico/gamdl)和[yt-dlp](https://github.com/yt-dlp/yt-dlpa)的代码。我们衷心感谢gamdl和yt-dlp的所有贡献者，感谢他们在开源社区做出的杰出贡献。

This project utilizes code from [gamdl (Glomatico's Apple Music Downloader)](https://github.com/glomatico/gamdl) and [yt-dlp](https://github.com/yt-dlp/yt-dlpa). We sincerely thank all contributors to gamdl yt-dlp for their outstanding work in the open-source community.

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
pip install -e .
```

本项目使用 `src` 布局；如果你不安装为可编辑包，也可以临时这样运行：

```bash
PYTHONPATH=src python -c "from amdl.cli import main; main(args=['--help'], standalone_mode=False)"
```

GUI 启动入口已统一为 `amdl.launcher`，源码运行可使用：

```bash
python -m amdl
```

### 命令行快速使用

```bash
amdl --help
amdl --cookies-path /path/to/cookies.txt "https://music.apple.com/..."
```

### Mac?
Try this [am-downloader-mac](https://github.com/aki4nvr/am-downloader-mac)

## CI/CD 验证与自动打包

仓库已内置 GitHub Actions 工作流：[.github/workflows/ci-build-windows.yml](.github/workflows/ci-build-windows.yml)

- `validate`：在 Ubuntu 安装依赖并执行 `python -m compileall src/amdl` 做基础验证。
- `build-windows`：在 Windows runner 联网下载 FFmpeg 压缩包，提取 `ffmpeg.exe` 到 `tools/` 后执行 PyInstaller 打包。
- 打包产物：`AppleMusicDownloader-windows-exe`（包含 `dist/AppleMusicDownloader.exe`）。

使用方式：

1. 打开 GitHub 仓库的 **Actions**。
2. 选择 **CI and Windows Build**。
3. 点击 **Run workflow** 手动触发，或通过 push/PR 自动触发。


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

## 免责声明 / Disclaimer

本工具仅供学习与研究使用，严禁将其用于任何违反法律法规或侵犯他人权益的用途。  
This tool is for educational and research purposes only. Any use that violates laws or infringes on the rights of others is strictly prohibited.

1. 本项目不直接提供或存储任何受版权保护的内容，用户需自行提供合法的凭证（如有效的 Apple Music 订阅和 Cookies 文件）以使用相关功能。  
   This project does not directly provide or store any copyrighted content. Users must independently provide valid credentials (e.g., a valid Apple Music subscription and cookie files) to use its features.

2. 本人不对用户如何使用本工具承担任何责任，因使用本工具产生的任何法律或版权争议，均由用户自行承担。  
   I (or the development team) assume no responsibility for how users use this tool. Any legal or copyright disputes arising from its use are the sole responsibility of the user.

3. 本项目基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 提供的代码实现，与原项目的作者无直接关联。如有任何异议，请联系本人以便协助处理。  
   This project is implemented based on code from [yt-dlp](https://github.com/yt-dlp/yt-dlp) and is not directly affiliated with the original project's authors. If there are any objections, please contact me for assistance.

4. 用户在使用本工具时，应自行确保符合当地相关法律法规。  
   Users must ensure compliance with local laws and regulations when using this tool.

By using this tool, you agree to comply with all applicable laws and assume full responsibility for your actions.  
通过使用本工具，您同意遵守所有适用法律，并对您的行为承担全部责任。
