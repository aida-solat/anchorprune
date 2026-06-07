import clsx from "clsx";
import type { ReactNode } from "react";

export type BadgeTone =
  | "neutral"
  | "system"
  | "domain"
  | "runtime"
  | "milestone"
  | "ok"
  | "warn"
  | "danger";

const TONE: Record<BadgeTone, string> = {
  neutral: "border-border bg-panel2 text-muted",
  system: "border-system/40 bg-system/10 text-system",
  domain: "border-domain/40 bg-domain/10 text-domain",
  runtime: "border-runtime/40 bg-runtime/10 text-runtime",
  milestone: "border-milestone/40 bg-milestone/10 text-milestone",
  ok: "border-ok/40 bg-ok/10 text-ok",
  warn: "border-warn/40 bg-warn/10 text-warn",
  danger: "border-danger/40 bg-danger/10 text-danger",
};

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: BadgeTone;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs font-medium",
        TONE[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
