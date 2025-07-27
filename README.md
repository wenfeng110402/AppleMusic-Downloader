# Apple Music 下载器  
一款用于下载Apple Music歌曲、音乐视频和帖视频的Python命令行工具    

## 功能特点  
* **高品质音频**：支持AAC 256kbps等多种编码格式下载  
* **高清音乐视频**：支持最高4K分辨率的音乐视频下载  
* **同步歌词**：支持LRC、SRT和TTML格式的同步歌词下载  
* **艺术家支持**：通过艺术家链接下载其所有专辑或音乐视频  
* **高度可定制**：为高级用户提供丰富的配置选项  

## 环境要求  
* **Python 3.9或更高版本**  
* **Netscape格式的Cookies文件**（需有效订阅）  
    * **Firefox**：使用[Export Cookies](https://addons.mozilla.org/addon/export-cookies-txt)扩展  
    * **Chromium内核浏览器**：使用[Open Cookies.txt](https://chromewebstore.google.com/detail/open-cookiestxt/gdocmgbfkjnnpapoeobnolbbkoibbcif)扩展  
* **系统PATH中需有FFmpeg**  
    * **Windows**：从[AnimMouse的FFmpeg构建版](https://github.com/AnimMouse/ffmpeg-stable-autobuild/releases)下载  
    * **Linux**：从[John Van Sickle的FFmpeg构建版](https://johnvansickle.com/ffmpeg/)下载  

### 可选依赖  
以下工具为特定功能所需，需加入系统PATH或通过命令行参数/配置文件指定路径：  
* [mp4decrypt](https://www.bento4.com/downloads/)：`mp4box`混流模式、音乐视频下载和实验性音频编码必需  
* [MP4Box](https://gpac.io/downloads/gpac-nightly-builds/)：`mp4box`混流模式必需  
* [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE/releases/latest)：`nm3u8dlre`下载模式必需  

## 安装指南  
1. 通过pip安装`gamdl`包  
    ```bash  
    pip install gamdl  
    ```  
2. 配置Cookies文件  
    * 将cookies文件移动到运行目录并重命名为`cookies.txt`  
    * 或通过命令行参数/配置文件指定路径  

## 使用说明  
运行命令：  
```bash  
gamdl [选项] 网址...  
```  

### 支持链接类型  
* 单曲  
* 专辑  
* 播放列表  
* 音乐视频  
* 艺术家主页  
* 帖视频  

### 使用示例  
* 下载单曲：  
    ```bash  
    gamdl "https://music.apple.com/us/album/never-gonna-give-you-up-2022-remaster/1624945511?i=1624945512"  
    ```  
* 下载整张专辑：  
    ```bash  
    gamdl "https://music.apple.com/us/album/whenever-you-need-somebody-2022-remaster/1624945511"  
    ```  
* 下载艺术家作品：  
    ```bash  
    gamdl "https://music.apple.com/us/artist/rick-astley/669771"  
    ```  

### 交互式操作控制  
* **方向键**：移动选择  
* **空格键**：切换选中状态  
* **Ctrl + A**：全选  
* **回车键**：确认选择  

## 配置选项  
可通过命令行参数或配置文件（首次运行时自动创建于`~/.gamdl/config.json`或`%USERPROFILE%\.gamdl\config.json`）进行配置。  

配置项可通过命令行参数覆盖：  

| 命令行参数 / 配置文件键                  | 描述                                                                 | 默认值                     |
|------------------------------------------|----------------------------------------------------------------------|----------------------------|
| `--disable-music-video-skip`             | 不跳过专辑/播放列表中的音乐视频下载                                   | `false`                    |
| `--save-cover`, `-s`                     | 将封面另存为单独文件                                                  | `false`                    |
| `--overwrite`                            | 覆盖已存在文件                                                        | `false`                    |
| `--read-urls-as-txt`, `-r`               | 将URL参数视为含换行分隔URL的文本文件路径                              | `false`                    |
| `--save-playlist`                        | 下载播放列表时生成M3U8文件                                            | `false`                    |
| `--synced-lyrics-only`                   | 仅下载同步歌词                                                        | `false`                    |
| `--no-synced-lyrics`                     | 不下载同步歌词                                                        | `false`                    |
| `--config-path`                          | 配置文件路径                                                          | `<home>/.gamdl/config.json`|
| `--log-level`                            | 日志级别                                                              | `INFO`                     |
| `--no-exceptions`                        | 不打印异常信息                                                        | `false`                    |
| `--cookies-path`, `-c`                   | Cookies文件路径                                                       | `./cookies.txt`            |
| `--language`, `-l`                       | 元数据语言（ISO-2A代码，视频不一定生效）                              | `en-US`                    |
| `--output-path`, `-o`                    | 输出目录路径                                                          | `./Apple Music`            |
| `--temp-path`                            | 临时目录路径                                                          | `./temp`                   |
| `--wvd-path`                             | .wvd文件路径                                                          | `null`                     |
| `--nm3u8dlre-path`                       | N_m3u8DL-RE可执行文件路径                                             | `N_m3u8DL-RE`              |
| `--mp4decrypt-path`                      | mp4decrypt可执行文件路径                                              | `mp4decrypt`               |
| `--ffmpeg-path`                          | FFmpeg可执行文件路径                                                  | `ffmpeg`                   |
| `--mp4box-path`                          | MP4Box可执行文件路径                                                  | `MP4Box`                   |
| `--download-mode`                        | 下载模式                                                              | `ytdlp`                    |
| `--remux-mode`                           | 混流模式                                                              | `ffmpeg`                   |
| `--cover-format`                         | 封面格式                                                              | `jpg`                      |
| `--template-folder-album`                | 专辑曲目的文件夹命名模板                                              | `{album_artist}/{album}`   |
| `--template-folder-compilation`          | 合辑专辑的文件夹命名模板                                              | `Compilations/{album}`     |
| `--template-file-single-disc`            | 单碟专辑曲目的文件名模板                                              | `{track:02d} {title}`      |
| `--template-file-multi-disc`             | 多碟专辑曲目的文件名模板                                              | `{disc}-{track:02d} {title}`|
| `--template-folder-no-album`             | 非专辑曲目的文件夹命名模板                                            | `{artist}/Unknown Album`   |
| `--template-file-no-album`               | 非专辑曲目的文件名模板                                                | `{title}`                  |
| `--template-file-playlist`               | M3U8播放列表的命名模板                                                | `Playlists/{playlist_title}`|
| `--template-date`                        | 日期标签格式                                                          | `%Y-%m-%dT%H:%M:%SZ`       |
| `--exclude-tags`                         | 要排除的标签（逗号分隔）                                              | `null`                     |
| `--cover-size`                           | 封面尺寸                                                              | `1200`                     |
| `--truncate`                             | 文件/文件夹名称最大长度                                               | `null`                     |
| `--codec-song`                           | 音频编码格式                                                          | `aac-legacy`               |
| `--synced-lyrics-format`                 | 同步歌词格式                                                          | `lrc`                      |
| `--codec-music-video`                    | 音乐视频编码格式                                                      | `h264`                     |
| `--quality-post`                         | 帖视频质量                                                            | `best`                     |
| `--no-config-file`, `-n`                 | 不使用配置文件                                                        | `false`                    |

### 模板变量  
可用于文件夹/文件命名模板或`exclude_tags`列表的变量：  
（完整列表保留原文变量名，如`album`, `artist_id`等）

### 混流模式  
* `ffmpeg`：默认模式  
* `mp4box`：替代模式（不转换音乐视频中的隐藏式字幕）  

### 下载模式  
* `ytdlp`：默认模式  
* `nm3u8dlre`：比`ytdlp`更快  

### 音频编码格式  
* 稳定支持：  
    * `aac-legacy`：AAC 256kbps 44.1kHz  
    * `aac-he-legacy`：AAC-HE 64kbps 44.1kHz  
* 实验性编码（因API限制可能失效）：  
    （完整列表保留原文技术术语，如`atmos`, `alac`等）  

### 音乐视频编码  
* `h264`：最高1080p + AAC 256kbps  
* `h265`：最高2160p + AAC 256kbps  
* `ask`：手动选择可用编码  

### 帖视频质量  
* `best`：最高1080p + AAC 256kbps  
* `ask`：手动选择画质  

### 同步歌词格式  
* `lrc`：轻量通用格式  
* `srt`：SubRip格式（时间戳更精确）  
* `ttml`：Apple原生格式（多数播放器不支持）  

### 封面格式  
* `jpg`：默认格式  
* `png`：无损格式  
* `raw`：原始未处理文件（需开启`save_cover`）  
