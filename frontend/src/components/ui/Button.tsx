import { ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "ghost" | "danger";
}

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  const base =
    "inline-flex items-center justify-center rounded-xl px-3.5 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50";
  const styles =
    variant === "primary"
      ? "bg-cocoa-700 text-foam-50 hover:bg-cocoa-600 dark:bg-cocoa-300 dark:text-roast-950 dark:hover:bg-cocoa-200"
      : variant === "danger"
        ? "bg-rose-700 text-foam-50 hover:bg-rose-600"
        : "bg-transparent text-roast-600 hover:bg-foam-200/60 dark:text-foam-200 dark:hover:bg-roast-800/60";
  return <button className={`${base} ${styles} ${className}`} {...props} />;
}
