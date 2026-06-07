import clsx from "clsx";
import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost";
};

export function Button({ variant = "primary", className, ...props }: Props) {
  return (
    <button
      className={clsx(
        "inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:opacity-50",
        variant === "primary"
          ? "bg-accent text-white hover:bg-accent/80"
          : "border border-border bg-panel2 text-ink hover:border-accent/50",
        className,
      )}
      {...props}
    />
  );
}
