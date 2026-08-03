import { apiClient } from "@/api/client";
import { Summary } from "@/types/analytics";

interface RawCategory {
  category: string;
  amount: number | string;
  count: number;
}

interface RawSummary {
  period: string;
  total: number | string;
  categories: RawCategory[];
}

export async function getSummary(period: string): Promise<Summary> {
  const { data } = await apiClient.get<RawSummary>("/analytics/summary", {
    params: { period },
  });
  return {
    period: data.period,
    total: Number(data.total),
    categories: data.categories.map((item) => ({
      category: item.category,
      amount: Number(item.amount),
      count: item.count,
    })),
  };
}
