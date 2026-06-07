"use client";

import clsx from "clsx";
import type { ReactNode } from "react";

export interface TabDef {
  id: string;
  label: string;
  count?: number;
}

export function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: TabDef[];
  active: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1 border-b border-border">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={clsx(
            "relative px-3 py-2 text-sm font-medium transition-colors",
            active === tab.id
              ? "text-ink"
              : "text-muted hover:text-ink",
          )}
        >
          <span className="flex items-center gap-1.5">
            {tab.label}
            {typeof tab.count === "number" ? (
              <span className="rounded bg-panel2 px-1.5 py-0.5 text-xs tabular-nums text-muted">
                {tab.count}
              </span>
            ) : null}
          </span>
          {active === tab.id ? (
            <span className="absolute inset-x-2 -bottom-px h-0.5 rounded bg-accent" />
          ) : null}
        </button>
      ))}
    </div>
  );
}

export function TabPanel({
  when,
  active,
  children,
}: {
  when: string;
  active: string;
  children: ReactNode;
}) {
  if (when !== active) return null;
  return <div className="pt-4">{children}</div>;
}
