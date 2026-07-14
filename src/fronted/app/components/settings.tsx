"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { DEFAULT_FORM } from "../service";
import { useI18n } from "../i18n";
import type { FormState, DependencyCheckItem, DependencyCheckResponse } from "../service";

function loadSettings(): FormState {
  if (typeof window === "undefined") return DEFAULT_FORM;
  return DEFAULT_FORM;
}

function saveSettings(form: FormState) {
  const { urls, ...rest } = form;
  void urls;
  fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(rest),
  }).catch(() => {});
}

interface DepDownloadStatus {
  status: string;   // "downloading" | "extracting" | "ok" | "error" | "skipped"
  progress: number;  // 0-100
  error?: string;
}

export default function Settings({ onNavigate }: { onNavigate?: (id: string) => void }) {
  const { t } = useI18n();
  const [form, setForm] = useState<FormState>(loadSettings);
  const [loaded, setLoaded] = useState(false);
  const [deps, setDeps] = useState<DependencyCheckItem[]>([]);
  const [checking, setChecking] = useState<string | null>(null);
  const [downloadProgress, setDownloadProgress] = useState<Record<string, DepDownloadStatus>>({});
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ── auto-check deps & poll download progress ──────────
  useEffect(() => {
    // Initial check
    fetch("/api/dependencies")
      .then((r) => r.json())
      .then((data: DependencyCheckResponse) => setDeps(data.dependencies))
      .catch(() => {});

    // Poll download progress while deps are being downloaded
    const poll = () => {
      fetch("/api/dependencies/download-progress")
        .then((r) => r.json())
        .then((data: { dependencies: Record<string, DepDownloadStatus> }) => {
          setDownloadProgress(data.dependencies);
          const allDone = Object.values(data.dependencies).every(
            (d) => d.status === "ok" || d.status === "error" || d.status === "skipped"
          );
          // Recheck deps when downloads finish
          if (allDone && Object.keys(data.dependencies).length > 0) {
            fetch("/api/dependencies")
              .then((r) => r.json())
              .then((d: DependencyCheckResponse) => setDeps(d.dependencies))
              .catch(() => {});
          }
        })
        .catch(() => {});
    };
    poll();
    pollingRef.current = setInterval(poll, 3000);
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, []);

  useEffect(() => {
    if (loaded) {
      saveSettings(form);
    }
  }, [form, loaded]);

  useEffect(() => {
    fetch("/api/settings")
      .then((r) => r.json())
      .then((data) => {
        if (data && Object.keys(data).length > 0) {
          setForm(() => ({ ...DEFAULT_FORM, ...data, urls: "" }));
        }
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, []);

  const checkDep = useCallback(async (name: string, path: string) => {
    setChecking(name);
    try {
      const params = new URLSearchParams();
      if (name === "ffmpeg" && path) params.set("ffmpeg_path", path);
      if (name === "MP4Box" && path) params.set("mp4box_path", path);
      if (name === "N_m3u8DL-RE" && path) params.set("nm3u8dlre_path", path);
      const res = await fetch(`/api/dependencies?${params.toString()}`);
      const data = (await res.json()) as DependencyCheckResponse;
      setDeps(data.dependencies);
    } catch {
      setDeps([]);
    }
    setChecking(null);
  }, []);

  const getDep = (name: string): DependencyCheckItem | undefined =>
    deps.find((d) => d.name === name);

  const set = (key: keyof FormState, value: string | boolean | number) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  // ── download progress states ──────────────────────────
  const activeDownloads = Object.entries(downloadProgress).filter(
    ([, v]) => v.status === "downloading" || v.status === "extracting" || v.status === "winget"
  );
  const failedDownloads = Object.entries(downloadProgress).filter(
    ([, v]) => v.status === "error"
  );

  const statusLabel = (st: DepDownloadStatus) => {
    if (st.status === "winget") return t("install.winget");
    if (st.status === "downloading") return t("install.downloading");
    if (st.status === "extracting") return t("install.extracting");
    return st.status;
  };

  return (
    <div className="flex flex-1 flex-col overflow-y-auto scroll-edge-top">
      <div className="mx-auto w-full max-w-[520px] px-8 py-8">

        {/* ══════ Auto-download progress banner ══════ */}
        {activeDownloads.length > 0 && (
          <section className="mb-6 animate-fade-in-up">
            <div className="card px-4 py-3.5">
              <div className="mb-2.5 text-[12.5px] font-semibold" style={{ color: "var(--text-body)" }}>
                {t("settings.dep_downloading")}
              </div>
              {activeDownloads.map(([name, st]) => (
                <div key={name} className="mb-2.5 last:mb-0">
                  <div className="flex items-center justify-between text-[11px] mb-1.5" style={{ color: "var(--text-dim)" }}>
                    <span className="font-medium">{name}</span>
                    <span className="tabular-nums">
                      {st.status === "winget" ? t("settings.dep_installing") : `${Math.round(st.progress)}%`}
                    </span>
                  </div>
                  <div className="h-1.5 w-full rounded-full overflow-hidden" style={{ background: "var(--card-border)" }}>
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: st.status === "winget" ? "50%" : `${st.progress}%`,
                        background: st.status === "winget" ? "#6366f1" : "#ef4444",
                        transition: "width 0.6s var(--ease-spring)",
                      }}
                    />
                  </div>
                  <div className="mt-0.5 text-[9.5px]" style={{ color: "var(--text-muted)" }}>
                    {statusLabel(st)}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ══════ Failed downloads notice ══════ */}
        {failedDownloads.length > 0 && activeDownloads.length === 0 && (
          <section className="mb-6 animate-fade-in-up">
            <div className="card px-4 py-3.5" style={{ borderColor: "rgba(239,68,68,0.2)" }}>
              <div className="mb-1 text-[12.5px] font-semibold" style={{ color: "#ef4444" }}>
                {t("settings.dep_failed_title")}
              </div>
              {failedDownloads.map(([name, st]) => (
                <div key={name} className="text-[11px]" style={{ color: "var(--text-dim)" }}>
                  {name}: {st.error || t("settings.dep_failed_unknown")}
                </div>
              ))}
              <div className="mt-2 text-[10.5px]" style={{ color: "var(--text-muted)" }}>
                {t("settings.dep_failed_hint")}
              </div>
            </div>
          </section>
        )}

        {/* ══════ Codec & Format ══════ */}
        <Section title="Codec & Format">
          <Row label={t("settings.codec")}>
            <select className="input" value={form.codec_song} onChange={(e) => set("codec_song", e.target.value)}>
              <option value="aac-web">AAC (web)</option>
              <option value="atmos">Atmos</option>
            </select>
          </Row>
          <Row label={t("settings.mode")}>
            <select className="input" value={form.download_mode} onChange={(e) => set("download_mode", e.target.value)}>
              <option value="ytdlp">ytdlp</option>
              <option value="nm3u8dlre">N_m3u8DL-RE</option>
            </select>
          </Row>
          <Row label={t("settings.cover")}>
            <select className="input" value={form.cover_format} onChange={(e) => set("cover_format", e.target.value)}>
              <option value="jpg">JPG</option>
              <option value="png">PNG</option>
              <option value="raw">Raw</option>
            </select>
          </Row>
          <Row label={t("settings.cover_size")}>
            <input className="input" type="number" min={50} max={5000} value={form.cover_size} onChange={(e) => set("cover_size", Number(e.target.value))} />
          </Row>
          <Row label={t("settings.language")}>
            <select className="input" value={form.language} onChange={(e) => set("language", e.target.value)}>
              <option value="en-US">English</option>
              <option value="zh-CN">中文</option>
              <option value="ja-JP">日本語</option>
              <option value="ko-KR">한국어</option>
            </select>
          </Row>
        </Section>

        {/* ══════ Toggles ══════ */}
        <Section title="">
          <div className="card">
            <ToggleRow label={t("settings.overwrite")} checked={form.overwrite} onChange={(v) => set("overwrite", v)} />
            <ToggleRow label={t("settings.save_cover")} checked={form.save_cover} onChange={(v) => set("save_cover", v)} />
            <ToggleRow label={t("settings.save_playlist")} checked={form.save_playlist} onChange={(v) => set("save_playlist", v)} />
            <ToggleRow label={t("settings.no_synced_lyrics")} checked={form.no_synced_lyrics} onChange={(v) => set("no_synced_lyrics", v)} />
          </div>
        </Section>

        {/* ══════ Advanced ══════ */}
        <details className="group mb-8">
          <summary
            className="mb-2 cursor-pointer text-[10.5px] font-semibold tracking-[0.05em] uppercase select-none"
            style={{
              color: "var(--text-dim)",
              transition: "color 0.2s var(--ease-spring)",
            }}
          >
            <span className="group-open:text-[var(--text-body)]">
              {t("settings.advanced")}
            </span>
          </summary>
          <div
            className="card animate-fade-in-up"
            style={{ animationDuration: "0.3s" }}
          >
            <DepRow
              label={t("settings.ffmpeg_path")}
              value={form.ffmpeg_path}
              onChange={(v) => set("ffmpeg_path", v)}
              dep={getDep("ffmpeg")}
              checking={checking === "ffmpeg"}
              onCheck={() => checkDep("ffmpeg", form.ffmpeg_path)}
            />
            <DepRow
              label={t("settings.mp4box_path")}
              value={form.mp4box_path}
              onChange={(v) => set("mp4box_path", v)}
              dep={getDep("MP4Box")}
              checking={checking === "MP4Box"}
              onCheck={() => checkDep("MP4Box", form.mp4box_path)}
            />
            <DepRow
              label={t("settings.nm3u8dlre_path")}
              value={form.nm3u8dlre_path}
              onChange={(v) => set("nm3u8dlre_path", v)}
              dep={getDep("N_m3u8DL-RE")}
              checking={checking === "N_m3u8DL-RE"}
              onCheck={() => checkDep("N_m3u8DL-RE", form.nm3u8dlre_path)}
            />
            <DepRow
              label={t("settings.cookies_path")}
              value={form.cookies_path}
              onChange={(v) => set("cookies_path", v)}
              dep={null}
              checking={false}
              onCheck={() => {}}
            />
            <DepRow
              label={t("settings.output_path")}
              value={form.output_path}
              onChange={(v) => set("output_path", v)}
              dep={null}
              checking={false}
              onCheck={() => {}}
            />
          </div>
        </details>

        {/* ══════ Actions ══════ */}
        <div className="flex flex-col gap-2.5 mt-6">
          <button
            className="btn-secondary w-full py-[9px] text-[12px] font-medium"
            style={{ borderRadius: 9 }}
            onClick={() => onNavigate?.("how-to-install")}
          >
            {t("settings.how_to_install")}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ── 子组件 ────────────────────────────────────────────── */

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-6">
      {title && (
        <div className="mb-1.5 text-[10.5px] font-semibold tracking-[0.05em] uppercase" style={{ color: "var(--text-dim)" }}>
          {title}
        </div>
      )}
      <div className="card">{children}</div>
    </section>
  );
}

function Row(props: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2.5">
      <span className="text-[12.5px] font-medium" style={{ color: "var(--text-body)" }}>{props.label}</span>
      <div className="w-[180px] shrink-0">{props.children}</div>
    </div>
  );
}

function ToggleRow(props: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2.5">
      <span className="text-[12.5px] font-medium" style={{ color: "var(--text-body)" }}>{props.label}</span>
      <button
        role="switch"
        aria-checked={props.checked}
        onClick={() => props.onChange(!props.checked)}
        className="relative h-[22px] w-[40px] shrink-0 rounded-full border-0 outline-none transition-colors duration-150 cursor-pointer"
        style={{
          background: props.checked ? "#ef4444" : "var(--card-border)",
        }}
      >
        <span
          className="absolute top-[3px] h-[16px] w-[16px] rounded-full bg-white transition-all duration-150 shadow-sm"
          style={{ left: props.checked ? "21px" : "3px" }}
        />
      </button>
    </div>
  );
}

function DepRow(props: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  dep: DependencyCheckItem | null | undefined;
  checking: boolean;
  onCheck: () => void;
}) {
  const { t } = useI18n();
  const statusIcon = props.dep
    ? props.dep.found ? "✓" : "✗"
    : null;
  const statusColor = props.dep
    ? props.dep.found ? "#22c55e" : "#ef4444"
    : undefined;
  const showCheck = props.dep !== null;

  return (
    <div className="px-4 py-2.5">
      <div className="flex items-center gap-2">
        <span className="text-[12.5px] font-medium shrink-0" style={{ color: "var(--text-body)", minWidth: 48 }}>{props.label}</span>
        <input
          type="text"
          className="input flex-1 min-w-0"
          value={props.value}
          onChange={(e) => props.onChange(e.target.value)}
          placeholder={props.label}
        />
        {props.dep ? (
          <span
            style={{
              color: statusColor,
              fontSize: 15,
              fontWeight: 600,
              width: 20,
              textAlign: "center",
              transition: "transform 0.3s var(--ease-spring-bounce)",
              display: props.checking ? "none" : "inline",
            }}
          >
            {statusIcon}
          </span>
        ) : null}
        {showCheck ? (
          <button
            className="btn-secondary text-[10.5px] whitespace-nowrap px-2.5 py-1"
            style={{ borderRadius: 6 }}
            disabled={props.checking}
            onClick={props.onCheck}
          >
            {props.checking ? "…" : t("settings.check")}
          </button>
        ) : null}
      </div>
      {props.dep && (
        <div className="mt-1 text-[10px] ml-[52px]" style={{ color: statusColor }}>
          {props.dep.found
            ? (props.dep.version || props.dep.path || props.dep.name)
            : t("settings.not_found", { name: props.dep.name })}
        </div>
      )}
    </div>
  );
}