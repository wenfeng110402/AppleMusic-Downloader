"use client";

import { useState, useRef, type KeyboardEvent } from "react";

interface TagInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function parseTags(value: string): string[] {
  return value
    .split("\n")
    .map((s) => s.trim())
    .filter(Boolean);
}

export default function TagInput({ value, onChange, placeholder }: TagInputProps) {
  const tags = parseTags(value);
  const [input, setInput] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const add = (tag: string) => {
    const trimmed = tag.trim();
    if (!trimmed) return;
    if (tags.includes(trimmed)) {
      setInput("");
      return;
    }
    onChange([...tags, trimmed].join("\n"));
    setInput("");
  };

  const remove = (index: number) => {
    const next = tags.filter((_, i) => i !== index);
    onChange(next.join("\n"));
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      add(input);
    } else if (e.key === "Backspace" && input === "" && tags.length > 0) {
      remove(tags.length - 1);
    }
  };

  const handleContainerClick = () => {
    inputRef.current?.focus();
  };

  return (
    <div
      className="input mb-4 flex min-h-[80px] cursor-text flex-wrap items-start gap-1.5 py-2.5"
      onClick={handleContainerClick}
    >
      {tags.map((tag, i) => (
        <span
          key={`${tag}-${i}`}
          className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[12px] transition-colors"
          style={{ background: "var(--card-border)", color: "var(--text-body)" }}
        >
          <span className="max-w-[260px] truncate">{tag}</span>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              remove(i);
            }}
            className="ml-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full transition-colors hover:bg-white/10 hover:text-foreground"
            style={{ color: "var(--text-muted)" }}
          >
            <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </span>
      ))}
      <input
        ref={inputRef}
        className="min-w-[120px] flex-1 bg-transparent py-0.5 text-[12.5px] outline-none placeholder:text-[var(--text-muted)]"
        style={{ color: "var(--foreground)" }}
        placeholder={tags.length === 0 ? placeholder : ""}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
      />
    </div>
  );
}