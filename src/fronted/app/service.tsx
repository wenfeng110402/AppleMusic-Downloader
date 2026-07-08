"use client";

import { useState, useCallback } from "react";

// ── 类型定义 ───────────────────────────────────────────────────

export interface FormState {
  urls: string;
  cookies_path: string;
  output_path: string;
  temp_path: string;
  ffmpeg_path: string;
  mp4box_path: string;
  nm3u8dlre_path: string;
  audio_format: string;
  codec_song: string;
  download_mode: string;
  cover_format: string;
  cover_size: number;
  language: string;
  overwrite: boolean;
  save_cover: boolean;
  save_playlist: boolean;
  no_synced_lyrics: boolean;
}

export interface TaskInfo {
  id: string;
  status: string;
  progress: Record<string, unknown>;
  error_count: number;
  message: string;
  logs: string[];
  created_at: string;
  updated_at: string;
  urls: string[];
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface DependencyCheckItem {
  name: string;
  found: boolean;
  path?: string;
  version?: string;
}

export interface DependencyCheckResponse {
  all_ok: boolean;
  dependencies: DependencyCheckItem[];
}

export interface TaskSubmitResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface TaskListResponse {
  tasks: TaskInfo[];
  total: number;
}

export interface ApiInfoResponse {
  api_version: string;
  supported_codecs_song: Array<{ id: string; name: string }>;
  supported_codecs_music_video: Array<{ id: string; name: string }>;
  supported_cover_formats: Array<{ id: string; name: string }>;
  supported_download_modes: Array<{ id: string; name: string }>;
  supported_audio_conversion_formats: string[];
  supported_video_conversion_formats: string[];
}

// ── 默认值 ────────────────────────────────────────────────────

export const DEFAULT_FORM: FormState = {
  urls: "",
  cookies_path: "",
  output_path: "./Apple Music",
  temp_path: "./temp",
  ffmpeg_path: "ffmpeg",
  mp4box_path: "MP4Box",
  nm3u8dlre_path: "N_m3u8DL-RE",
  audio_format: "",
  codec_song: "aac-web",
  download_mode: "ytdlp",
  cover_format: "jpg",
  cover_size: 1200,
  language: "en-US",
  overwrite: false,
  save_cover: false,
  save_playlist: false,
  no_synced_lyrics: false,
};

// ── 状态映射 ──────────────────────────────────────────────────

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

// ── 健康检查 ──────────────────────────────────────────────────

export function useBackendStatus() {
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [version, setVersion] = useState<string | null>(null);

  const check = useCallback(async () => {
    try {
      const res = await fetch("/api/health");
      const data = (await res.json()) as HealthResponse;
      setHealthy(true);
      setVersion(data.version);
    } catch {
      setHealthy(false);
    }
  }, []);

  return { healthy, version, check };
}

// ── 提交下载任务 ──────────────────────────────────────────────

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
      const res = await fetch("/api/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json();
        let msg = res.statusText;
        if (typeof err.detail === "string") {
          msg = err.detail;
        } else if (Array.isArray(err.detail)) {
          msg = err.detail.map((e: { msg?: string }) => e.msg || String(e)).join("; ");
        }
        alert(`submit failed: ${msg}`);
        return;
      }

      onSuccess?.();
    } catch {
      alert("submit failed, check if backend is running");
    }
  };
}

// ── 任务列表 ──────────────────────────────────────────────────

export function useTasks() {
  const [tasks, setTasks] = useState<TaskInfo[]>([]);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch("/api/tasks");
      const data = (await res.json()) as TaskListResponse;
      setTasks(data.tasks);
    } catch {
      /* backend not ready */
    }
  }, []);

  return { tasks, refresh };
}

// ── 取消任务 ──────────────────────────────────────────────────

export function useCancelTask(onDone?: () => void) {
  return async (taskId: string) => {
    try {
      await fetch(`/api/tasks/${taskId}`, { method: "DELETE" });
      onDone?.();
    } catch {
      /* ignore */
    }
  };
}

// ── 依赖检测 ──────────────────────────────────────────────────

export function useDependencyCheck() {
  const [deps, setDeps] = useState<DependencyCheckItem[]>([]);

  const check = useCallback(async (ffmpegPath: string, mp4boxPath: string, nm3u8dlrePath: string) => {
    try {
      const params = new URLSearchParams();
      if (ffmpegPath) params.set("ffmpeg_path", ffmpegPath);
      if (mp4boxPath) params.set("mp4box_path", mp4boxPath);
      if (nm3u8dlrePath) params.set("nm3u8dlre_path", nm3u8dlrePath);
      const res = await fetch(`/api/dependencies?${params.toString()}`);
      const data = (await res.json()) as DependencyCheckResponse;
      setDeps(data.dependencies);
    } catch {
      setDeps([]);
    }
  }, []);

  return { deps, check };
}