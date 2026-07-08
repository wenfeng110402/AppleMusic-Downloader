"use client";

import { createContext, useContext, useState, useCallback, type ReactNode } from "react";

// ── 翻译键 ──────────────────────────────────────────────────

const zh: Record<string, string> = {
  "nav.download": "下载",
  "nav.queue": "队列",
  "nav.settings": "设置",
  "nav.language": "语言",
  "nav.theme": "主题",
  "nav.theme.dark": "深色",
  "nav.theme.light": "浅色",
  "download.title": "Apple Music 下载器",
  "download.url": "Apple Music 链接",
  "download.url.placeholder": "每行一个链接...",
  "download.cookies": "Cookies 文件",
  "download.cookies.browse": "浏览",
  "download.output": "输出目录",
  "download.output.browse": "浏览",
  "download.submit": "下载",
  "download.urls_empty": "请输入至少一个下载链接",
  "download.cookies_empty": "请先设置 Cookies 文件路径",
  "download.settings.hint": "编解码、封面等选项可在 设置 中调整",
  "download.audio_format": "音频转换格式",
  "download.empty": "请输入至少一个链接",
  "download.no_cookies": "请选择 cookies.txt 文件",
  "download.failed": "提交失败",
  "download.failed.backend": "提交失败，请检查后端是否运行",
  "queue.title": "下载队列",
  "queue.empty": "暂无任务",
  "queue.auto": "自动刷新",
  "queue.cancel": "取消",
  "queue.no_logs": "暂无日志输出",
  "queue.count": "{count} 个任务",
  "settings.title": "设置",
  "settings.codec": "音频编码",
  "settings.cover": "封面格式",
  "settings.cover_size": "封面尺寸",
  "settings.mode": "下载模式",
  "settings.language": "语言",
  "settings.overwrite": "覆盖已存在文件",
  "settings.save_cover": "保存封面",
  "settings.save_playlist": "保存播放列表",
  "settings.no_synced_lyrics": "跳过同步歌词",
  "settings.advanced": "高级设置",
  "settings.temp_path": "临时目录",
  "settings.ffmpeg_path": "FFmpeg 路径",
  "settings.mp4box_path": "MP4Box 路径",
  "settings.nm3u8dlre_path": "N_m3u8DL-RE 路径",
  "settings.audio_format": "音频转换格式",
  "settings.how_to_install": "如何安装依赖",
  "status.pending": "等待中",
  "status.running": "运行中",
  "status.completed": "已完成",
  "status.failed": "失败",
  "status.cancelled": "已取消",
  "install.title": "依赖安装指南",
  "install.ffmpeg": "FFmpeg",
  "install.ffmpeg.desc": "用于音频编解码转换，是核心依赖之一。",
  "install.ffmpeg.win": "Windows",
  "install.ffmpeg.win.step1": "下载 ffmpeg-release-full.7z",
  "install.ffmpeg.win.step2": "解压到 C:\\ffmpeg",
  "install.ffmpeg.win.step3": "将 C:\\ffmpeg\\bin 添加到系统 PATH 环境变量",
  "install.ffmpeg.win.step4": "打开终端输入 ffmpeg -version 验证",
  "install.ffmpeg.mac": "macOS",
  "install.ffmpeg.mac.step1": "安装 Homebrew（如已安装可跳过）",
  "install.ffmpeg.mac.step2": "终端运行：brew install ffmpeg",
  "install.ffmpeg.mac.step3": "运行 ffmpeg -version 验证安装",
  "install.ffmpeg.linux": "Linux",
  "install.ffmpeg.linux.step1": "终端运行：sudo apt install ffmpeg",
  "install.ffmpeg.linux.step2": "运行 ffmpeg -version 验证安装",
  "install.mp4box": "MP4Box",
  "install.mp4box.desc": "用于 MP4 容器封装处理。",
  "install.mp4box.win.step1": "下载 GPAC 安装包",
  "install.mp4box.win.step2": "安装后将 MP4Box 所在目录添加到 PATH",
  "install.mp4box.mac.step1": "终端运行：brew install gpac",
  "install.mp4box.mac.step2": "运行 MP4Box -version 验证安装",
  "install.mp4box.linux.step1": "终端运行：sudo apt install gpac",
  "install.mp4box.linux.step2": "运行 MP4Box -version 验证安装",
  "install.nm3u8dlre": "N_m3u8DL-RE",
  "install.nm3u8dlre.desc": "用于下载 m3u8 流媒体，是核心下载引擎。",
  "install.nm3u8dlre.win.step1": "从 GitHub Releases 下载 N_m3u8DL-RE_win-x64.zip",
  "install.nm3u8dlre.win.step2": "解压到指定目录，将 N_m3u8DL-RE.exe 所在目录添加到 PATH",
  "install.nm3u8dlre.mac": "macOS (ARM)",
  "install.nm3u8dlre.mac.step1": "从 GitHub Releases 下载 N_m3u8DL-RE_osx-arm64.tar.gz",
  "install.nm3u8dlre.mac.step2": "解压后移动到 /usr/local/bin 或添加到 PATH",
  "install.nm3u8dlre.mac.step3": "运行 N_m3u8DL-RE --version 验证",
  "install.nm3u8dlre.linux": "Linux",
  "install.nm3u8dlre.linux.step1": "从 GitHub Releases 下载 N_m3u8DL-RE_linux-x64.tar.gz",
  "install.nm3u8dlre.linux.step2": "解压后移动到 /usr/local/bin 或添加到 PATH",
  "install.nm3u8dlre.linux.step3": "运行 N_m3u8DL-RE --version 验证",
  "install.verify": "进入设置 → 高级设置 → 点击「Check」按钮验证依赖是否安装成功。",
  "install.back": "返回",
};

