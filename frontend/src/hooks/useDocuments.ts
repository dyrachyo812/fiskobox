import { useCallback, useEffect, useState } from "react";

import { DocumentQuery, listDocuments } from "@/api/documents";
import { DocumentListResult } from "@/types/document";

export function useDocuments(query: DocumentQuery) {
  const { limit, offset, status, category, dateFrom, dateTo } = query;
  const [data, setData] = useState<DocumentListResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  const reload = useCallback(() => setTick((current) => current + 1), []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    listDocuments({ limit, offset, status, category, dateFrom, dateTo })
      .then((result) => {
        if (active) {
          setData(result);
          setError(null);
        }
      })
      .catch(() => {
        if (active) {
          setError("Не удалось загрузить документы");
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
  }, [limit, offset, status, category, dateFrom, dateTo, tick]);

  return { data, loading, error, reload };
}
