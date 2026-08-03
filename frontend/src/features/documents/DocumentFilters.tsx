import { useCategories } from "@/hooks/useCategories";

export interface FilterState {
  status: string;
  category: string;
  dateFrom: string;
  dateTo: string;
}

const statuses = [
  { value: "", label: "все статусы" },
  { value: "done", label: "готово" },
  { value: "processing", label: "обработка" },
  { value: "pending", label: "очередь" },
  { value: "failed", label: "ошибка" },
];

interface Props {
  value: FilterState;
  onChange: (value: FilterState) => void;
}

export function DocumentFilters({ value, onChange }: Props) {
  const categories = useCategories();
  const patch = (changes: Partial<FilterState>) => onChange({ ...value, ...changes });

  return (
    <div className="flex flex-nowrap items-center gap-2 overflow-x-auto pb-1">
      <select
        className="field-input shrink-0"
        value={value.status}
        onChange={(event) => patch({ status: event.target.value })}
      >
        {statuses.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <select
        className="field-input shrink-0"
        value={value.category}
        onChange={(event) => patch({ category: event.target.value })}
      >
        <option value="">все категории</option>
        {categories.map((category) => (
          <option key={category.id} value={category.name}>
            {category.name}
          </option>
        ))}
      </select>
      <div className="flex shrink-0 items-center gap-2 text-sm text-roast-500 dark:text-roast-300">
        <label className="flex items-center gap-2">
          <span>от</span>
          <input
            className="field-input w-[10.5rem]"
            type="date"
            value={value.dateFrom}
            onChange={(event) => patch({ dateFrom: event.target.value })}
          />
        </label>
        <label className="flex items-center gap-2">
          <span>до</span>
          <input
            className="field-input w-[10.5rem]"
            type="date"
            value={value.dateTo}
            onChange={(event) => patch({ dateTo: event.target.value })}
          />
        </label>
      </div>
    </div>
  );
}
