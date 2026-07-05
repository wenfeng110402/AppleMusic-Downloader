# TODO — AppleMusic Downloader

> 架构：**FastAPI 后端**（`amdl/`）+ **Flutter 前端**（`gui/`）
> 后端基于 gamdl 封装，提供 REST API + WebSocket 实时推送。
> 支持平台：Web / Windows / Linux / macOS

---

## 一、🟡 后端 API 完善

### Phase 1 — 核心功能

- [X] **1.1 `server.py` 基础 API**

  - `GET /api/health` — 健康检查
  - `GET /api/info` — 返回支持的枚举值（编解码器、封面格式等），供前端动态渲染
  - `POST /api/download` — 简单下载（同步等待）
- [ ] **1.2 实时进度推送（WebSocket）**

  - `WS /api/ws/{task_id}` — 订阅下载进度
  - 使用 `progress_callback` → `asyncio.run_coroutine_threadsafe` → WebSocket 广播
  - 消息格式：`{"type":"progress", "completed":3, "total":10, "percent":30.0}`
  - 参考：[task_manager.py](file:///Users/cret/Desktop/AppleMusic-Downloader/src/amdl/task_manager.py)
- [ ] **1.3 多任务队列管理**

  - `POST /api/tasks` — 提交下载任务，返回 `task_id`
  - `GET /api/tasks` — 获取所有任务列表（按时间倒序）
  - `GET /api/tasks/{task_id}` — 获取单个任务详情
  - `DELETE /api/tasks/{task_id}` — 取消任务
  - 后台 Worker 从队列取出任务，依次执行（支持并发数配置）
  - 参考：`TaskManager` in [task_manager.py](file:///Users/cret/Desktop/AppleMusic-Downloader/src/amdl/task_manager.py)
- [ ] **1.4 日志流推送**

  - WebSocket 增加 `{"type":"log", "message":"[INFO] 正在下载..."}` 消息
  - 将 `log_callback` 也接入 WebSocket 广播

### Phase 2 — 增强

- [ ] **1.5 下载历史持久化**

  - 使用 SQLite 记录已下载的 URL / 标题 / 时间
  - `GET /api/history` — 查询历史
  - `DELETE /api/history` — 清空历史
- [ ] **1.6 配置持久化**

  - `GET /api/config` — 获取当前配置
  - `PUT /api/config` — 保存配置（默认下载路径、编解码器偏好等）
  - 配置文件存 `~/.amdl/config.json`
- [ ] **1.7 批量 URL 导入**

  - 支持上传 `.txt` 文件，每行一个 URL
  - `POST /api/tasks/import` — 上传文件并批量创建任务

---

## 二、🟡 Flutter GUI

- [ ] **2.1 项目基础**

  - 搭建 Flutter 项目结构（已存在 `gui/`）
  - 配置 platform: web / windows / linux / macos
  - 添加依赖：`web_socket_channel`、`http`、`provider`（或 riverpod）
  - 配置后端 API 地址（开发环境可配）
- [ ] **2.2 下载页面**

  - URL 输入框（支持多行粘贴）
  - Cookie 文件选择器
  - 参数配置区（编解码器、格式、封面尺寸等）
  - **提交按钮** → `POST /api/tasks` → 跳转到任务详情
- [ ] **2.3 任务列表页**

  - 卡片列表展示所有任务（状态、进度、URL、创建时间）
  - 状态标签：🟡 pending / 🔵 running / 🟢 completed / 🔴 failed / ⚫ cancelled
  - 进度条 + 百分比显示
  - 每个任务可取消、可重新下载
  - 下拉刷新
- [ ] **2.4 实时进度**

  - 进入任务列表页时，连接所有 running 任务的 WebSocket
  - 收到 `progress` 消息 → 更新进度条（动画）
  - 收到 `status` 消息 → 更新状态标签
  - 收到 `log` 消息 → 可选的日志面板
- [ ] **2.5 设置页面**

  - 后端地址配置
  - 默认下载路径
  - 默认编解码器偏好
  - 默认封面尺寸
  - 主题切换（浅色/深色）
- [ ] **2.6 下载历史页**

  - 历史记录列表
  - 搜索/过滤
  - 清空历史
- [ ] **2.7 Cookie 管理**

  - 文件选择器（支持拖拽）
  - 上传到后端保存
  - 提示：如何从浏览器导出 Netscape 格式 cookies.txt

---

## 三、🟢 打包与部署

- [ ] **3.1 后端打包**

  - 使用 PyInstaller 打包 `server.py` 为单文件/单目录
  - 支持 `--host`、`--port`、`--workers` 参数
  - 输出到 `dist/amdl-server/`
- [ ] **3.2 Flutter 打包**

  - **Web**: `flutter build web` → 部署到任意静态服务器
  - **macOS**: `flutter build macos` → `.app` 或 DMG
  - **Windows**: `flutter build windows` → NSIS 或 MSIX
  - **Linux**: `flutter build linux` → AppImage 或 deb
- [ ] **3.3 一键启动脚本**

  - 启动后端 + 打开前端
  - macOS: `.command` 或 `launchd`
  - Windows: `.bat` 或 `.ps1`
  - Linux: `.sh`

---

## 四、🟢 代码质量

- [ ] **4.1 后端测试**

  - `pytest` 测试所有 API 端点
  - Mock gamdl 下载（测试队列逻辑）
- [ ] **4.2 错误处理完善**

  - 后端全局异常捕获，统一返回 JSON
  - 前端统一的错误提示组件
- [ ] **4.3 类型注解**

  - 后端完整类型注解
  - Flutter 使用 freezed 或 json_serializable

---

## 完成进度

| 类别 | 总数 | 已完成 |
|:---|:---:|:---:|
| 🟡 后端 API — Phase 1 | 4 | 1 |
| 🟡 后端 API — Phase 2 | 3 | 0 |
| 🟡 Flutter GUI | 7 | 0 |
| 🟢 打包部署 | 3 | 0 |
| 🟢 代码质量 | 3 | 0 |
| **总计** | **20** | **1** |

> 最后更新: 2026-07-05