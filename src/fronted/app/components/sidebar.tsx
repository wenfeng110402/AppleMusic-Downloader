"use client";

import { useI18n } from "../i18n";
import { useTheme } from "../theme";

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

  return (
    <nav className="flex h-screen w-[220px] shrink-0 flex-col" style={{ background: "var(--sidebar-bg)" }}>
      {/* Drag region + Title */}
      <div className="shrink-0 px-5 pt-5 pb-4" style={{ WebkitAppRegion: "drag" } as React.CSSProperties}>
        <div className="text-[11px] font-medium tracking-[0.04em] uppercase text-foreground/20">
          AMDL
        </div>
      </div>

      {/* Separator */}
      <div className="mx-4 h-px" style={{ background: "var(--divider)" }} />

      {/* Nav items */}
      <div className="flex-1 overflow-y-auto px-2 py-3">
        <ul className="flex flex-col gap-px">
          {NAV_ITEMS.map((item) => {
            const isSelected = active === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => onNavigate(item.id)}
                  className={[
                    "group relative flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-[12.5px] font-medium transition-all duration-150",
                    isSelected
                      ? "text-foreground"
                      : "text-foreground/35 hover:text-foreground/65",
                  ].join(" ")}
                >
                  {/* Left accent bar */}
                  <span
                    className={[
                      "absolute inset-y-1.5 left-0 w-[2.5px] rounded-full transition-all duration-200",
                      isSelected
                        ? "bg-[#ef4444] opacity-100"
                        : "bg-[#ef4444] opacity-0 group-hover:opacity-30",
                    ].join(" ")}
                  />
                  {/* Icon */}
                  <span
                    className={[
                      "transition-colors duration-150",
                      isSelected ? "text-[#ef4444]" : "",
                    ].join(" ")}
                  >
                    {item.icon}
                  </span>
                  {/* Label */}
                  <span>{t(item.key)}</span>
                  {/* Selected dot */}
                  {isSelected && (
                    <span className="ml-auto h-1.5 w-1.5 rounded-full bg-[#ef4444]" />
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
          <span className="px-2 text-[10px] text-foreground/20">{t("nav.language")}</span>
          <div className="ml-auto flex rounded-md border p-0.5" style={{ borderColor: "var(--card-border)" }}>
            <button
              onClick={() => setLocale("zh")}
              className={[
                "rounded px-2 py-0.5 text-[10px] font-medium transition-all duration-150",
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
                "rounded px-2 py-0.5 text-[10px] font-medium transition-all duration-150",
                locale === "en"
                  ? "bg-[#ef4444] text-white"
                  : "text-foreground/35 hover:text-foreground/60",
              ].join(" ")}
            >
              EN
            </button>
          </div>
        </div>

        {/* Theme switcher */}
        <div className="flex items-center gap-1 px-2 py-2">
          {/* <span className="px-2 text-[10px] text-foreground/20">{t("nav.theme")}</span> */}
          <div className="ml-auto flex rounded-md border p-0.5" style={{ borderColor: "var(--card-border)" }}>
            <button
              onClick={() => setTheme("dark")}
              className={[
                "rounded px-2 py-0.5 text-[10px] font-medium transition-all duration-150",
                theme === "dark"
                  ? "bg-[#ef4444] text-white"
                  : "text-foreground/35 hover:text-foreground/60",
              ].join(" ")}
            >
              {t("nav.theme.dark")}
            </button>
            <button
              onClick={() => setTheme("light")}
              className={[
                "rounded px-2 py-0.5 text-[10px] font-medium transition-all duration-150",
                theme === "light"
                  ? "bg-[#ef4444] text-white"
                  : "text-foreground/35 hover:text-foreground/60",
              ].join(" ")}
            >
              {t("nav.theme.light")}
            </button>
          </div>
        </div>

        {/* Version */}
        <div className="px-5 py-3">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500/70" />
            <span className="text-[10.5px] text-foreground/20">v2.4.6</span>
          </div>
        </div>
      </div>
    </nav>
  );
}