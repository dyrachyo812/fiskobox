import { AuthImage } from "@/components/AuthImage";
import { StatusBadge } from "@/components/ui/Badge";
import { formatDate, formatMoney } from "@/lib/format";
import { ReceiptDocument } from "@/types/document";

interface Props {
  documents: ReceiptDocument[];
  onOpen: (id: number) => void;
}

export function RecentDocuments({ documents, onOpen }: Props) {
  return (
    <section>
      <h2 className="mb-4 text-sm text-roast-500 dark:text-roast-300">последние</h2>
      {documents.length === 0 ? (
        <p className="py-8 text-sm text-roast-400">пока пусто</p>
      ) : (
        <ul className="divide-y divide-roast-200/70 dark:divide-roast-800">
          {documents.map((document) => (
            <li key={document.id}>
              <button
                type="button"
                onClick={() => onOpen(document.id)}
                className="flex w-full items-center gap-3 py-3 text-left transition hover:opacity-80"
              >
                <AuthImage
                  documentId={document.id}
                  alt="чек"
                  className="h-10 w-10 rounded-lg object-cover"
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-roast-950 dark:text-foam-50">
                    {document.receipt?.merchantName ?? "без названия"}
                  </p>
                  <p className="text-xs text-roast-500 dark:text-roast-400">
                    {formatDate(document.receipt?.purchaseDate ?? document.createdAt)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm tabular-nums text-roast-950 dark:text-foam-50">
                    {formatMoney(
                      document.receipt?.amount ?? null,
                      document.receipt?.currency ?? null,
                    )}
                  </p>
                  <StatusBadge status={document.status} />
                </div>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
