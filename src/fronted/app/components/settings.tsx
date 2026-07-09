"use client";

import { useState, useEffect, useCallback } from "react";
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

export default function Settings({ onNavigate }: { onNavigate?: (id: string) => void }) {
  const { t } = useI18n();
  const [form, setForm] = useState<FormState>(loadSettings);
  const [loaded, setLoaded] = useState(false);
  const [deps, setDeps] = useState<DependencyCheckItem[]>([]);
  const [checking, setChecking] = useState<string | null>(null);

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

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <div className="mx-auto w-full max-w-[520px] px-8 py-8">

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
        <details className="group mb-6">
          <summary className="mb-1.5 cursor-pointer text-[10.5px] font-semibold tracking-[0.05em] uppercase transition-colors" style={{ color: "var(--text-dim)" }}>
            {t("settings.advanced")}
          </summary>
          <div className="card">
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
        <div className="flex flex-col gap-2">
          <button className="btn-secondary w-full" onClick={() => onNavigate?.("how-to-install")}>
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
  const statusIcon = props.dep
    ? props.dep.found ? "✓" : "✗"
    : null;
  const statusColor = props.dep
    ? props.dep.found ? "#22c55e" : "#ef4444"
    : undefined;
  const showCheck = props.dep !== null; // null = cookies/output, undefined = deps还没检测过

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
          <span style={{ color: statusColor, fontSize: 15, fontWeight: 600, width: 20, textAlign: "center" }}>
            {statusIcon}
          </span>
        ) : null}
        {showCheck ? (
          <button
            className="btn-secondary text-[10.5px] whitespace-nowrap px-2.5 py-1"
            disabled={props.checking}
            onClick={props.onCheck}
          >
            {props.checking ? "…" : "检查"}
          </button>
        ) : null}
      </div>
      {props.dep && (
        <div className="mt-1 text-[10px] ml-[52px]" style={{ color: statusColor }}>
          {props.dep.found
            ? (props.dep.version || props.dep.path || props.dep.name)
            : `未找到: ${props.dep.name}`}
        </div>
      )}
    </div>
  );
}