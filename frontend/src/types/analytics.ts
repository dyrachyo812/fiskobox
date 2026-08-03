export interface CategorySummary {
  category: string;
  amount: number;
  count: number;
}

export interface Summary {
  period: string;
  total: number;
  categories: CategorySummary[];
}
