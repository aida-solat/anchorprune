import clsx from "clsx";
import type { ReactNode } from "react";

export function Table({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full border-collapse text-sm">{children}</table>
    </div>
  );
}

export function THead({ columns }: { columns: string[] }) {
  return (
    <thead>
      <tr className="border-b border-border bg-panel2 text-left text-xs uppercase tracking-wide text-muted">
        {columns.map((c) => (
          <th key={c} className="px-3 py-2 font-medium">
            {c}
          </th>
        ))}
      </tr>
    </thead>
  );
}

export function TRow({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <tr className={clsx("border-b border-border/60 last:border-0", className)}>
      {children}
    </tr>
  );
}

export function TCell({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return <td className={clsx("px-3 py-2 align-top", className)}>{children}</td>;
}
