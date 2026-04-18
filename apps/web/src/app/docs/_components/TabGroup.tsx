"use client";

import { useState } from "react";

interface Tab {
  label: string;
  content: React.ReactNode;
}

interface TabGroupProps {
  tabs: Tab[];
}

export function TabGroup({ tabs }: TabGroupProps) {
  const [active, setActive] = useState(0);

  return (
    <div>
      <div
        className="flex gap-0 rounded-t-lg overflow-hidden"
        style={{ borderBottom: "1px solid rgba(79,70,51,0.15)" }}
      >
        {tabs.map((tab, i) => (
          <button
            key={tab.label}
            onClick={() => setActive(i)}
            className={`px-4 py-2.5 text-xs font-medium transition-colors ${
              active === i
                ? "bg-surface-container-lowest text-primary border-b-2 border-primary"
                : "bg-surface-container-low text-on-surface/40 hover:text-on-surface/60"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div>{tabs[active].content}</div>
    </div>
  );
}
