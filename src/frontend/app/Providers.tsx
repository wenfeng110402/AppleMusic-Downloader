"use client";

import { I18nProvider } from "./i18n";
import { ThemeProvider } from "./theme";
import { ToastProvider } from "./components/Toast";
import type { ReactNode } from "react";

export default function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <I18nProvider>
        <ToastProvider>
          {children}
        </ToastProvider>
      </I18nProvider>
    </ThemeProvider>
  );
}