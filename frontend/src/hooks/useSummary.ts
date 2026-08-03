import { useEffect, useState } from "react";

import { getSummary } from "@/api/analytics";
import { Summary } from "@/types/analytics";

export function useSummary(period: string) {
  const [data, setData] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    getSummary(period)
      .then((summary) => {
        if (active) {
          setData(summary);
          setError(null);
        }
      })
      .catch(() => {
        if (active) {
          setError("Не удалось загрузить статистику");
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [period]);

  return { data, loading, error };
}
