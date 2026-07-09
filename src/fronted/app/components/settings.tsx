"use client";

import { useState, useEffect, useCallback } from "react";
import { DEFAULT_FORM, useDependencyCheck } from "../service";
import { useI18n } from "../i18n";
import type { FormState, DependencyCheckItem } from "../service";

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
  const { deps, check } = useDependencyCheck();
  const [checking, setChecking] = useState(false);

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

  const handleCheckDeps = useCallback(async () => {
    setChecking(true);
    await check(form.ffmpeg_path, form.mp4box_path, form.nm3u8dlre_path);
    setChecking(false);
  }, [form.ffmpeg_path, form.mp4box_path, form.nm3u8dlre_path, check]);

  const getDep = (name: string): DependencyCheckItem | undefined =>
    deps.find((d) => d.name === name);

  const set = (key: keyof FormState, value: string | boolean | number) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <div className="mx-auto w-full max-w-[520px] px-8 py-8">

        {/* ══════ Codec & Format ══════ */}
        <section className="mb-6">
          <div className="mb-1.5 text-[10.5px] font-semibold tracking-[0.05em] uppercase" style={{ color: "var(--text-dim)" }}>
            Codec & Format
          </div>
          <div className="card">
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
          </div>
        </section>

        {/* ══════ Toggles ══════ */}
        <section className="mb-6">
          <div className="card">
            <ToggleRow label={t("settings.overwrite")} checked={form.overwrite} onChange={(v) => set("overwrite", v)} />
            <ToggleRow label={t("settings.save_cover")} checked={form.save_cover} onChange={(v) => set("save_cover", v)} />
            <ToggleRow label={t("settings.save_playlist")} checked={form.save_playlist} onChange={(v) => set("save_playlist", v)} />
            <ToggleRow label={t("settings.no_synced_lyrics")} checked={form.no_synced_lyrics} onChange={(v) => set("no_synced_lyrics", v)} />
          </div>
        </section>

        {/* ══════ Advanced ══════ */}
        <details className="group mb-6">
          <summary className="mb-1.5 cursor-pointer text-[10.5px] font-semibold tracking-[0.05em] uppercase transition-colors" style={{ color: "var(--text-dim)" }}>
            {t("settings.advanced")}
          </summary>
          <div className="card">
            <DependencyRow
              label={t("settings.ffmpeg_path")}
              value={form.ffmpeg_path}
              onChange={(v) => set("ffmpeg_path", v)}
              dep={getDep("ffmpeg")}
            />
            <DependencyRow
              label={t("settings.mp4box_path")}
              value={form.mp4box_path}
              onChange={(v) => set("mp4box_path", v)}
              dep={getDep("mp4box")}
            />
            <DependencyRow
              label={t("settings.nm3u8dlre_path")}
              value={form.nm3u8dlre_path}
              onChange={(v) => set("nm3u8dlre_path", v)}
              dep={getDep("nm3u8dlre")}
            />
            <DependencyRow
              label={t("settings.cookies_path")}
              value={form.cookies_path}
              onChange={(v) => set("cookies_path", v)}
              dep={null}
            />
            <DependencyRow
              label={t("settings.output_path")}
              value={form.output_path}
              onChange={(v) => set("output_path", v)}
              dep={null}
            />
          </div>
        </details>

        {/* ══════ Actions ══════ */}
        <div className="flex flex-col gap-2">
          <button className="btn-secondary w-full" disabled={checking} onClick={handleCheckDeps}>
            {checking ? t("settings.checking") : t("settings.check_deps")}
          </button>
          <button className="btn-secondary w-full" onClick={() => onNavigate?.("how-to-install")}>
            {t("settings.how_to_install")}
          </button>
        </div>
      </div>
    </div>
  );
}

function Row(props: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 py-2">
      <span className="text-sm text-main">{props.label}</span>
      <div className="w-[180px]">{props.children}</div>
    </div>
  );
}

function ToggleRow(props: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-3 py-2">
      <span className="text-sm text-main">{props.label}</span>
      <input
        type="checkbox"
        checked={props.checked}
        onChange={(e) => props.onChange(e.target.checked)}
        className="toggle"
      />
    </div>
  );
}

function DependencyRow(props: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  dep: DependencyCheckItem | null | undefined;
}) {
  const status = props.dep;
  return (
    <Row label={props.label}>
      <div className="flex flex-col gap-1">
        <input
          type="text"
          className="input w-full"
          value={props.value}
          onChange={(e) => props.onChange(e.target.value)}
          placeholder={props.label}
        />
        {status && (
          <span
            className="text-[10px]"
            style={{
              color: status.found ? "var(--success)" : "var(--danger)",
            }}
          >
            {status.found ? (status.version || status.path || status.name) : `Not found: ${status.name}`}
          </span>
        )}
      </div>
    </Row>
  );
}