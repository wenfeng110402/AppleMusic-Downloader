# Apple Music 下载器

初中生写的一个功能强大的 Apple Music 下载工具，基于gamdl，增加了图形化界面

Donate（non-porfit,no tax)
[here！](https://hcb.hackclub.com/donations/start/amdl)

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/wenfeng110402/AppleMusic-Downloader)](LICENSE)

## 致谢 / Acknowledgments

本项目使用了 [gamdl (Glomatico's Apple Music Downloader)](https://github.com/glomatico/gamdl) 的代码。我们衷心感谢 [Glomatico](https://github.com/glomatico) 和所有 gamdl 的贡献者们为开源社区所做的杰出工作。

This project utilizes code from [gamdl (Glomatico's Apple Music Downloader)](https://github.com/glomatico/gamdl). We sincerely thank [Glomatico](https://github.com/glomatico) and all contributors to gamdl for their outstanding work in the open-source community.

## 功能特性

- 🎵 **高品质音频下载** - 支持 AAC 256kbps 等多种编码格式
- 🎬 **高清音乐视频** - 支持最高 1080p 分辨率下载
- 👤 **艺术家作品批量下载** - 通过多个链接或专辑歌单链接下载
- 📊 **实时下载进度** - 显示每首歌曲的下载进度，让你了解下载状态
- ✅ **选择性下载** - 从专辑或播放列表中选择特定歌曲进行下载
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

## 使用方法

### 图形界面（GUI）

运行程序后，在图形界面中：

1. **输入URL** - 在URL输入框中输入 Apple Music 链接（可多行输入多个链接）
2. **选择Cookie文件** - 点击"浏览"选择你的 cookies.txt 文件
3. **设置输出目录** - 选择音乐下载保存的位置
4. **配置下载选项**：
   - ✅ **选择要下载的歌曲** - 勾选此选项后，下载专辑或播放列表时会弹出选择界面，让你挑选想要下载的歌曲
   - 覆盖已存在文件
   - 保存播放列表
   - 其他高级选项...
5. **点击"开始下载"** - 程序会显示：
   - 总体进度条：显示所有URL的下载进度
   - 当前歌曲进度条：显示正在下载的歌曲进度
   - 实时日志：查看详细的下载信息

### 命令行（CLI）

基本用法：
```bash
python -m gamdl [OPTIONS] URLS...
```

#### 新增选项

**选择性下载**：
```bash
# 下载专辑时选择特定歌曲
python -m gamdl --select-tracks "https://music.apple.com/cn/album/..."

# 下载播放列表时选择特定歌曲
python -m gamdl --select-tracks "https://music.apple.com/cn/playlist/..."
```

启用 `--select-tracks` 选项后，程序会显示一个交互式菜单，列出所有可用的歌曲，你可以使用方向键和空格键选择要下载的歌曲。

#### 其他常用选项

```bash
# 指定Cookie文件
python -m gamdl -c /path/to/cookies.txt "URL"

# 指定输出目录
python -m gamdl -o /path/to/output "URL"

# 覆盖已存在的文件
python -m gamdl --overwrite "URL"

# 保存专辑封面为独立文件
python -m gamdl -s "URL"

# 查看所有选项
python -m gamdl --help
```

### 下载进度显示

程序会实时显示：
- **总体进度**：当前处理的URL进度（例如：URL 1/3）
- **歌曲进度**：当前下载的歌曲在专辑/播放列表中的位置（例如：Track 5/12）
- **下载状态**：正在下载、解密、混流、应用标签等各个步骤的进度
- **完成信息**：下载完成后会显示最终路径和统计信息

## 免责声明 / Disclaimer

本工具仅供学习与研究使用，严禁将其用于任何违反法律法规或侵犯他人权益的用途。  
This tool is for educational and research purposes only. Any use that violates laws or infringes on the rights of others is strictly prohibited.

1. 本项目不直接提供或存储任何受版权保护的内容，用户需自行提供合法的凭证（如有效的 Apple Music 订阅和 Cookies 文件）以使用相关功能。  
   This project does not directly provide or store any copyrighted content. Users must independently provide valid credentials (e.g., a valid Apple Music subscription and cookie files) to use its features.

2. 本人不对用户如何使用本工具承担任何责任，因使用本工具产生的任何法律或版权争议，均由用户自行承担。  
   I (or the development team) assume no responsibility for how users use this tool. Any legal or copyright disputes arising from its use are the sole responsibility of the user.

3. 本项目基于 [gamdl](https://github.com/glomatico/gamdl) 提供的代码实现，与原项目的作者无直接关联。如有任何异议，请联系本人以便协助处理。  
   This project is implemented based on code from [gamdl](https://github.com/glomatico/gamdl) and is not directly affiliated with the original project's authors. If there are any objections, please contact me for assistance.

4. 用户在使用本工具时，应自行确保符合当地相关法律法规。  
   Users must ensure compliance with local laws and regulations when using this tool.

By using this tool, you agree to comply with all applicable laws and assume full responsibility for your actions.  
通过使用本工具，您同意遵守所有适用法律，并对您的行为承担全部责任。
