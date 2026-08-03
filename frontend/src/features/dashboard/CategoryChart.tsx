import { formatMoney } from "@/lib/format";
import { Summary } from "@/types/analytics";

export function CategoryChart({ summary }: { summary: Summary }) {
  const data = [...summary.categories].sort((a, b) => b.amount - a.amount);
  const max = Math.max(...data.map((item) => item.amount), 1);

  return (
    <section>
      <h2 className="mb-4 text-sm text-roast-500 dark:text-roast-300">категории</h2>
      {data.length === 0 ? (
        <p className="py-8 text-sm text-roast-400">нет данных</p>
      ) : (
        <ul className="space-y-3">
          {data.map((item) => {
            const width = Math.max(6, Math.round((item.amount / max) * 100));
            return (
              <li key={item.category}>
                <div className="mb-1 flex items-center justify-between gap-3 text-sm">
                  <span className="text-roast-800 dark:text-foam-100">{item.category}</span>
                  <span className="tabular-nums text-roast-500 dark:text-roast-300">
                    {formatMoney(item.amount, null)}
                  </span>
                </div>
                <div className="h-1 overflow-hidden rounded-full bg-foam-200 dark:bg-roast-800">
                  <div
                    className="h-full rounded-full bg-cocoa-600 dark:bg-cocoa-400"
                    style={{ width: `${width}%` }}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
