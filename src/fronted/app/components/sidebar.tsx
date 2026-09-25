"use client";

import { useState, useEffect } from "react";
import { useI18n } from "../i18n";
import { useTheme } from "../theme";
import { useCheckUpdate, type UpdateInfo } from "../service";
import { useToast } from "./Toast";

const NAV_ITEMS = [
  {
    id: "download",
    key: "nav.download",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" y1="15" x2="12" y2="3" />
      </svg>
    ),
  },
  {
    id: "queue",
    key: "nav.queue",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <line x1="8" y1="6" x2="21" y2="6" />
        <line x1="8" y1="12" x2="21" y2="12" />
        <line x1="8" y1="18" x2="21" y2="18" />
        <line x1="3" y1="6" x2="3.01" y2="6" />
        <line x1="3" y1="12" x2="3.01" y2="12" />
        <line x1="3" y1="18" x2="3.01" y2="18" />
      </svg>
    ),
  },
  {
    id: "settings",
    key: "nav.settings",
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 114 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
      </svg>
    ),
  },
];

export default function Sidebar({ active, onNavigate }: { active: string; onNavigate: (id: string) => void }) {
  const { t, locale, setLocale } = useI18n();
  const { theme, setTheme } = useTheme();
  const { updateInfo, checking, check } = useCheckUpdate();
  const toast = useToast();
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    check();
  }, [check]);

  const handleVersionClick = async () => {
    if (updateInfo?.has_update) {
      setShowModal(true);
      return;
    }
    toast.info(t("update.checking"));
    const res = await check(true);
    if (res?.has_update) {
      setShowModal(true);
    } else {
      toast.success(t("update.up_to_date"));
    }
  };

  return (
    <>
      <nav
        className="flex h-screen w-[220px] shrink-0 flex-col relative z-10"
        style={{
          background: "var(--sidebar-bg)",
          backdropFilter: "blur(var(--sidebar-blur)) saturate(var(--sidebar-saturate))",
          WebkitBackdropFilter: "blur(var(--sidebar-blur)) saturate(var(--sidebar-saturate))",
          borderRight: "1px solid var(--sidebar-border)",
          transition: "background 0.4s var(--ease-spring), border-color 0.4s var(--ease-spring)",
        }}
      >
        {/* Drag region + Title */}
        <div className="shrink-0 px-5 pt-5 pb-4" style={{ WebkitAppRegion: "drag" } as React.CSSProperties}>
          <div
            className="text-[11px] font-semibold tracking-[0.06em] uppercase"
            style={{
              color: "var(--text-dim)",
              letterSpacing: "0.06em",
            }}
          >
            AMDL
          </div>
        </div>

        {/* Separator */}
        <div className="mx-4 h-px" style={{ background: "var(--divider)" }} />

        {/* Nav items */}
        <div className="flex-1 overflow-y-auto px-2 py-3">
          <ul className="flex flex-col gap-0.5">
            {NAV_ITEMS.map((item) => {
              const isSelected = active === item.id;
              return (
                <li key={item.id}>
                  <button
                    onClick={() => onNavigate(item.id)}
                    className={[
                      "group relative flex w-full items-center gap-2.5 rounded-[8px] px-3 py-2 text-[12.5px] font-medium",
                      "transition-all",
                      isSelected
                        ? "text-[var(--foreground)]"
                        : "text-[var(--text-muted)] hover:text-[var(--text-dim)]",
                    ].join(" ")}
                    style={{
                      transitionDuration: "0.25s",
                      transitionTimingFunction: "var(--ease-spring)",
                      background: isSelected ? "var(--sidebar-active)" : "transparent",
                    }}
                  >
                    {/* Left accent bar */}
                    <span
                      className={[
                        "absolute inset-y-1.5 left-0 w-[2.5px] rounded-full",
                        "transition-all",
                      ].join(" ")}
                      style={{
                        transitionDuration: "0.3s",
                        transitionTimingFunction: "var(--ease-spring-bounce)",
                        background: isSelected ? "#ef4444" : "transparent",
                        opacity: isSelected ? 1 : 0,
                        transform: isSelected ? "scaleY(1)" : "scaleY(0.5)",
                      }}
                    />
                    {/* Icon */}
                    <span
                      className={[
                        "transition-all",
                      ].join(" ")}
                      style={{
                        transitionDuration: "0.25s",
                        transitionTimingFunction: "var(--ease-spring)",
                        color: isSelected ? "#ef4444" : undefined,
                        transform: isSelected ? "scale(1.05)" : "scale(1)",
                      }}
                    >
                      {item.icon}
                    </span>
                    {/* Label */}
                    <span>{t(item.key)}</span>
                    {/* Selected dot */}
                    {isSelected && (
                      <span
                        className="ml-auto h-1.5 w-1.5 rounded-full bg-[#ef4444]"
                        style={{
                          animation: "fade-in-up 0.3s var(--ease-spring-bounce) both",
                        }}
                      />
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Bottom controls */}
        <div className="shrink-0" style={{ borderTop: "1px solid var(--divider)" }}>
          {/* Language switcher */}
          <div className="flex items-center gap-1 px-2 py-2">
            <span className="px-2 text-[10px]" style={{ color: "var(--text-muted)" }}>{t("nav.language")}</span>
            <div className="ml-auto flex rounded-[7px] p-0.5" style={{ border: "1px solid var(--card-border)", background: "var(--input-bg)" }}>
              <button
                onClick={() => setLocale("zh")}
                className={[
                  "rounded-[5px] px-2 py-0.5 text-[10px] font-medium",
                  "transition-all",
                  locale === "zh"
                    ? "bg-[#ef4444] text-white shadow-sm"
                    : "text-[var(--text-muted)] hover:text-[var(--text-body)]",
                ].join(" ")}
                style={{ transitionDuration: "0.2s", transitionTimingFunction: "var(--ease-spring)" }}
              >
                中
              </button>
              <button
                onClick={() => setLocale("en")}
                className={[
                  "rounded-[5px] px-2 py-0.5 text-[10px] font-medium",
                  "transition-all",
                  locale === "en"
                    ? "bg-[#ef4444] text-white shadow-sm"
                    : "text-[var(--text-muted)] hover:text-[var(--text-body)]",
                ].join(" ")}
                style={{ transitionDuration: "0.2s", transitionTimingFunction: "var(--ease-spring)" }}
              >
                EN
              </button>
            </div>
          </div>

          {/* Theme switcher */}
          <div className="flex items-center gap-1 px-2 py-2">
            <div className="ml-auto flex rounded-[7px] p-0.5" style={{ border: "1px solid var(--card-border)", background: "var(--input-bg)" }}>
              <button
                onClick={() => setTheme("dark")}
                className={[
                  "rounded-[5px] px-2 py-0.5 text-[10px] font-medium",
                  "transition-all",
                  theme === "dark"
                    ? "bg-[#ef4444] text-white shadow-sm"
                    : "text-[var(--text-muted)] hover:text-[var(--text-body)]",
                ].join(" ")}
                style={{ transitionDuration: "0.2s", transitionTimingFunction: "var(--ease-spring)" }}
              >
                {t("nav.theme.dark")}
              </button>
              <button
                onClick={() => setTheme("light")}
                className={[
                  "rounded-[5px] px-2 py-0.5 text-[10px] font-medium",
                  "transition-all",
                  theme === "light"
                    ? "bg-[#ef4444] text-white shadow-sm"
                    : "text-[var(--text-muted)] hover:text-[var(--text-body)]",
                ].join(" ")}
                style={{ transitionDuration: "0.2s", transitionTimingFunction: "var(--ease-spring)" }}
              >
                {t("nav.theme.light")}
              </button>
            </div>
          </div>

          {/* Version & Update Checker */}
          <div className="px-5 py-3">
            <button
              onClick={handleVersionClick}
              disabled={checking}
              className="flex items-center gap-2 group w-full text-left cursor-pointer transition-opacity hover:opacity-80"
              title={updateInfo?.has_update ? t("update.available") : t("update.up_to_date")}
            >
              <span
                className={[
                  "h-1.5 w-1.5 rounded-full shrink-0 transition-colors",
                  updateInfo?.has_update
                    ? "bg-amber-500 animate-pulse ring-2 ring-amber-500/20"
                    : "bg-emerald-500/70",
                ].join(" ")}
              />
              <span className="text-[10.5px] truncate" style={{ color: "var(--text-muted)" }}>
                {updateInfo?.has_update
                  ? `${updateInfo.current_version} → v${updateInfo.latest_version}`
                  : `v2.5.0`}
              </span>
              {updateInfo?.has_update && (
                <span className="ml-auto rounded bg-amber-500/15 px-1 py-0.5 text-[8.5px] font-semibold text-amber-500 uppercase tracking-wider">
                  New
                </span>
              )}
            </button>
          </div>
        </div>
      </nav>

      {/* Update Modal */}
      {showModal && updateInfo && (
        <UpdateModal
          updateInfo={updateInfo}
          onClose={() => setShowModal(false)}
        />
      )}
    </>
  );
}

function UpdateModal({
  updateInfo,
  onClose,
}: {
  updateInfo: UpdateInfo;
  onClose: () => void;
}) {
  const { t } = useI18n();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in-up"
      style={{
        background: "rgba(0, 0, 0, 0.55)",
        backdropFilter: "blur(8px)",
        WebkitBackdropFilter: "blur(8px)",
      }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-[420px] rounded-2xl p-6 shadow-2xl animate-spring-in"
        style={{
          background: "var(--card-bg)",
          border: "1px solid var(--card-border)",
          boxShadow: "0 20px 40px rgba(0, 0, 0, 0.45)",
          backdropFilter: "blur(20px)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-500/20 text-amber-500 text-xs font-bold">
              ↑
            </span>
            <h3 className="text-[14px] font-semibold" style={{ color: "var(--text-heading)" }}>
              {t("update.title")}
            </h3>
          </div>
          <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
            {t("update.available")}
          </span>
        </div>

        <div
          className="mb-4 flex items-center justify-between rounded-lg p-2.5"
          style={{ background: "var(--input-bg)", border: "1px solid var(--input-border)" }}
        >
          <div className="text-[11px]" style={{ color: "var(--text-dim)" }}>
            <span>{t("update.current")}: </span>
            <span className="font-mono text-foreground font-medium">v{updateInfo.current_version}</span>
          </div>
          <div className="text-[11px]" style={{ color: "var(--text-dim)" }}>
            <span>{t("update.latest")}: </span>
            <span className="font-mono font-semibold text-emerald-400">v{updateInfo.latest_version}</span>
          </div>
        </div>

        {updateInfo.release_notes && (
          <div className="mb-5">
            <div className="text-[10.5px] font-medium mb-1.5" style={{ color: "var(--text-dim)" }}>
              {t("update.changelog")}
            </div>
            <div
              className="max-h-[160px] overflow-y-auto rounded-lg p-3 text-[11px] leading-relaxed font-mono whitespace-pre-wrap"
              style={{
                background: "var(--log-bg)",
                color: "var(--log-text)",
                border: "1px solid var(--card-border)",
              }}
            >
              {updateInfo.release_notes}
            </div>
          </div>
        )}

        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="btn-secondary flex-1 py-2 text-[12px] font-medium"
            style={{ borderRadius: 8 }}
          >
            {t("update.close")}
          </button>
          <button
            onClick={() => {
              window.open(updateInfo.release_url, "_blank");
              onClose();
            }}
            className="btn-primary flex-1 py-2 text-[12px] font-medium"
            style={{ borderRadius: 8 }}
          >
            {t("update.download_btn")}
          </button>
        </div>
      </div>
    </div>
  );
}