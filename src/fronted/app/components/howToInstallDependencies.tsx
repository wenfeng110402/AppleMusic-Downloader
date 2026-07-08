"use client";

import { useI18n } from "../i18n";

export default function HowToInstallDependencies({ onBack }: { onBack: () => void }) {
  const { t } = useI18n();

  const deps = [
    {
      name: t("install.ffmpeg"),
      desc: t("install.ffmpeg.desc"),
      platforms: [
        {
          os: t("install.ffmpeg.win"),
          steps: [
            t("install.ffmpeg.win.step1"),
            t("install.ffmpeg.win.step2"),
            t("install.ffmpeg.win.step3"),
            t("install.ffmpeg.win.step4"),
          ],
        },
        {
          os: t("install.ffmpeg.mac"),
          steps: [
            t("install.ffmpeg.mac.step1"),
            t("install.ffmpeg.mac.step2"),
            t("install.ffmpeg.mac.step3"),
          ],
        },
        {
          os: t("install.ffmpeg.linux"),
          steps: [
            t("install.ffmpeg.linux.step1"),
            t("install.ffmpeg.linux.step2"),
          ],
        },
      ],
    },
    {
      name: t("install.mp4box"),
      desc: t("install.mp4box.desc"),
      platforms: [
        {
          os: t("install.ffmpeg.win"),
          steps: [
            t("install.mp4box.win.step1"),
            t("install.mp4box.win.step2"),
          ],
        },
        {
          os: t("install.ffmpeg.mac"),
          steps: [
            t("install.mp4box.mac.step1"),
            t("install.mp4box.mac.step2"),
          ],
        },
        {
          os: t("install.ffmpeg.linux"),
          steps: [
            t("install.mp4box.linux.step1"),
            t("install.mp4box.linux.step2"),
          ],
        },
      ],
    },
    {
      name: t("install.nm3u8dlre"),
      desc: t("install.nm3u8dlre.desc"),
      platforms: [
        {
          os: t("install.ffmpeg.win"),
          steps: [
            t("install.nm3u8dlre.win.step1"),
            t("install.nm3u8dlre.win.step2"),
          ],
        },
        {
          os: t("install.nm3u8dlre.mac"),
          steps: [
            t("install.nm3u8dlre.mac.step1"),
            t("install.nm3u8dlre.mac.step2"),
            t("install.nm3u8dlre.mac.step3"),
          ],
        },
        {
          os: t("install.nm3u8dlre.linux"),
          steps: [
            t("install.nm3u8dlre.linux.step1"),
            t("install.nm3u8dlre.linux.step2"),
            t("install.nm3u8dlre.linux.step3"),
          ],
        },
      ],
    },
  ];

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto">
      {/* ── Header ── */}
      <div className="flex shrink-0 items-center gap-4 border-b px-6 py-4" style={{ borderColor: "var(--card-border)" }}>
        <button
          onClick={onBack}
          className="flex h-8 w-8 items-center justify-center rounded-md transition-colors hover:bg-white/5"
          style={{ color: "var(--text-dim)" }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
        <h2 className="text-[15px] font-medium" style={{ color: "var(--text-heading)" }}>
          {t("install.title")}
        </h2>
      </div>

      {/* ── Content ── */}
      <div className="mx-auto w-full max-w-[640px] px-8 py-6 space-y-8">
        {deps.map((dep) => (
          <div key={dep.name}>
            <h3 className="mb-1 text-[14px] font-semibold" style={{ color: "var(--text-heading)" }}>
              {dep.name}
            </h3>
            <p className="mb-3 text-[12px]" style={{ color: "var(--text-dim)" }}>
              {dep.desc}
            </p>
            <div className="grid grid-cols-3 gap-4">
              {dep.platforms.map((p) => (
                <div
                  key={p.os}
                  className="rounded-lg p-4"
                  style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)" }}
                >
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-[0.04em]" style={{ color: "var(--text-dim)" }}>
                    {p.os}
                  </div>
                  <ol className="space-y-1.5" style={{ color: "var(--text-body)" }}>
                    {p.steps.map((step, i) => (
                      <li key={i} className="flex gap-2 text-[11.5px] leading-relaxed">
                        <span className="shrink-0 font-medium" style={{ color: "var(--text-muted)" }}>
                          {i + 1}.
                        </span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              ))}
            </div>
          </div>
        ))}

        {/* ── Verify hint ── */}
        <div
          className="rounded-lg p-4 text-[12px]"
          style={{ background: "var(--card-bg)", border: "1px solid var(--card-border)", color: "var(--text-dim)" }}
        >
          {t("install.verify")}
        </div>
      </div>
    </div>
  );
}