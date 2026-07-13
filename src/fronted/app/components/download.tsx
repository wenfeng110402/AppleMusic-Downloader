"use client";

import { useState, useEffect } from "react";
import TagInput from "./TagInput";
import { FormState, DEFAULT_FORM, useSubmitTask } from "../service";
import { useI18n } from "../i18n";

const AUDIO_FORMATS = [
  { value: "", label: "None" },
  { value: "mp3", label: "MP3" },
  { value: "flac", label: "FLAC" },
  { value: "wav", label: "WAV" },
  { value: "aac", label: "AAC" },
  { value: "m4a", label: "M4A" },
  { value: "ogg", label: "OGG" },
  { value: "alac", label: "ALAC" },
];

const AUDIO_FORMATS_ZH = [
  { value: "", label: "不转换" },
  { value: "mp3", label: "MP3" },
  { value: "flac", label: "FLAC" },
  { value: "wav", label: "WAV" },
  { value: "aac", label: "AAC" },
  { value: "m4a", label: "M4A" },
  { value: "ogg", label: "OGG" },
  { value: "alac", label: "ALAC" },
];

declare global {
  interface Window {
    pywebview?: { api: { open_file: () => Promise<string>; open_folder: () => Promise<string> } };
  }
}

export default function Download({ onNavigate }: { onNavigate?: (id: string) => void }) {
  const { t, locale } = useI18n();
  const submitTask = useSubmitTask();
  const [form, setForm] = useState<FormState>(DEFAULT_FORM);
  const [hover, setHover] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    // 恢复上次的 url 输入
    const savedUrls = sessionStorage.getItem("amdl_pending_urls") || "";

    fetch("/api/settings")
      .then((r) => r.json())
      .then((data) => {
        setForm(() => ({
          ...DEFAULT_FORM,
          ...(data && Object.keys(data).length > 0 ? data : {}),
          urls: savedUrls,
        }));
      })
      .catch(() => {});
  }, []);

  const set = (key: keyof FormState, value: string) => {
    setForm((prev) => {
      const next = { ...prev, [key]: value };
      const { urls, ...rest } = next;
      void urls;
      // 随时保存 urls 到 sessionStorage
      if (key === "urls") {
        sessionStorage.setItem("amdl_pending_urls", value);
      }
      fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(rest),
      }).catch(() => {});
      return next;
    });
  };

  const handleSubmit = async () => {
    if (!form.cookies_path || !form.cookies_path.trim()) {
      alert(t("download.cookies_empty"));
      return;
    }
    // 直接用当前 form 的全部状态提交，无需读 localStorage
    // form 已在 useEffect 中从 /api/settings 加载，set() 实时更新
    await submitTask(form);
    // 提交成功后清空暂存
    sessionStorage.removeItem("amdl_pending_urls");
    onNavigate?.("queue");
  };

  const browseFile = () => {
    if (window.pywebview?.api) {
      window.pywebview.api.open_file().then((path: string) => { if (path) set("cookies_path", path); });
    } else {
      const p = prompt("Cookies file path:");
      if (p) set("cookies_path", p);
    }
  };

  const browseFolder = () => {
    if (window.pywebview?.api) {
      window.pywebview.api.open_folder().then((path: string) => { if (path) set("output_path", path); });
    } else {
      const p = prompt("Output folder path:");
      if (p) set("output_path", p);
    }
  };

  return (
    <div className="flex flex-1 flex-col items-center justify-center overflow-y-auto">
      <div className="w-full max-w-[480px] px-8">

        {/* ── Language switcher ──
        <div className="mb-6 flex justify-center">
          <div className="flex rounded-md border p-0.5" style={{ borderColor: "var(--card-border)" }}>
            <button
              onClick={() => setLocale("zh")}
              className={[
                "rounded px-2.5 py-0.5 text-[10px] font-medium transition-all duration-150",
                locale === "zh"
                  ? "bg-[#ef4444] text-white"
                  : "text-foreground/35 hover:text-foreground/60",
              ].join(" ")}
            >
              中
            </button>
            <button
              onClick={() => setLocale("en")}
              className={[
                "rounded px-2.5 py-0.5 text-[10px] font-medium transition-all duration-150",
                locale === "en"
                  ? "bg-[#ef4444] text-white"
                  : "text-foreground/35 hover:text-foreground/60",
              ].join(" ")}
            >
              EN
            </button>
          </div>
        </div> */}

        {/* ── Hero ── */}
        <div className="mb-10 text-center animate-fade-in-up">
          <div
            className="mx-auto mb-5 flex h-13 w-13 items-center justify-center rounded-2xl"
            style={{
              background: "var(--card-bg)",
              border: "1px solid var(--card-border)",
              boxShadow: hover ? "0 4px 20px rgba(239, 68, 68, 0.08)" : "0 1px 3px rgba(0,0,0,0.04)",
              transition: "box-shadow 0.35s var(--ease-spring), transform 0.35s var(--ease-spring-bounce)",
              transform: hover ? "scale(1.03)" : "scale(1)",
            }}
            onMouseEnter={() => setHover(true)}
            onMouseLeave={() => setHover(false)}
          >
            <svg
              width="22" height="22" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
              style={{
                color: hover ? "#ef4444" : "var(--text-dim)",
                transition: "color 0.3s var(--ease-spring), transform 0.35s var(--ease-spring-bounce)",
                transform: hover ? "scale(1.08)" : "scale(1)",
              }}
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </div>
          <h2
            className="text-[16px] font-semibold tracking-[-0.01em]"
            style={{ color: "var(--text-heading)" }}
          >
            {t("download.title")}
          </h2>
          <p className="mt-1.5 text-[11px] leading-relaxed" style={{ color: "var(--text-muted)" }}>
            {t("download.url.placeholder")}
          </p>
        </div>

        {/* ── URL Input ── */}
        <TagInput
          value={form.urls}
          onChange={(v) => set("urls", v)}
          placeholder={t("download.url.placeholder")}
        />

        {/* ── Path rows ── */}
        <div className="mb-5 space-y-2">
          <div className="flex gap-2">
            <input
              className="input"
              placeholder={t("download.cookies")}
              value={form.cookies_path}
              onChange={(e) => set("cookies_path", e.target.value)}
            />
            <button className="btn-secondary shrink-0 text-[11px]" onClick={browseFile}>
              {t("download.cookies.browse")}
            </button>
          </div>
          <div className="flex gap-2">
            <input
              className="input"
              placeholder={t("download.output")}
              value={form.output_path}
              onChange={(e) => set("output_path", e.target.value)}
            />
            <button className="btn-secondary shrink-0 text-[11px]" onClick={browseFolder}>
              {t("download.output.browse")}
            </button>
          </div>
        </div>

        {/* ── Audio format ── */}
        <div className="mb-5">
          <label className="mb-1.5 block text-[10.5px] font-medium" style={{ color: "var(--text-dim)" }}>
            {t("download.audio_format")}
          </label>
          <select
            className="input"
            value={form.audio_format}
            onChange={(e) => set("audio_format", e.target.value)}
          >
            {(locale === "zh" ? AUDIO_FORMATS_ZH : AUDIO_FORMATS).map((fmt) => (
              <option key={fmt.value} value={fmt.value}>{fmt.label}</option>
            ))}
          </select>
        </div>

        {/* ── Submit ── */}
        <button
          className="btn-primary w-full py-[12px] text-[13px] font-semibold tracking-[0.01em]"
          style={{
            borderRadius: 10,
            letterSpacing: "0.01em",
          }}
          onClick={handleSubmit}
        >
          {t("download.submit")}
        </button>

        <p className="mt-3.5 text-center text-[10.5px]" style={{ color: "var(--text-muted)" }}>
          {t("download.settings.hint")}
        </p>
      </div>
    </div>
  );
}