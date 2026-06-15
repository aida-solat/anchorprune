import { DASHBOARD_VERSION } from "@/lib/version";

import { ApiStatus } from "./ApiStatus";
import { Logo } from "./Logo";

export function Header() {
  return (
    <header className="flex items-center justify-between border-b border-border bg-panel/80 px-5 py-3 backdrop-blur">
      <div className="flex items-center gap-2">
        <Logo size={20} className="md:hidden" />
        <span className="text-sm font-semibold text-ink md:hidden">
          AnchorPrune
        </span>
        <span className="hidden text-xs text-muted md:block">
          Governed State Graph Dashboard
        </span>
      </div>
      <div className="flex items-center gap-2">
        <span className="inline-flex items-center rounded-md border border-border bg-panel2 px-2.5 py-1 text-xs text-muted">
          Dashboard v{DASHBOARD_VERSION}
        </span>
        <ApiStatus />
      </div>
    </header>
  );
}
