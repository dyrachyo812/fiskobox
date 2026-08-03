import { MouseEvent, ReactNode } from "react";

interface ModalProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

export function Modal({ open, title, onClose, children }: ModalProps) {
  if (!open) {
    return null;
  }

  const stop = (event: MouseEvent) => event.stopPropagation();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-roast-950/40 p-4"
      onClick={onClose}
    >
      <div className="surface max-h-[90vh] w-full max-w-lg overflow-y-auto p-5" onClick={stop}>
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-base font-medium text-roast-950 dark:text-foam-50">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-sm text-roast-400 transition hover:text-roast-700 dark:hover:text-foam-100"
            aria-label="Закрыть"
          >
            закрыть
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
