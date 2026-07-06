"use client";

import { useEffect, useState, useCallback } from "react";

// ── API 基础配置 ────────────────────────────────────────────────

const API_BASE = "";

// ── 后端响应类型 ────────────────────────────────────────────────

interface HealthResponse {
    status: string;
    version: string;
}

interface TaskSubmitResponse {
    task_id: string;
    status: string;
    message: string;
}

interface TaskInfo {
    id: string;
    status: string;
    progress: Record<string, unknown>;
    error_count: number;
    message: string;
    created_at: string;
    updated_at: string;
    urls: string[];
}

interface TaskListResponse {
    tasks: TaskInfo[];
    total: number;
}

// ── 表单状态类型（对应后端 DownloadRequest 常用字段） ──────────

export interface FormState {
  urls: string;              // textarea 输入，提交时按换行拆成数组
  cookies_path: string;      // 必填：cookies.txt 绝对路径
  output_path: string;       // 下载输出目录
  temp_path: string;         // 临时文件目录
  ffmpeg_path: string;       // ffmpeg 路径
  nm3u8dlre_path: string;    // N_m3u8DL-RE 路径
  audio_format: string;      // 格式转换，空=不转换
  codec_song: string;        // 歌曲编码格式
  download_mode: string;     // 下载模式
  cover_format: string;      // 封面格式
  cover_size: number;        // 封面尺寸
  language: string;          // API 语言
  overwrite: boolean;        // 覆盖已有文件
  save_cover: boolean;       // 保存封面文件
  save_playlist: boolean;    // 保存播放列表文件
  no_synced_lyrics: boolean; // 不下载同步歌词
}

// 默认表单值
export const DEFAULT_FORM: FormState = {
    urls: "",
    cookies_path: "",
    output_path: "./Apple Music",
    temp_path: "./temp",
    ffmpeg_path: "ffmpeg",
    nm3u8dlre_path: "N_m3u8DL-RE",
    audio_format: "",
    codec_song: "AAC_WEB",
    download_mode: "YTDLP",
    cover_format: "JPG",
    cover_size: 1200,
    language: "en-US",
    overwrite: false,
    save_cover: false,
    save_playlist: false,
    no_synced_lyrics: false,
};

// ── Hooks ───────────────────────────────────────────────────────

/** 检查后端是否在线 */
export function useBackendStatus() {
    const [online, setOnline] = useState(false);

    useEffect(() => {
    fetch(`${API_BASE}/api/health`)
        .then((res) => res.json())
        .then((data: HealthResponse) => {
            if (data.status === "ok") setOnline(true);
        })
        .catch(() => setOnline(false));
    }, []);

    return online;
}

/** 任务列表管理 */
export function useTasks() {
    const [tasks, setTasks] = useState<TaskInfo[]>([]);

    useEffect(() => {
    fetch(`${API_BASE}/api/tasks`)
        .then((res) => res.json())
        .then((data: TaskListResponse) => setTasks(data.tasks))
        .catch(() => {});
    }, []);

    const refresh = useCallback(async () => {
    try {
        const res = await fetch(`${API_BASE}/api/tasks`);
        const data = (await res.json()) as TaskListResponse;
        setTasks(data.tasks);
    } catch {}
    }, []);

    return { tasks, refresh };
}

/** 提交下载任务 */
export function useSubmitTask(onSuccess?: () => void) {
    return async (form: FormState) => {
        const urlList = form.urls.split("\n").map((s) => s.trim()).filter(Boolean);
        if (urlList.length === 0) return;
        if (!form.cookies_path.trim()) {
        alert("cookies.txt path is required");
        return;
        }

    const body = {
        urls: urlList,
        cookies_path: form.cookies_path.trim(),
        output_path: form.output_path.trim(),
        temp_path: form.temp_path.trim(),
        ffmpeg_path: form.ffmpeg_path.trim(),
        nm3u8dlre_path: form.nm3u8dlre_path.trim(),
        codec_song: form.codec_song,
        download_mode: form.download_mode,
        cover_format: form.cover_format,
        cover_size: form.cover_size,
        language: form.language,
        overwrite: form.overwrite,
        save_cover: form.save_cover,
        save_playlist: form.save_playlist,
        no_synced_lyrics: form.no_synced_lyrics,
        audio_format: form.audio_format || null,
    };

    try {
        const res = await fetch(`${API_BASE}/api/tasks`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (!res.ok) {
            const err = await res.json();
            alert(`submit failed: ${err.detail || res.statusText}`);
            return;
        }

        onSuccess?.();
        } catch {
            alert("submit failed, check if backend is running");
        }
    };
}

/** 取消任务 */
export function useCancelTask(onDone?: () => void) {
    return async (taskId: string) => {
        try {
            await fetch(`${API_BASE}/api/tasks/${taskId}`, { method: "DELETE" });
            onDone?.();
        } catch {}
    };
}

// ── 状态辅助函数 ────────────────────────────────────────────────

const STATUS_LABELS: Record<string, string> = {
    pending: "pending",
    running: "running",
    completed: "completed",
    failed: "failed",
    cancelled: "cancelled",
};

const STATUS_COLORS: Record<string, string> = {
    completed: "bg-green-500/20 text-green-400",
    running: "bg-blue-500/20 text-blue-400",
    failed: "bg-red-500/20 text-red-400",
    cancelled: "bg-gray-500/20 text-gray-400",
    pending: "bg-yellow-500/20 text-yellow-400",
};

export function statusLabel(s: string): string {
    return STATUS_LABELS[s] || s;
}

export function statusColor(s: string): string {
    return STATUS_COLORS[s] || "bg-gray-500/20 text-gray-400";
}