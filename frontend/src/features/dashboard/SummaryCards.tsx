import { formatMoney } from "@/lib/format";
import { Summary } from "@/types/analytics";

export function SummaryCards({ summary }: { summary: Summary }) {
  const top = [...summary.categories].sort((a, b) => b.amount - a.amount)[0];
  const count = summary.categories.reduce((acc, item) => acc + item.count, 0);

  const items = [
    { label: "всего", value: formatMoney(summary.total, null) },
    { label: "топ категория", value: top ? top.category : "—" },
    { label: "чеков", value: String(count) },
  ];

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
      {items.map((item) => (
        <div key={item.label}>
          <p className="text-sm text-roast-500 dark:text-roast-300">{item.label}</p>
          <p className="mt-1 text-2xl font-medium tracking-tight text-roast-950 dark:text-foam-50">
            {item.value}
          </p>
        </div>
      ))}
    </div>
  );
}
