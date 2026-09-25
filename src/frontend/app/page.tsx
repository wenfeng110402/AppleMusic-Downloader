"use client";

import { useState } from "react";
import Sidebar from "./components/sidebar";
import Download from "./components/download";
import Queue from "./components/queue";
import Settings from "./components/settings";
import HowToInstallDependencies from "./components/howToInstallDependencies";

export default function Page() {
  const [active, setActive] = useState("download");

  if (active === "how-to-install") {
    return (
      <div className="flex h-screen w-screen overflow-hidden" style={{ background: "var(--background)", color: "var(--foreground)" }}>
        <HowToInstallDependencies onBack={() => setActive("settings")} />
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "var(--background)", color: "var(--foreground)" }}>
      <Sidebar active={active} onNavigate={setActive} />
      <main className="flex flex-1 flex-col overflow-hidden">
        {active === "download" && <Download onNavigate={setActive} />}
        {active === "queue" && <Queue />}
        {active === "settings" && <Settings onNavigate={setActive} />}
      </main>
    </div>
  );
}