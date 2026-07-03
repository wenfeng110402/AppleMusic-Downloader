# TODO — AppleMusic Downloader (amdl) — 重构清单

> **新架构方向**: 直接依赖 gamdl v3.8+，不再自维护 Apple Music API / 下载 / 解密代码。  
> applemusic-dl 变为 gamdl 的薄封装层，保留：GUI (PyQt6+Fluent) + 格式转换 + wrapper 自动部署命令。  
> 勾选一个，完成一个！💪

---

## 一、🔴 核心架构迁移

> 将项目从自维护的 gamdl fork 迁移到直接依赖 `gamdl` 库。  
> 这是重构的根基，建议按顺序执行。

### Phase 1 — 依赖与骨架

- [ ] **1.1 添加 gamdl 依赖**
  - `pyproject.toml` 添加 `gamdl >= 3.8`，`requirements.txt` 同步
  - 移除 `pywidevine` 直接依赖（gamdl 自带）
  - 移除 `InquirerPy` 重依赖（gamdl 内部管理交互式提示）

- [ ] **1.2 重写 `cli.py` → 调用 gamdl CLI**
  - 删除当前 Click 命令定义（参数、config 加载、枚举映射等）
  - 改为直接调用 `gamdl.cli.cli.main()`，将 `argv` 透传
  - 保留 `amdl` 命令入口，行为与 `gamdl` 一致

- [ ] **1.3 重写 `core_downloader.py` → 薄封装 gamdl Embedding API**
  - 删除所有内部 downloader 调用
  - 改为异步调用 gamdl 的 `AppleMusicDownloader` + `AppleMusicApi`
  - 保留 `download_urls()` 函数签名兼容性（同步封装异步）
  - 保留 `progress_callback` / `log_callback` 透传

- [ ] **1.4 重写 `download_worker.py` → 调用新 `core_downloader`**
  - 删除 `_SONG_CODEC_MAP` 等枚举映射（gamdl 原生支持）
  - 同步适配新 `core_downloader` 的函数签名

- [ ] **1.5 重写 GUI 下载逻辑 → 适配 gamdl**
  - `fluent_gui.py` `start_download()` 适配新接口
  - `ui_builder.py` 选项与 gamdl 配置对齐（codec 命名等）

- [ ] **1.6 重写 `settings_store.py` → 适配 gamdl 配置**
  - 配置项对齐 gamdl 的 `CliConfig` / `config.ini` 格式
  - 保留原有持久化机制，选项映射到 gamdl 命名

### Phase 2 — 文件清理

- [ ] **1.7 删除废弃文件**
  - `downloader.py` — 整个文件删除（功能由 gamdl 接管）
  - `downloader_song.py` — 删除
  - `downloader_song_legacy.py` — 删除
  - `downloader_music_video.py` — 删除
  - `downloader_post.py` — 删除
  - `apple_music_api.py` — 删除
  - `itunes_api.py` — 删除
  - `hardcoded_wvd.py` — 删除
  - `custom_formatter.py` — 删除
  - `models.py` — 删除
  - `enums.py` — 删除（如 GUI 引用则保留映射 shim）
  - `constants.py` — 大部分删除，保留 GUI 可能需要的内容

- [ ] **1.8 清理 `utils.py`**
  - 删除 `raise_response_exception`、`color_text`（gamdl 内部处理）
  - 保留 `get_subprocess_startupinfo`、`resource_path`、`prepend_tools_to_path`
  - 保留格式转换相关工具函数

- [ ] **1.9 清理 `AppleMusicDownloader.spec`**
  - 从 `hiddenimports` 中移除已删除模块
  - 添加 `gamdl` 及其子模块

- [ ] **1.10 清理 `pyproject.toml`**
  - 移除不再需要的 `dependencies` 列表
  - `inquirerpy`、`m3u8`、`mutagen`、`pillow`、`pywidevine`、`pyyaml`、`termcolor`、`yt-dlp` 由 gamdl 传递依赖
  - 保留 `PyQt6`、`PyQt6-Fluent-Widgets`、`click`、`colorama`

---

## 二、🟡 格式转换 (保留 + 增强)

- [ ] **2.1 确认 `gui_conversion.py` 独立运作**
  - 验证不依赖已删除模块
  - 确保 `resolve_ffmpeg_executable`、`convert_audio_file`、`convert_video_file` 正常

- [ ] **2.2 GUI 格式转换选项对齐**
  - 确保 `audio_format` / `video_format` 组合框值有效
  - 格式转换默认关闭（keep original）

- [ ] **2.3 CLI 模式下的格式转换**
  - 新增 `--audio-format` / `--video-format` CLI 参数
  - 下载完成后自动调起转换

---

## 三、🟡 Wrapper 自动部署

> wrapper-v2 是用于下载 ALAC (无损) 的可选依赖服务。

