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
    fetch("/api/settings")
      .then((r) => r.json())
      .then((data) => {
        setForm(() => ({
          ...DEFAULT_FORM,
          ...(data && Object.keys(data).length > 0 ? data : {}),
          urls: "",
        }));
      })
      .catch(() => {});
  }, []);

  const set = (key: keyof FormState, value: string) => {
    setForm((prev) => {
      const next = { ...prev, [key]: value };
      const { urls, ...rest } = next;
      void urls;
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
    let settings: Partial<FormState> = {};
    try {
      const raw = localStorage.getItem("amdl_settings");
      if (raw) settings = JSON.parse(raw);
    } catch { /* ignore */ }
    const merged: FormState = { ...DEFAULT_FORM, ...settings };
    merged.urls = form.urls;
    merged.cookies_path = form.cookies_path.trim();
    merged.output_path = form.output_path;
    merged.audio_format = form.audio_format;
    await submitTask(merged);
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
        <div className="mb-10 text-center">
          <div
            className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full ring-1"
            style={{ background: "var(--card-bg)", borderColor: "var(--card-border)" }}
            onMouseEnter={() => setHover(true)}
            onMouseLeave={() => setHover(false)}
          >
            <svg
              width="20" height="20" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"
              className={`transition-all duration-300 ${hover ? "text-[#ef4444] scale-110" : ""}`}
              style={{ color: hover ? undefined : "var(--text-dim)" }}
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
          </div>
          <h2 className="text-[15px] font-medium" style={{ color: "var(--text-heading)" }}>{t("download.title")}</h2>
          <p className="mt-1 text-[11px]" style={{ color: "var(--text-muted)" }}>
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
          className="btn-primary w-full py-[11px] text-[13px] tracking-wide"
          onClick={handleSubmit}
        >
          {t("download.submit")}
        </button>

        <p className="mt-3 text-center text-[10.5px] text-foreground/15">
          {t("download.settings.hint")}
        </p>
      </div>
    </div>
  );
}