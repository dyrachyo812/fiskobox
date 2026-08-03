import { useEffect, useState } from "react";

import { CategoryItem, listCategories } from "@/api/categories";

export function useCategories() {
  const [categories, setCategories] = useState<CategoryItem[]>([]);

  useEffect(() => {
    let active = true;
    listCategories()
      .then((items) => {
        if (active) {
          setCategories(items);
        }
      })
      .catch(() => {
        if (active) {
          setCategories([]);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  return categories;
}
