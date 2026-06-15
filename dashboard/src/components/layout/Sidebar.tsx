"use client";

import clsx from "clsx";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "./Logo";

const NAV = [
  { href: "/", label: "Overview" },
  { href: "/runs", label: "Runs" },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="hidden w-56 shrink-0 flex-col gap-1 border-r border-border bg-panel px-3 py-4 md:flex">
      <Link href="/" className="mb-4 flex items-center gap-2 px-2">
        <Logo size={26} className="shrink-0" />
        <span>
          <span className="block text-sm font-semibold text-ink">
            AnchorPrune
          </span>
          <span className="block text-xs text-muted">
            Governed state microscope
          </span>
        </span>
      </Link>
      {NAV.map((item) => {
        const active =
          item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "rounded-md px-2 py-1.5 text-sm transition-colors",
              active
                ? "bg-panel2 text-ink"
                : "text-muted hover:bg-panel2/60 hover:text-ink",
            )}
          >
            {item.label}
          </Link>
        );
      })}
      <span className="mt-auto px-2 text-[10px] leading-relaxed text-muted">
        Read-only. The dashboard observes governance; it does not perform it.
      </span>
    </aside>
  );
}