- [ ] **3.1 新建 `wrapper_manager.py`**
  - `install_wrapper()` — 检测系统，下载/安装 [wrapper-v2](https://github.com/glomatico/wrapper-v2)
  - `start_wrapper()` — 启动 wrapper 服务 (systemd/launchd/Windows Service)
  - `stop_wrapper()` / `status_wrapper()`
  - 支持 `amdl wrapper install`、`amdl wrapper start`、`amdl wrapper status`

- [ ] **3.2 跨平台支持**
  - macOS: `launchd` plist 自启动
  - Linux: `systemd` service
  - Windows: NSSM 或 Windows Service

- [ ] **3.3 wrapper 配置管理**
  - `amdl wrapper config` — 设置 wrapper URL、端口、凭据
  - 配置持久化到 `~/.amdl/wrapper_config.json`

- [ ] **3.4 GUI wrapper 状态面板**
  - 设置页显示 wrapper 连接状态
  - 提供"启动/停止 wrapper"按钮

---

## 四、🟡 新增功能

- [ ] **4.1 自动检查更新**
  - GUI/CLI 启动时异步检查 GitHub Releases

- [ ] **4.2 macOS / Linux 原生打包**
  - macOS: `.app` + DMG（`py2app` 或 `briefcase`）
  - Linux: AppImage 或 Flatpak

- [ ] **4.3 下载历史记录**
  - 新建 `history_store.py`，记录已下载 URL/ID
  - 可选：与 gamdl 的 SQLite database 互通

- [ ] **4.4 下载完成后系统通知**
  - macOS `pyobjc` / Windows `win10toast` / Linux `notify-send`

---

## 五、🟡 代码质量与测试

- [ ] **5.1 添加单元测试**
  - 新建 `tests/`，`pytest` 覆盖：
    - 新 `core_downloader` 接口
    - `gui_conversion` 工具函数
    - `wrapper_manager` 配置读写
    - `settings_store` 持久化

- [ ] **5.2 CI 适配 + 自动化测试**
  - 更新 `.github/workflows/ci-build-windows.yml`
  - 添加 `pytest` 步骤
  - 验证 gamdl 可正常导入

- [ ] **5.3 类型注解完善**
  - 新代码要求完整类型注解
  - 启用 `mypy` 严格模式

---

## 六、🟢 GUI 改进

- [ ] **6.1 GUI 选项与 gamdl 全对齐**
  - codec 选项：aac-web / aac-he-web / aac / alac / atmos / ac3 等
  - 同步歌词格式：lrc / srt / ttml
  - 封面格式：jpg / png / raw
  - MV 分辨率选项
  - MV 混流格式选项

- [ ] **6.2 模板参数插入功能修复**
  - `ui_builder.py` 连接 `template_param_combo` / `template_param_insert_btn`

- [ ] **6.3 GUI 暴露所有模板设置**
  - 添加 `template_folder_no_album`、`template_file_no_album`、`template_file_playlist`

- [ ] **6.4 进度显示细化**
  - 显示当前下载文件名 / 百分比 / 预估剩余时间

- [ ] **6.5 下载按钮状态完善**
  - 失败时保留错误上下文

- [ ] **6.6 设置持久化覆盖所有选项**

- [ ] **6.7 GUI 主题切换**
  - 设置页添加浅色/深色/跟随系统

- [ ] **6.8 Cookie 拖拽支持**

- [ ] **6.9 下载队列管理**
  - 多任务队列，暂停/恢复/取消

---

## 七、🟢 文档与社区

- [ ] **7.1 更新 README**
  - 说明新架构：applemusic-dl = gamdl 封装 + GUI + 格式转换
  - CLI 参数说明
  - wrapper 安装使用说明
  - FAQ

- [ ] **7.2 添加 CHANGELOG**
  - `CHANGELOG.md`，重点记录 v3.0 架构变更

- [ ] **7.3 添加 `CONTRIBUTING.md`**

- [ ] **7.4 GitHub Issue / PR 模板**

---

## 八、🟢 打包与部署

- [ ] **8.1 PyInstaller spec 更新**
  - 移除已删模块的 hiddenimports
  - 添加 `gamdl`、`httpx`、`structlog` 等新依赖
  - 移除无效的 `'ffmpeg'` hiddenimport

- [ ] **8.2 NSIS 版本号同步**
  - `AppleMusicDownloader.nsi` 版本号与 `__init__.py` 统一

- [ ] **8.3 PyPI 发布流程加固**
  - 版本验证步骤

- [ ] **8.4 NSIS 安装程序集成 wrapper**
  - 可选：安装时询问是否同时部署 wrapper-v2 服务

---

## 九、🟢 远期规划

- [ ] **9.1 Web UI（FastAPI + Vue/React）**
- [ ] **9.2 移动端支持（iOS/Android）**

---

## 完成进度

> **总计 48 项** · 🔴 10 项 · 🟡 11 项 · 🟢 27 项

| 类别 | 总数 | 已完成 |
|------|:----:|:------:|
| 🔴 架构迁移 Phase 1 | 6 | 0 |
| 🔴 架构迁移 Phase 2 | 4 | 0 |
| 🟡 格式转换 | 3 | 0 |
| 🟡 Wrapper 自动部署 | 4 | 0 |
| 🟡 新增功能 | 4 | 0 |
| 🟡 代码质量 | 3 | 0 |
| 🟢 GUI 改进 | 9 | 0 |
| 🟢 文档社区 | 4 | 0 |
| 🟢 打包部署 | 4 | 0 |
| 🟢 远期规划 | 2 | 0 |
| **总计** | **48** | **0** |

> 最后更新: 2026-07-02 · 架构方向: gamdl v3.8+ 直接依赖

### 7.1 使用 gamdl 作为核心库
- 评估将 `gamdl` 作为直接依赖的可行性，减少维护重复的下游代码

### 7.2 可选的自动部署 Wrapper
- 将 `applemusic-dl` 包重构为 gamdl + wrapper 的整合方案
- 注意：wrapper 在 Windows 部署困难是已知问题

### 7.3 Web UI
- 使用 FastAPI + Vue/React 构建 Web 界面，实现远程下载管理

### 7.4 移动端支持
- 评估通过 API 暴露核心功能，构建 iOS/Android 客户端

---

## 版本追踪

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-02 | v2.4.5 | 初次全面整理 TODO，列出 7 大类 30+ 项任务 |
