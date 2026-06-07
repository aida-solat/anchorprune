"use client";

import { getHealth } from "@/lib/api";
import { useResource } from "@/lib/useResource";

export function ApiStatus() {
  const { data, error, loading } = useResource(getHealth, []);

  let dot = "bg-warn";
  let text = "connecting…";
  if (!loading && data) {
    dot = "bg-ok";
    text = `Service v${data.version}`;
  } else if (!loading && error) {
    dot = "bg-danger";
    text = "Service unreachable";
  }

  return (
    <span
      className="inline-flex items-center gap-2 rounded-md border border-border bg-panel2 px-2.5 py-1 text-xs text-muted"
      title={error ?? undefined}
    >
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      {text}
    </span>
  );
}
