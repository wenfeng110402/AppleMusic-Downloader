# AppleMusic Downloader

![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/wenfeng110402/AppleMusic-Downloader/total?style=social&logo=GitHub)

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Platform](<https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey>)](https://github.com/wenfeng110402/AppleMusic-Downloader)
![GitHub License](https://img.shields.io/github/license/wenfeng110402/AppleMusic-Downloader?style=social)

- [English README](README_en.md)

---

AppleMusic Downloader 是一个功能强大的 Apple Music 下载工具，支持下载歌曲、音乐视频、歌词和封面。

项目提供三种使用方式：

| 方式                 | 适用场景                                                 |
| -------------------- | -------------------------------------------------------- |
| **CLI 命令行** | 终端用户，通过`pip install applemusic-dl` 安装即可使用 |
| **API 服务**   | 开发者，将下载能力集成到自己的应用中                     |
| **桌面应用**   | 普通用户，下载打包好的安装程序直接使用                   |

---

## 致谢

本项目使用了 [gamdl (Glomatico&#39;s Apple Music Downloader)](https://github.com/glomatico/gamdl) 和 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的代码。衷心感谢 gamdl 和 yt-dlp 的所有贡献者在开源社区做出的杰出贡献。

---

## 目录

- [安装方式](#安装方式)
  - [方式一：pip 安装（推荐）](#方式一pip-安装推荐)
  - [方式二：桌面安装程序](#方式二桌面安装程序仅限-windows)
  - [方式三：从源码运行](#方式三从源码运行)
- [CLI 命令行使用](#cli-命令行使用)
- [API 服务部署](#api-服务部署)
  - [启动 API 服务](#启动-api-服务)
  - [API 端点概览](#api-端点概览)
  - [API 客户端示例](#api-客户端示例)
- [前端部署](#前端部署)
  - [前端功能特性](#前端功能特性)
  - [开发模式](#开发模式)
  - [生产模式](#生产模式)
- [桌面应用](#桌面应用)
- [环境要求](#环境要求)
- [支持的链接类型](#支持的链接类型)
- [项目结构](#项目结构)
- [免责声明](#免责声明)

---

## 安装方式

### 方式一：pip 安装（推荐）

```bash
pip install applemusic-dl
```

安装后可直接使用 `amdl` 命令：

```bash
amdl --help
```

如果需要桌面 GUI 模式，请安装带桌面依赖的版本：

```bash
pip install applemusic-dl[desktop]
```

### 方式二：桌面安装程序（仅限 Windows）

1. 从 [Releases](https://github.com/wenfeng110402/AppleMusic-Downloader/releases) 页面下载最新安装程序
2. 运行 `AppleMusicDownloader_Setup.exe` 按提示完成安装
3. 在开始菜单中找到 "Apple Music Downloader"

### 方式三：从源码运行

```bash
git clone https://github.com/wenfeng110402/AppleMusic-Downloader.git
cd AppleMusic-Downloader
pip install -r requirements.txt
pip install -e .
```

---

## CLI 命令行使用

```bash
# 查看帮助
amdl --help

# 下载单曲
amdl -c /path/to/cookies.txt "https://music.apple.com/cn/album/left-and-right/1630451412?i=1630451413"

# 下载整张专辑
amdl -c /path/to/cookies.txt "https://music.apple.com/cn/album/left-and-right/1630451412"

# 指定输出目录
amdl -c /path/to/cookies.txt -o "./My Music" "https://music.apple.com/..."

# 指定音频编码和格式
amdl -c /path/to/cookies.txt --codec-song aac-256k --audio-format mp3 "https://music.apple.com/..."
```

---

## API 服务部署

项目内置了 FastAPI 后端，可独立部署为 API 服务，供其他应用调用。

### 启动 API 服务

```bash
# 安装后直接启动
python -m amdl --server

# 自定义端口
python -m amdl --server --port 8080

# 允许外部访问（生产环境请配置反向代理）
python -m amdl --server --host 0.0.0.0 --port 8000
```

服务启动后访问 `http://127.0.0.1:8000` 可查看 API 文档（Swagger UI）。

### API 端点概览

| 方法      | 路径                     | 说明                                |
| --------- | ------------------------ | ----------------------------------- |
| GET       | `/api/health`          | 健康检查                            |
| GET       | `/api/info`            | 获取支持的编码、格式等选项          |
| GET       | `/api/dependencies`    | 检查外部依赖（ffmpeg, N_m3u8DL-RE） |
| POST      | `/api/tasks`           | 提交下载任务                        |
| GET       | `/api/tasks`           | 获取所有任务列表                    |
| GET       | `/api/tasks/{task_id}` | 获取单个任务详情                    |
| DELETE    | `/api/tasks/{task_id}` | 取消任务                            |
| WebSocket | `/api/ws/{task_id}`    | 实时下载进度推送                    |
| GET       | `/api/settings`        | 读取用户偏好设置                    |
| POST      | `/api/settings`        | 保存用户偏好设置                    |
| DELETE    | `/api/temp`            | 清理临时目录                        |

详细 API 文档请参见 [docs/api.md](docs/api.md)。

### API 客户端示例

**Python 调用：**

```python
import requests

# 提交下载任务
resp = requests.post("http://127.0.0.1:8000/api/tasks", json={
    "urls": ["https://music.apple.com/cn/album/left-and-right/1630451412?i=1630451413"],
    "cookies_path": "/path/to/cookies.txt",
    "output_path": "./Apple Music"
})
task = resp.json()
print(f"Task ID: {task['task_id']}")

# 查询任务状态
import time
while True:
    status = requests.get(f"http://127.0.0.1:8000/api/tasks/{task['task_id']}").json()
    print(f"Status: {status['status']}, Progress: {status['progress']}")
    if status["status"] in ("completed", "failed", "cancelled"):
        break
    time.sleep(3)
```

**curl 调用：**

```bash
# 提交任务
curl -X POST http://127.0.0.1:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://music.apple.com/cn/album/left-and-right/1630451412"],
    "cookies_path": "/path/to/cookies.txt"
  }'

# 查询任务
curl http://127.0.0.1:8000/api/tasks/<task_id>
```

**WebSocket 实时进度（Python）：**

```python
import asyncio
import websockets
import json

async def listen_progress(task_id: str):
    uri = f"ws://127.0.0.1:8000/api/ws/{task_id}"
    async with websockets.connect(uri) as ws:
        # 发送 ping 保持连接
        await ws.send(json.dumps({"type": "ping"}))
        async for msg in ws:
            data = json.loads(msg)
            print(f"进度: {data}")
            if data.get("type") == "completed":
                break

asyncio.run(listen_progress("your-task-id"))
```

---

## 前端部署

项目包含一个基于 Next.js 的 Web 前端，可直接部署供用户使用。

### 前端功能特性

Web 前端提供了一套完整的图形界面，包括：

- **中/英双语界面（i18n）** — 一键切换语言
- **深色/浅色主题** — CSS 变量驱动，支持明暗切换
- **后端在线状态指示** — 侧边栏红绿点实时反馈后端状态
- **下载表单** — 支持多 URL 输入、文件浏览选择器（桌面端调用系统对话框）
- **音频格式选择** — 支持 MP3/FLAC/WAV/AAC 等格式转换
- **设置持久化** — 每次修改自动保存至后端，刷新不丢失
- **下载队列** — 实时任务列表、进度条、自动刷新（3 秒间隔）
- **任务日志** — 可展开查看每个任务的详细运行日志
- **依赖检测** — 一键检查 FFmpeg / N_m3u8DL-RE 等外部工具是否就绪
- **深色风格 UI** — 磨砂玻璃质感、沉浸式暗黑设计

### 开发模式

```bash
cd src/fronted
npm install
npm run dev
```

开发模式下前端运行在 `http://localhost:3000`，API 请求自动代理到 `http://127.0.0.1:8000`。

需要同时启动后端：

```bash
python -m amdl --server
```

### 生产模式

```bash
cd src/fronted
npm install
npm run build
```

构建产物在 `src/fronted/out/` 目录，可直接部署到任意静态文件服务器（Nginx、Caddy 等）。

**Nginx 配置示例：**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    root /path/to/src/fronted/out;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Docker 部署：**

```bash
# 后端
docker run -d --name amdl-api \
  -p 8000:8000 \
  -v /path/to/cookies.txt:/cookies.txt \
  -v /path/to/output:/output \
  --restart unless-stopped \
  python:3.10-slim \
  sh -c "pip install applemusic-dl && python -m amdl --server --host 0.0.0.0"

# 前端（使用 Nginx 提供静态文件）
docker run -d --name amdl-frontend \
  -p 80:80 \
  -v /path/to/src/fronted/out:/usr/share/nginx/html \
  --restart unless-stopped \
  nginx:alpine
```

---

## 桌面应用

在桌面模式下，后端服务和前端 Web UI 集成在同一个窗口中：

```bash
# 启动桌面应用
python -m amdl --desktop

# 或直接启动（自动检测）
python -m amdl
```

桌面应用基于 pywebview，在 Windows、macOS、Linux 上均可用。

> **🐧 Linux 用户请注意**：pywebview 在 Linux 上依赖 Qt WebEngine，启动桌面模式前需要先安装系统依赖：
>
> ```bash
> sudo apt update && sudo apt install -y python3-pyqt5 python3-pyqt5.qtwebengine libqt5webkit5-dev
> pip install pywebview[qt]
> ```

---

## 环境要求

### 必需

- Python 3.10 或更高版本
- 有效的 Apple Music 订阅
- Netscape 格式的 Cookies 文件
- FFmpeg

**获取 Cookies 文件：**

- Firefox 用户：使用 [Export Cookies](https://addons.mozilla.org/firefox/addon/export-cookies-txt/) 扩展
- Chromium 用户：使用 [Open Cookies.txt](https://chromewebstore.google.com/detail/open-cookiestxt/gdocmgbfkjnnpapoeobnolbbkoibbcif) 扩展

**安装 FFmpeg：**

- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg` / `pacman -S ffmpeg`
- Windows: 从 [ffmpeg.org](https://ffmpeg.org/) 下载

### 可选

- [mp4decrypt](https://www.bento4.com/downloads/)：用于音乐视频下载和实验性音频编码
- [MP4Box](https://gpac.io/downloads/gpac-nightly-builds/)：替代混流模式
- [N_m3u8DL-RE](https://github.com/nilaoda/N_m3u8DL-RE/releases/latest)：替代下载模式

---

## 支持的链接类型

- 单曲
- 专辑
- 播放列表
- 音乐视频
- 艺术家主页
- 帖子视频

---

## 项目结构

```
AppleMusic-Downloader/
├── src/
│   ├── amdl/              # Python 后端包
│   │   ├── server.py      # FastAPI 服务入口
│   │   ├── cli.py         # CLI 命令行入口
│   │   ├── core_downloader.py  # 下载核心逻辑
│   │   ├── task_manager.py     # 任务队列管理
│   │   ├── converter.py        # 格式转换
│   │   └── ...
│   └── fronted/           # Next.js 前端
│       ├── app/
│       │   ├── components/  # 前端组件
│       │   ├── service.tsx  # API 调用封装
│       │   └── i18n.tsx     # 国际化
│       └── next.config.ts
├── docs/
│   └── api.md             # API 文档
├── pyproject.toml          # 包配置
├── requirements.txt
└── README.md
```

---

## 免责声明

本工具仅供学习与研究使用，严禁将其用于任何违反法律法规或侵犯他人权益的用途。

1. 本项目不直接提供或存储任何受版权保护的内容，用户需自行提供合法的凭证（如有效的 Apple Music 订阅和 Cookies 文件）以使用相关功能。
2. 本人不对用户如何使用本工具承担任何责任，因使用本工具产生的任何法律或版权争议，均由用户自行承担。
3. 本项目基于 [gamdl](https://github.com/glomatico/gamdl) 和 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 提供的代码实现，与原项目的作者无直接关联。如有任何异议，请联系本人以便协助处理。
4. 用户在使用本工具时，应自行确保符合当地相关法律法规。

By using this tool, you agree to comply with all applicable laws and assume full responsibility for your actions.
