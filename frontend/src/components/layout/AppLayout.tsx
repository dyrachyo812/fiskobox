import { ReactNode } from "react";
import { NavLink } from "react-router-dom";

import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/features/auth/useAuth";

function linkClass({ isActive }: { isActive: boolean }): string {
  return isActive
    ? "text-sm font-medium text-roast-950 dark:text-foam-50"
    : "text-sm text-roast-500 transition hover:text-roast-800 dark:text-roast-300 dark:hover:text-foam-100";
}

export function AppLayout({ children }: { children: ReactNode }) {
  const { logout } = useAuth();

  return (
    <div className="page-shell">
      <header className="border-b border-roast-200/60 dark:border-roast-800/70">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div className="flex items-center gap-8">
            <NavLink to="/" className="text-lg font-medium tracking-tight">
              fiskobox
            </NavLink>
            <nav className="flex items-center gap-5">
              <NavLink to="/" end className={linkClass}>
                обзор
              </NavLink>
              <NavLink to="/documents" className={linkClass}>
                чеки
              </NavLink>
            </nav>
          </div>
          <div className="flex items-center gap-1">
            <ThemeToggle />
            <Button variant="ghost" onClick={logout}>
              выйти
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6">{children}</main>
    </div>
  );
}
