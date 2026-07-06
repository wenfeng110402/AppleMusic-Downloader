"use client";

import { useState } from "react";
import {
  useBackendStatus,
  useTasks,
  useSubmitTask,
  useCancelTask,
  DEFAULT_FORM,
  FormState,
} from "./service";
import Sidebar from "./widgets/sidebar";

export default function Page() {
  const backendOnline = useBackendStatus();
  const { tasks, refresh: refreshTasks } = useTasks();
  const submitTask = useSubmitTask(refreshTasks);
  const cancelTask = useCancelTask(refreshTasks);

  const [form, setForm] = useState<FormState>(DEFAULT_FORM);

  function updateForm<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSubmit() {
    await submitTask(form);
    setForm((prev) => ({ ...prev, urls: "" }));
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      
      <Sidebar />
      {/* Download form - write your UI here */}
      <section>
        <textarea
          placeholder="URLs (one per line)"
          value={form.urls}
          onChange={(e) => updateForm("urls", e.target.value)}
        />
        <input
          placeholder="cookies.txt path"
          value={form.cookies_path}
          onChange={(e) => updateForm("cookies_path", e.target.value)}
        />
        <button onClick={handleSubmit}>Submit</button>
      </section>

      {/* Task list - write your UI here */}
      <section>
        <button onClick={refreshTasks}>Refresh</button>
        {tasks.length === 0 && <p>No tasks</p>}
        <ul>
          {tasks.map((t) => (
            <li key={t.id}>
              <span>{t.status}</span> | <span>{t.message}</span>{" "}
              <button onClick={() => cancelTask(t.id)}>Cancel</button>
            </li>
          ))}
        </ul>
      </section>

      {!backendOnline && <p>Backend not running</p>}
    </div>
  );
}