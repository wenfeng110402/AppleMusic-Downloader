    "use client";

    import { useState } from "react";
    import { useBackendStatus } from "../service";

    // 导航项定义：id + 图标 + 文字
    const NAV_ITEMS = [
    { id: "download", label: "Download" },
    { id: "queue", label: "Queue" },
    { id: "settings", label: "Settings" },
    ];

    export default function Sidebar() {
    const [active, setActive] = useState("download");
    const online = useBackendStatus();

    return (
        <nav className="flex h-screen w-60 flex-col bg-gray-950 border-r border-gray-800">
        {/* Logo */}
        <div className="flex items-center gap-2 px-5 py-5">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9.92 11.354c.966 0 1.453-.487 1.453-1.49v-3.4c0-1.004-.487-1.483-1.453-1.483H6.452C5.487 4.981 5 5.46 5 6.464v3.4c0 1.003.487 1.49 1.452 1.49zm7.628 0c.965 0 1.452-.487 1.452-1.49v-3.4c0-1.004-.487-1.483-1.452-1.483h-3.46c-.974 0-1.46.479-1.46 1.483v3.4c0 1.003.486 1.49 1.46 1.49zm-7.65-1.073h-3.43c-.266 0-.396-.137-.396-.418v-3.4c0-.273.13-.41.396-.41h3.43c.265 0 .402.137.402.41v3.4c0 .281-.137.418-.403.418zm7.634 0h-3.43c-.273 0-.402-.137-.402-.418v-3.4c0-.273.129-.41.403-.41h3.43c.265 0 .395.137.395.41v3.4c0 .281-.13.418-.396.418zm-7.612 8.7c.966 0 1.453-.48 1.453-1.483v-3.407c0-.996-.487-1.483-1.453-1.483H6.452c-.965 0-1.452.487-1.452 1.483v3.407c0 1.004.487 1.483 1.452 1.483zm7.628 0c.965 0 1.452-.48 1.452-1.483v-3.407c0-.996-.487-1.483-1.452-1.483h-3.46c-.974 0-1.46.487-1.46 1.483v3.407c0 1.004.486 1.483 1.46 1.483zm-7.65-1.072h-3.43c-.266 0-.396-.137-.396-.41v-3.4c0-.282.13-.418.396-.418h3.43c.265 0 .402.136.402.418v3.4c0 .273-.137.41-.403.41zm7.634 0h-3.43c-.273 0-.402-.137-.402-.41v-3.4c0-.282.129-.418.403-.418h3.43c.265 0 .395.136.395.418v3.4c0 .273-.13.41-.396.41z"/>
            </svg>
            <span className={`ml-auto h-2 w-2 rounded-full ${online ? "bg-green-500" : "bg-red-500"}`} />
        </div>

        {/* Navigation list */}
        <ul className="flex-1 px-2">
            {NAV_ITEMS.map((item) => (
            <li key={item.id}>
                <button
                onClick={() => setActive(item.id)}
                className={`w-full rounded-lg px-3 py-2 text-left text-sm transition
                    ${active === item.id
                    ? "bg-white/10 text-white"
                    : "text-gray-400 hover:bg-white/5 hover:text-gray-200"
                    }`}
                >
                {item.label}
                </button>
            </li>
            ))}
        </ul>

        {/* Bottom */}
        <div className="border-t border-gray-800 px-4 py-3 text-xs text-gray-500">
            v1.0.0
        </div>
        </nav>
    );
    }