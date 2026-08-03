import { AuthImage } from "@/components/AuthImage";
import { StatusBadge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { formatDate, formatMoney } from "@/lib/format";
import { ReceiptDocument } from "@/types/document";

interface Props {
  documents: ReceiptDocument[];
  onEdit: (id: number) => void;
  onDelete: (id: number) => void;
  deletingId?: number | null;
}

export function DocumentList({ documents, onEdit, onDelete, deletingId = null }: Props) {
  if (documents.length === 0) {
    return <p className="py-12 text-center text-sm text-roast-400">ничего не найдено</p>;
  }

  return (
    <>
      <div className="hidden md:block">
        <table className="w-full text-sm">
          <thead className="text-left text-roast-500 dark:text-roast-300">
            <tr className="border-b border-roast-200/70 dark:border-roast-800">
              <th className="pb-3 pr-4 font-normal">чек</th>
              <th className="pb-3 pr-4 font-normal">продавец</th>
              <th className="pb-3 pr-4 font-normal">дата</th>
              <th className="pb-3 pr-4 font-normal">категория</th>
              <th className="pb-3 pr-4 text-right font-normal">сумма</th>
              <th className="pb-3 pr-4 font-normal">статус</th>
              <th className="pb-3" />
            </tr>
          </thead>
          <tbody className="divide-y divide-roast-200/60 dark:divide-roast-800">
            {documents.map((document) => (
              <tr key={document.id}>
                <td className="py-3 pr-4">
                  <AuthImage
                    documentId={document.id}
                    alt="чек"
                    className="h-9 w-9 rounded-lg object-cover"
                  />
                </td>
                <td className="py-3 pr-4 text-roast-950 dark:text-foam-50">
                  {document.receipt?.merchantName ?? "—"}
                </td>
                <td className="py-3 pr-4 text-roast-500 dark:text-roast-300">
                  {formatDate(document.receipt?.purchaseDate ?? null)}
                </td>
                <td className="py-3 pr-4 text-roast-500 dark:text-roast-300">
                  {document.receipt?.category ?? "—"}
                </td>
                <td className="py-3 pr-4 text-right tabular-nums text-roast-950 dark:text-foam-50">
                  {formatMoney(
                    document.receipt?.amount ?? null,
                    document.receipt?.currency ?? null,
                  )}
                </td>
                <td className="py-3 pr-4">
                  <div className="flex flex-col gap-0.5">
                    <StatusBadge status={document.status} />
                    {document.lowQualityScan && (
                      <span className="text-[11px] text-amber-700 dark:text-amber-300">
                        нечёткий
                      </span>
                    )}
                    {document.receipt?.needsManualReview && (
                      <span className="text-[11px] text-rose-700 dark:text-rose-300">
                        проверить
                      </span>
                    )}
                  </div>
                </td>
                <td className="py-3 text-right">
                  <div className="flex justify-end gap-1">
                    <Button variant="ghost" onClick={() => onEdit(document.id)}>
                      править
                    </Button>
                    <Button
                      variant="ghost"
                      className="text-rose-700 dark:text-rose-300"
                      disabled={deletingId === document.id}
                      onClick={() => onDelete(document.id)}
                    >
                      {deletingId === document.id ? "…" : "удалить"}
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <ul className="divide-y divide-roast-200/70 md:hidden dark:divide-roast-800">
        {documents.map((document) => (
          <li key={document.id} className="space-y-2 py-4">
            <div className="flex items-center gap-3">
              <AuthImage
                documentId={document.id}
                alt="чек"
                className="h-10 w-10 rounded-lg object-cover"
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm text-roast-950 dark:text-foam-50">
                  {document.receipt?.merchantName ?? "—"}
                </p>
                <p className="text-xs text-roast-500 dark:text-roast-400">
                  {formatDate(document.receipt?.purchaseDate ?? null)} ·{" "}
                  {document.receipt?.category ?? "без категории"}
                </p>
              </div>
              <StatusBadge status={document.status} />
            </div>
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm tabular-nums text-roast-950 dark:text-foam-50">
                {formatMoney(
                  document.receipt?.amount ?? null,
                  document.receipt?.currency ?? null,
                )}
              </p>
              <div className="flex gap-1">
                <Button variant="ghost" onClick={() => onEdit(document.id)}>
                  править
                </Button>
                <Button
                  variant="ghost"
                  className="text-rose-700 dark:text-rose-300"
                  disabled={deletingId === document.id}
                  onClick={() => onDelete(document.id)}
                >
                  {deletingId === document.id ? "…" : "удалить"}
                </Button>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </>
  );
}
