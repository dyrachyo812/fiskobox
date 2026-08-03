import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/features/auth/useAuth";

const botUsername = import.meta.env.VITE_TELEGRAM_BOT_USERNAME ?? "";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login(code.trim());
      navigate("/");
    } catch {
      setError("неверный или просроченный код");
    } finally {
      setLoading(false);
    }
  };

  const botLink = botUsername ? `https://t.me/${botUsername}` : "#";

  return (
    <div className="page-shell relative flex min-h-screen items-center justify-center px-4 py-10">
      <div className="absolute right-4 top-4">
        <ThemeToggle />
      </div>

      <div className="w-full max-w-sm">
        <h1 className="text-3xl font-medium tracking-tight">fiskobox</h1>
        <p className="mt-2 text-sm text-roast-500 dark:text-roast-300">
          чеки из telegram в одном месте
        </p>

        <form onSubmit={submit} className="mt-8 space-y-3">
          <input
            value={code}
            onChange={(event) => setCode(event.target.value)}
            inputMode="numeric"
            placeholder="код из /link"
            className="field-input w-full"
          />
          {error && <p className="text-sm text-rose-600 dark:text-rose-300">{error}</p>}
          <Button
            type="submit"
            className="w-full"
            disabled={loading || code.trim().length === 0}
          >
            {loading ? "вход…" : "войти"}
          </Button>
        </form>

        <a
          href={botLink}
          target="_blank"
          rel="noreferrer"
          className="mt-4 block text-center text-sm text-roast-500 transition hover:text-roast-800 dark:text-roast-300 dark:hover:text-foam-100"
        >
          открыть бота
        </a>
      </div>
    </div>
  );
}
