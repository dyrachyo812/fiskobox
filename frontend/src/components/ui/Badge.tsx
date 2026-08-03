import { DocumentStatus } from "@/types/document";

const labels: Record<DocumentStatus, string> = {
  pending: "очередь",
  processing: "обработка",
  done: "готово",
  failed: "ошибка",
};

const styles: Record<DocumentStatus, string> = {
  pending: "text-roast-500 dark:text-roast-300",
  processing: "text-amber-700 dark:text-amber-300",
  done: "text-cocoa-700 dark:text-cocoa-300",
  failed: "text-rose-700 dark:text-rose-300",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span className={`text-xs font-medium ${styles[status]}`}>{labels[status]}</span>
  );
}