const en: Record<string, string> = {
  "nav.download": "Download",
  "nav.queue": "Queue",
  "nav.settings": "Settings",
  "nav.language": "Language",
  "nav.theme": "Theme",
  "nav.theme.dark": "Dark",
  "nav.theme.light": "Light",
  "download.title": "Apple Music Downloader",
  "download.url": "Apple Music URL",
  "download.url.placeholder": "One link per line...",
  "download.cookies": "Cookies File",
  "download.cookies.browse": "Browse",
  "download.output": "Output Folder",
  "download.output.browse": "Browse",
  "download.submit": "Download",
  "download.urls_empty": "Please enter at least one URL",
  "download.cookies_empty": "Please set the cookies file path first",
  "download.settings.hint": "Codec, cover, and other options in Settings",
  "download.audio_format": "Audio Output Format",
  "download.empty": "Please enter at least one URL",
  "download.no_cookies": "Please select a cookies.txt file",
  "download.failed": "Submit failed",
  "download.failed.backend": "Submit failed, check if backend is running",
  "queue.title": "Download Queue",
  "queue.empty": "No tasks yet",
  "queue.auto": "Auto-refresh",
  "queue.cancel": "Cancel",
  "queue.no_logs": "No log output yet",
  "queue.count": "{count} task(s)",
  "settings.title": "Settings",
  "settings.codec": "Audio Codec",
  "settings.cover": "Cover Format",
  "settings.cover_size": "Cover Size",
  "settings.mode": "Download Mode",
  "settings.language": "Language",
  "settings.overwrite": "Overwrite existing files",
  "settings.save_cover": "Save cover image",
  "settings.save_playlist": "Save playlist",
  "settings.no_synced_lyrics": "Skip synced lyrics",
  "settings.advanced": "Advanced",
  "settings.temp_path": "Temp Directory",
  "settings.ffmpeg_path": "FFmpeg Path",
  "settings.mp4box_path": "MP4Box Path",
  "settings.nm3u8dlre_path": "N_m3u8DL-RE Path",
  "settings.audio_format": "Audio Conversion Format",
  "settings.how_to_install": "How to install dependencies",
  "status.pending": "Pending",
  "status.running": "Running",
  "status.completed": "Completed",
  "status.failed": "Failed",
  "status.cancelled": "Cancelled",
  "install.title": "Dependency Installation Guide",
  "install.ffmpeg": "FFmpeg",
  "install.ffmpeg.desc": "Core dependency for audio codec transcoding.",
  "install.ffmpeg.win": "Windows",
  "install.ffmpeg.win.step1": "Download ffmpeg-release-full.7z",
  "install.ffmpeg.win.step2": "Extract to C:\\ffmpeg",
  "install.ffmpeg.win.step3": "Add C:\\ffmpeg\\bin to system PATH",
  "install.ffmpeg.win.step4": "Open terminal and run ffmpeg -version to verify",
  "install.ffmpeg.mac": "macOS",
  "install.ffmpeg.mac.step1": "Install Homebrew (skip if already installed)",
  "install.ffmpeg.mac.step2": "Terminal: brew install ffmpeg",
  "install.ffmpeg.mac.step3": "Run ffmpeg -version to verify",
  "install.ffmpeg.linux": "Linux",
  "install.ffmpeg.linux.step1": "Terminal: sudo apt install ffmpeg",
  "install.ffmpeg.linux.step2": "Run ffmpeg -version to verify",
  "install.mp4box": "MP4Box",
  "install.mp4box.desc": "For MP4 container muxing.",
  "install.mp4box.win.step1": "Download GPAC installer",
  "install.mp4box.win.step2": "Add MP4Box directory to PATH after installation",
  "install.mp4box.mac.step1": "Terminal: brew install gpac",
  "install.mp4box.mac.step2": "Run MP4Box -version to verify",
  "install.mp4box.linux.step1": "Terminal: sudo apt install gpac",
  "install.mp4box.linux.step2": "Run MP4Box -version to verify",
  "install.nm3u8dlre": "N_m3u8DL-RE",
  "install.nm3u8dlre.desc": "Core download engine for m3u8 streams.",
  "install.nm3u8dlre.win.step1": "Download N_m3u8DL-RE_win-x64.zip from GitHub Releases",
  "install.nm3u8dlre.win.step2": "Extract and add the directory to PATH",
  "install.nm3u8dlre.mac": "macOS (ARM)",
  "install.nm3u8dlre.mac.step1": "Download N_m3u8DL-RE_osx-arm64.tar.gz from GitHub Releases",
  "install.nm3u8dlre.mac.step2": "Extract, move to /usr/local/bin or add to PATH",
  "install.nm3u8dlre.mac.step3": "Run N_m3u8DL-RE --version to verify",
  "install.nm3u8dlre.linux": "Linux",
  "install.nm3u8dlre.linux.step1": "Download N_m3u8DL-RE_linux-x64.tar.gz from GitHub Releases",
  "install.nm3u8dlre.linux.step2": "Extract, move to /usr/local/bin or add to PATH",
  "install.nm3u8dlre.linux.step3": "Run N_m3u8DL-RE --version to verify",
  "install.verify": "Go to Settings → Advanced → click Check to verify dependencies are installed.",
  "install.back": "Back",
};

const locales: Record<string, Record<string, string>> = { zh, en };

// ── Context ──────────────────────────────────────────────────

interface I18nContextValue {
  locale: string;
  setLocale: (l: string) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue>({
  locale: "zh",
  setLocale: () => {},
  t: (key: string) => key,
});

export function useI18n() {
  return useContext(I18nContext);
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("amdl_locale") || "zh";
    }
    return "zh";
  });

  const changeLocale = useCallback((l: string) => {
    setLocale(l);
    localStorage.setItem("amdl_locale", l);
  }, []);

  const t = useCallback(
    (key: string, vars?: Record<string, string | number>) => {
      const dict = locales[locale] || locales.zh;
      let text = dict[key] || locales.zh[key] || key;
      if (vars) {
        for (const [k, v] of Object.entries(vars)) {
          text = text.replace(`{${k}}`, String(v));
        }
      }
      return text;
    },
    [locale],
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale: changeLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}