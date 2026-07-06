# TODO — AppleMusic Downloader

> 架构：**FastAPI 后端**（`amdl/`）+ **Next.js 前端**（`gui/`）
> 后端基于 gamdl 封装，提供 REST API + WebSocket 实时推送。
> 前端使用 Next.js 开发，开发时独立运行，生产环境构建为静态文件后由 pywebview 内嵌加载。
> 支持平台：Windows / Linux / macOS

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
- [ ] **1.8 依赖检测与自动下载**

  - `GET /api/deps/status` — 检查 ffmpeg、N_m3u8DL-RE 等外部依赖是否可用
  - `POST /api/deps/install` — 自动下载缺失的依赖到 `tools/` 目录
  - 查找顺序：系统 PATH → 项目 `tools/` 目录 → 自动下载预编译二进制
  - 参考：[converter.py:resolve_ffmpeg_executable](file:///Users/cret/Desktop/AppleMusic-Downloader/src/amdl/converter.py#L24-L44)、[utils.py:prepend_tools_to_path](file:///Users/cret/Desktop/AppleMusic-Downloader/src/amdl/utils.py#L17-L99)
- [ ] **1.9 下载后清理**

  - `POST /api/cleanup` — 删除 `temp_path` 临时目录
  - 下载任务完成后自动调用，也可手动触发

---

## 二、🟡 Next.js 前端（`gui/`）

### Phase 1 — 项目基础

- [ ] **2.1 搭建 Next.js 项目**

  - 使用 `create-next-app` 初始化项目
  - 配置 TypeScript、Tailwind CSS
  - 目录结构：`pages/`（或 `app/`）、`components/`、`hooks/`、`types/`
  - 配置开发时后端 API 代理（解决跨域）
- [ ] **2.2 项目基础架构**

  - 封装 API 请求工具（`/api/*` 调用后端）
  - 封装 WebSocket 连接工具（自动重连、心跳）
  - 全局状态管理（可选择 Zustand / Context + useReducer）
  - 主题支持（浅色/深色模式）

### Phase 2 — 核心页面

- [ ] **2.3 下载页面**

  - URL 输入框（支持多行粘贴）
  - Cookie 文件选择器（或粘贴 cookie 文本）
  - 参数配置区（编解码器、格式、封面尺寸等）
  - **提交按钮** → `POST /api/tasks` → 跳转到任务详情
- [ ] **2.4 任务列表页**

  - 卡片列表展示所有任务（状态、进度、URL、创建时间）
  - 状态标签：🟡 pending / 🔵 running / 🟢 completed / 🔴 failed / ⚫ cancelled
  - 进度条 + 百分比显示
  - 每个任务可取消、可重新下载
  - 实时进度更新（WebSocket）
- [ ] **2.5 设置页面**

  - 后端地址配置
  - 默认下载路径
  - 默认编解码器偏好
  - 默认封面尺寸
  - Cookie 设置
  - 主题切换（浅色/深色）
- [ ] **2.6 下载历史页**

  - 历史记录列表
  - 搜索/过滤
  - 清空历史
- [ ] **2.7 依赖管理页**

  - 显示各依赖工具的检测状态（✅ / ❌）
  - 缺失时显示"一键下载"按钮
  - 显示已安装工具的版本号
- [ ] **2.8 关于页面**

  - 版本信息
  - 依赖工具版本展示
  - GitHub 链接

---

## 三、🟡 pywebview 桌面壳（`pywebview/`）

> Next.js 开发完成后，构建为静态文件，由 pywebview 加载。

- [ ] **3.1 搭建 pywebview 壳**

  - 使用 Python 编写 pywebview 启动脚本
  - 开发模式：加载 Next.js 开发服务器地址（`http://localhost:3000`）
  - 生产模式：加载 Next.js 构建后的静态文件（`file://` 或内嵌 HTTP 服务器）
- [ ] **3.2 pywebview 功能集成**

  - 窗口标题、图标、最小尺寸设置
  - 右键菜单屏蔽（可选）
  - 开发者工具开关（开发模式自动开启）
  - 文件对话框（打开/保存文件，通过 pywebview API 暴露给前端）
  - 窗口置顶、全屏等操作
- [ ] **3.3 前后端通信桥接**

  - 前端通过 `pywebview.api` 调用 Python 方法（如文件选择器、系统通知）
  - 后端事件推送（下载完成时弹出系统通知）

---

## 四、🟢 打包与部署

- [ ] **4.1 后端打包**

  - 使用 PyInstaller 打包 `server.py` 为单文件/单目录
  - 支持 `--host`、`--port`、`--workers` 参数
  - 输出到 `dist/amdl-server/`
- [ ] **4.2 前端构建**

  - `npm run build` → 输出静态文件到 `out/` 目录
  - 静态文件嵌入 pywebview 壳中
- [ ] **4.3 桌面应用打包**

  - 使用 PyInstaller 将 pywebview 壳 + 前端静态文件打包为单文件/单目录
  - **macOS**: 打包为 `.app` 或 DMG
  - **Windows**: 打包为 NSIS 安装包或便携版
  - **Linux**: 打包为 AppImage 或 deb
- [ ] **4.4 一键启动脚本**

  - 启动后端 + 桌面应用
  - macOS: `.command` 或 `launchd`
  - Windows: `.bat` 或 `.ps1`
  - Linux: `.sh`

---

## 五、🟢 代码质量

- [ ] **5.1 后端测试**

  - `pytest` 测试所有 API 端点
  - Mock gamdl 下载（测试队列逻辑）
- [ ] **5.2 前端代码质量**

  - ESLint + Prettier 代码规范
  - TypeScript 严格模式
- [ ] **5.3 错误处理完善**

  - 后端全局异常捕获，统一返回 JSON
  - 前端统一的错误提示组件
- [ ] **5.4 类型注解**

  - 后端完整类型注解
  - 前端 TypeScript 类型定义与后端 API 对齐

---

## 完成进度

| 类别 | 总数 | 已完成 |
|:---|:---:|:---:|
| 🟡 后端 API — Phase 1 | 4 | 1 |
| 🟡 后端 API — Phase 2 | 5 | 0 |
| 🟡 Next.js 前端 | 8 | 0 |
| 🟡 pywebview 桌面壳 | 3 | 0 |
| 🟢 打包部署 | 4 | 0 |
| 🟢 代码质量 | 4 | 0 |
| **总计** | **28** | **1** |

> 最后更新: 2026-07-05