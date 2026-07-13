"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useTasks, useCancelTask, statusColor } from "../service";
import { useI18n } from "../i18n";
import type { TaskInfo } from "../service";

export default function Queue() {
  const { t } = useI18n();
  const { tasks, refresh } = useTasks();
  const cancelTask = useCancelTask(refresh);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    refresh();
    if (!autoRefresh) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }
    timerRef.current = setInterval(refresh, 3000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [autoRefresh, refresh]);

  const toggle = useCallback((id: string) => {
    setExpanded((prev) => (prev === id ? null : id));
  }, []);

  if (tasks.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center overflow-y-auto">
        <div
          className="flex h-16 w-16 items-center justify-center rounded-2xl"
          style={{
            background: "var(--card-bg)",
            border: "1px solid var(--card-border)",
            animation: "spring-in 0.5s var(--ease-spring-bounce) both",
          }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--text-muted)" }}>
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="12" y1="3" x2="12" y2="21" />
          </svg>
        </div>
        <p className="mt-4 text-[12px]" style={{ color: "var(--text-muted)", animation: "fade-in-up 0.4s var(--ease-spring) 0.1s both" }}>{t("queue.empty")}</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-y-auto scroll-edge-top">
      <div className="mx-auto w-full max-w-[640px] px-6 py-6">
        {/* Header */}
        <div className="mb-5 flex items-center justify-between">
          <div>
            <h2 className="text-[15px] font-semibold tracking-[-0.01em]" style={{ color: "var(--text-heading)" }}>{t("queue.title")}</h2>
            <p className="mt-0.5 text-[10.5px]" style={{ color: "var(--text-muted)" }}>
              {t("queue.count", { count: tasks.length })}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10.5px]" style={{ color: "var(--text-dim)" }}>{t("queue.auto")}</span>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={[
                "relative h-[18px] w-[32px] shrink-0 rounded-full transition-colors duration-150",
                autoRefresh ? "bg-[#ef4444]" : "bg-[var(--card-border)]",
              ].join(" ")}
            >
              <span
                className={[
                  "absolute top-[2px] h-[14px] w-[14px] rounded-full bg-white transition-all duration-150 shadow-sm",
                  autoRefresh ? "left-[16px]" : "left-[2px]",
                ].join(" ")}
              />
            </button>
          </div>
        </div>

        {/* Tasks list */}
        <div className="space-y-2">
          {tasks.map((task) => (
            <TaskRow
              key={task.id}
              task={task}
              expanded={expanded === task.id}
              onToggle={() => toggle(task.id)}
              onCancel={() => cancelTask(task.id)}
            />
          ))}
        </div>

        <div className="h-4" />
      </div>
    </div>
  );
}

// ── TaskRow ──

function TaskRow({
  task,
  expanded,
  onToggle,
  onCancel,
}: {
  task: TaskInfo;
  expanded: boolean;
  onToggle: () => void;
  onCancel: () => void;
}) {
  const { t } = useI18n();
  const [copied, setCopied] = useState(false);
  const progress = task.progress as Record<string, number>;
  const { completed = 0, total = 0, percent } = progress;
  const pct = task.status === "completed"
    ? 1
    : total > 0
      ? (percent ?? (completed / total * 100)) / 100
      : 0;
  const isRunning = task.status === "running" || task.status === "pending";

  const handleCopyLogs = useCallback(async () => {
    if (!task.logs || task.logs.length === 0) return;
    try {
      await navigator.clipboard.writeText(task.logs.join("\n"));
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch { /* clipboard not available */ }
  }, [task.logs]);

  return (
    <div className="card">
      {/* ── Header row ── */}
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <p className="truncate text-[12px]" style={{ color: "var(--text-body)" }} title={task.urls.join(", ")}>
              {task.urls[0] || task.id}
              {task.urls.length > 1 && ` (+${task.urls.length - 1})`}
            </p>
            <span className={`shrink-0 rounded-full px-2 py-0.5 text-[9px] font-medium ${statusColor(task.status)}`}>
              {t(`status.${task.status}`)}
            </span>
          </div>
          {pct > 0 && (
            <div className="mt-1.5 h-[3px] w-full overflow-hidden rounded-full" style={{ background: "var(--card-border)" }}>
              <div
                className={[
                  "h-full transition-all duration-300",
                  task.status === "completed" ? "bg-green-500" : "bg-blue-500",
                ].join(" ")}
                style={{ width: `${Math.round(pct * 100)}%` }}
              />
            </div>
          )}
        </div>

        {isRunning ? (
          <button
            onClick={(e) => { e.stopPropagation(); onCancel(); }}
            className="shrink-0 rounded border border-red-500/30 bg-red-500/10 px-2 py-1 text-[10px] font-medium text-red-400 hover:bg-red-500/20"
          >
            {t("queue.cancel")}
          </button>
        ) : (
          <div className="shrink-0 w-[48px]" />
        )}

        <svg
          width="12" height="12" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          className="shrink-0"
          style={{
            color: "rgba(255,255,255,0.25)",
            transition: "transform 0.35s var(--ease-spring-bounce)",
            transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* ── Expanded: logs ── */}
      <div
        className="overflow-hidden"
        style={{
          transition: "max-height 0.4s var(--ease-spring), opacity 0.3s var(--ease-spring)",
          maxHeight: expanded ? "400px" : "0px",
          opacity: expanded ? 1 : 0,
        }}
      >
        <div className="border-t px-4 py-3" style={{ borderColor: "var(--card-border)" }}>
          {task.logs && task.logs.length > 0 ? (
            <>
              <div className="mb-2 flex justify-end">
                <button
                  onClick={handleCopyLogs}
                  className="rounded px-2 py-0.5 text-[10px] font-medium transition-colors hover:bg-white/5"
                  style={{ color: copied ? "#22c55e" : "var(--text-dim)" }}
                >
                  {copied ? "Copied" : "Copy"}
                </button>
              </div>
              <div className="max-h-[300px] overflow-y-auto rounded p-3 font-mono text-[10.5px] leading-relaxed" style={{ background: "var(--log-bg)", color: "var(--log-text)" }}>
                {task.logs.map((line, i) => (
                  <div key={i} className="break-all">
                    {line}
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="py-2 text-center text-[11px]" style={{ color: "var(--text-muted)" }}>{t("queue.no_logs")}</p>
          )}
        </div>
      </div>
    </div>
  );
}