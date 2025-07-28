# Apple Music Downloader

一个功能强大的 Apple Music 下载工具，支持下载歌曲、音乐视频和帖子内容。

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/glomatico/gamdl)](LICENSE)

## 功能特性

- 🎵 **高品质音频下载** - 支持 AAC 256kbps 等多种编码格式
- 🎬 **高清音乐视频** - 支持最高 4K 分辨率下载
- 📝 **同步歌词支持** - 支持 LRC、SRT 和 TTML 格式
- 👤 **艺术家作品批量下载** - 通过艺术家链接下载全部作品
- 🎨 **高度可定制** - 丰富的配置选项满足个性化需求
- 🖥️ **双模式操作** - 支持图形界面和命令行两种使用方式

## 界面预览

![GUI界面](https://raw.githubusercontent.com/glomatico/gamdl/main/assets/gui.png)

## 安装方式

### 方法一：使用安装程序（推荐，仅限Windows）

1. 从 [Releases](https://github.com/your-repo/releases) 页面下载最新版本的安装程序
2. 运行 `AppleMusicDownloader_Setup.exe` 并按照提示完成安装
3. 安装完成后，您可以在开始菜单中找到 "Apple Music Downloader"

### 方法二：通过 pip 安装

```bash
pip install gamdl
```

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

## 使用方法

### 图形界面模式

```bash
python -m gamdl
```

图形界面提供直观的操作方式，适合普通用户使用。

### 命令行模式

```bash
gamdl [OPTIONS] URLS...
```

示例：
```bash
gamdl "https://music.apple.com/us/album/album-name/album-id"
```

## 支持的链接类型

- 单曲
- 专辑
- 播放列表
- 音乐视频
- 艺术家主页
- 帖子视频

## 交互式操作控制

- **方向键**：移动选择
- **空格键**：切换选中状态
- **Ctrl + A**：全选
- **回车键**：确认选择

## 配置选项

### 路径设置
- `--cookie-file`: Cookies 文件路径
- `--output-path`: 输出目录路径
- `--temp-path`: 临时文件目录路径
- `--wvd-path`: .wvd 设备文件路径

### 下载选项
- `--save-cover`: 保存封面图片
- `--overwrite`: 覆盖已存在的文件
- `--disable-music-video-skip`: 不跳过已存在的音乐视频
- `--save-playlist`: 保存播放列表
- `--synced-lyrics-only`: 仅下载同步歌词
- `--no-synced-lyrics`: 不下载同步歌词
- `--read-urls-as-txt`: 将输入作为包含 URL 的文本文件处理

### 高级选项
- `--download-mode`: 下载模式 (ytdlp 或 nm3u8dlre)
- `--remux-mode`: 混流模式 (ffmpeg 或 mp4box)
- `--cover-format`: 封面图片格式 (jpg, png, raw)
- `--cover-size`: 封面图片尺寸 (像素)
- `--truncate`: 截断文件名长度
- `--codec-song`: 音频编解码器 (aac-legacy, aac-he-legacy, aac, aac-he, aac-binaural, aac-downmix, aac-he-binaural, aac-he-downmix, atmos, ac3, alac, ask)
- `--exclude-tags`: 排除的元数据标签

### 模板选项
- `--template-folder-album`: 专辑文件夹命名模板
- `--template-folder-compilation`: 合辑文件夹命名模板
- `--template-file-single-disc`: 单碟文件命名模板
- `--template-file-multi-disc`: 多碟文件命名模板
- `--template-folder-no-album`: 无专辑歌曲文件夹命名模板
- `--template-file-no-album`: 无专辑歌曲文件命名模板
- `--template-file-playlist`: 播放列表文件命名模板

## 模板变量

可用于文件夹/文件命名模板或 `exclude_tags` 列表的变量：

| 变量名 | 描述 |
|--------|------|
| album | 专辑名称 |
| album_artist | 专辑艺术家 |
| album_id | 专辑ID |
| artist | 艺术家名称 |
| artist_id | 艺术家ID |
| comments | 评论 |
| compilation | 合辑标识 |
| composer | 作曲家 |
| copyright | 版权信息 |
| date | 日期 |
| disc | 碟片编号 |
| disc_total | 总碟片数 |
| genre | 流派 |
| genre_id | 流派ID |
| lyrics | 歌词 |
| media_type | 媒体类型 |
| title | 标题 |
| track | 音轨编号 |
| track_total | 总音轨数 |
| url | URL |

## 下载模式

- `ytdlp`：默认模式，稳定可靠
- `nm3u8dlre`：速度更快的替代模式

## 混流模式

- `ffmpeg`：默认模式，功能全面
- `mp4box`：替代模式（不转换音乐视频中的隐藏式字幕）

## 音频编码格式

### 稳定支持
- `aac-legacy`：AAC 256kbps 44.1kHz
- `aac-he-legacy`：AAC-HE 64kbps 44.1kHz

### 实验性编码
注意：由于 API 限制，以下编码可能无法正常工作
- `aac`：AAC 256kbps
- `aac-he`：AAC-HE 64kbps
- `aac-binaural`：AAC 空间音频（双耳）
- `aac-downmix`：AAC 空间音频（缩混）
- `aac-he-binaural`：AAC-HE 空间音频（双耳）
- `aac-he-downmix`：AAC-HE 空间音频（缩混）
- `atmos`：杜比全景声
- `ac3`：杜比数字
- `alac`：Apple 无损音频编解码器

## 音乐视频编码

- `h264`：最高 1080p + AAC 256kbps
- `h265`：最高 2160p + AAC 256kbps
- `ask`：手动选择可用编码

## 帖子视频质量

- `best`：最高 1080p + AAC 256kbps
- `ask`：手动选择画质

## 同步歌词格式

- `lrc`：轻量通用格式
- `srt`：SubRip 格式（时间戳更精确）
- `ttml`：Apple 原生格式（多数播放器不支持）

## 封面格式

- `jpg`：默认格式
- `png`：无损格式
- `raw`：原始未处理文件（需开启 `save_cover`）

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情