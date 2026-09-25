"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useRef,
  type ReactNode,
} from "react";

// ── Types ────────────────────────────────────────────────────

export type ToastType = "success" | "error" | "info";

interface ToastItem {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  show: (message: string, type?: ToastType) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
}

// ── Context ──────────────────────────────────────────────────

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside <ToastProvider>");
  return ctx;
}

// ── Provider ─────────────────────────────────────────────────

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const counterRef = useRef(0);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const show = useCallback(
    (message: string, type: ToastType = "info") => {
      const id = ++counterRef.current;
      setToasts((prev) => [...prev, { id, type, message }]);
      setTimeout(() => dismiss(id), 3500);
    },
    [dismiss]
  );

  const value: ToastContextValue = {
    show,
    success: useCallback((m) => show(m, "success"), [show]),
    error: useCallback((m) => show(m, "error"), [show]),
    info: useCallback((m) => show(m, "info"), [show]),
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

// ── Toast Container ───────────────────────────────────────────

function ToastContainer({
  toasts,
  onDismiss,
}: {
  toasts: ToastItem[];
  onDismiss: (id: number) => void;
}) {
  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 16,
        right: 16,
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        pointerEvents: "none",
      }}
    >
      {toasts.map((t) => (
        <ToastBubble key={t.id} item={t} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

// ── Single Toast Bubble ───────────────────────────────────────

const ICONS: Record<ToastType, string> = {
  success: "✓",
  error: "✕",
  info: "i",
};

const ACCENT: Record<ToastType, string> = {
  success: "#22c55e",
  error:   "#ef4444",
  info:    "#60a5fa",
};

function ToastBubble({
  item,
  onDismiss,
}: {
  item: ToastItem;
  onDismiss: (id: number) => void;
}) {
  const accent = ACCENT[item.type];

  return (
    <div
      style={{
        pointerEvents: "auto",
        display: "flex",
        alignItems: "flex-start",
        gap: 10,
        minWidth: 240,
        maxWidth: 360,
        padding: "10px 14px",
        borderRadius: 10,
        background: "var(--card-bg)",
        border: `1px solid ${accent}33`,
        boxShadow: `0 4px 20px rgba(0,0,0,0.25), 0 0 0 1px ${accent}22`,
        backdropFilter: "blur(12px)",
        animation: "toast-in 0.28s var(--ease-spring-bounce) both",
      }}
    >
      {/* icon */}
      <span
        style={{
          flexShrink: 0,
          width: 18,
          height: 18,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderRadius: "50%",
          background: `${accent}22`,
          color: accent,
          fontSize: 10,
          fontWeight: 700,
          marginTop: 1,
        }}
      >
        {ICONS[item.type]}
      </span>

      {/* message */}
      <span
        style={{
          flex: 1,
          fontSize: 12,
          lineHeight: 1.5,
          color: "var(--text-body)",
          wordBreak: "break-word",
        }}
      >
        {item.message}
      </span>

      {/* close */}
      <button
        onClick={() => onDismiss(item.id)}
        style={{
          flexShrink: 0,
          background: "none",
          border: "none",
          cursor: "pointer",
          color: "var(--text-muted)",
          fontSize: 14,
          lineHeight: 1,
          padding: 0,
          marginTop: 1,
        }}
      >
        ×
      </button>
    </div>
  );
}
