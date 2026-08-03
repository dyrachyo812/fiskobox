import { apiClient } from "@/api/client";

export interface CategoryItem {
  id: number;
  name: string;
}

interface RawList {
  items: CategoryItem[];
}

export async function listCategories(): Promise<CategoryItem[]> {
  const { data } = await apiClient.get<RawList>("/categories");
  return data.items;
}
