import { useTheme } from "@/lib/useTheme";

export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "Светлая тема" : "Тёмная тема"}
      title={isDark ? "Светлая тема" : "Тёмная тема"}
      className="inline-flex h-9 w-9 items-center justify-center rounded-lg text-roast-600 transition hover:bg-foam-200/70 dark:text-foam-200 dark:hover:bg-roast-800/70"
    >
      {isDark ? (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="3.5" fill="currentColor" />
          <path
            d="M12 3v1.8M12 19.2V21M5.2 5.2l1.3 1.3M17.5 17.5l1.3 1.3M3 12h1.8M19.2 12H21M5.2 18.8l1.3-1.3M17.5 6.5l1.3-1.3"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
        </svg>
      ) : (
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor" aria-hidden="true">
          <path d="M20.5 14.2A7.8 7.8 0 0 1 9.8 3.5 6.7 6.7 0 1 0 20.5 14.2Z" />
        </svg>
      )}
    </button>
  );
}
