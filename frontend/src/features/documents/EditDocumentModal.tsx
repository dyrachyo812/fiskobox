import { useEffect, useState } from "react";

import { deleteDocument, getDocument, updateDocument } from "@/api/documents";
import { AuthImage } from "@/components/AuthImage";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { useCategories } from "@/hooks/useCategories";
import { DocumentDetail, DocumentUpdate } from "@/types/document";

interface Props {
  documentId: number | null;
  onClose: () => void;
  onSaved: () => void;
  onDeleted?: () => void;
}

const fieldClass = "field-input w-full";

export function EditDocumentModal({
  documentId,
  onClose,
  onSaved,
  onDeleted,
}: Props) {
  const [detail, setDetail] = useState<DocumentDetail | null>(null);
  const [form, setForm] = useState<DocumentUpdate>({});
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const categories = useCategories();

  useEffect(() => {
    if (documentId === null) {
      setDetail(null);
      return;
    }
    setDetail(null);
    getDocument(documentId)
      .then((loaded) => {
        setDetail(loaded);
        setForm({
          amount: loaded.receipt?.amount ?? null,
          currency: loaded.receipt?.currency ?? null,
          merchantName: loaded.receipt?.merchantName ?? null,
          purchaseDate: loaded.receipt?.purchaseDate ?? null,
          category: loaded.receipt?.category ?? null,
        });
      })
      .catch(() => undefined);
  }, [documentId]);

  const save = async () => {
    if (documentId === null) {
      return;
    }
    setSaving(true);
    try {
      await updateDocument(documentId, form);
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (documentId === null) {
      return;
    }
    if (!window.confirm("удалить этот чек?")) {
      return;
    }
    setDeleting(true);
    try {
      await deleteDocument(documentId);
      (onDeleted ?? onSaved)();
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Modal open={documentId !== null} title="чек" onClose={onClose}>
      {!detail ? (
        <div className="flex justify-center py-10">
          <Spinner />
        </div>
      ) : (
        <div className="space-y-4">
          <AuthImage
            documentId={detail.id}
            alt="чек"
            className="max-h-56 w-full rounded-xl bg-foam-100 object-contain dark:bg-roast-950"
          />
          {detail.lowQualityScan && (
            <p className="text-sm text-amber-700 dark:text-amber-300">
              нечёткий скан
              {detail.sharpnessScore != null
                ? ` · резкость ${detail.sharpnessScore.toFixed(0)}`
                : ""}
            </p>
          )}
          {detail.receipt?.needsManualReview && (
            <p className="text-sm text-rose-700 dark:text-rose-300">нужна проверка полей</p>
          )}
          <div className="grid grid-cols-2 gap-3">
            <label className="space-y-1">
              <span className="text-xs text-roast-500 dark:text-roast-400">продавец</span>
              <input
                className={fieldClass}
                value={form.merchantName ?? ""}
                onChange={(event) =>
                  setForm({ ...form, merchantName: event.target.value })
                }
              />
            </label>
            <label className="space-y-1">
              <span className="text-xs text-roast-500 dark:text-roast-400">категория</span>
              <select
                className={fieldClass}
                value={form.category ?? ""}
                onChange={(event) =>
                  setForm({
                    ...form,
                    category: event.target.value === "" ? null : event.target.value,
                  })
                }
              >
                <option value="">не определена</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.name}>
                    {category.name}
                  </option>
                ))}
                {form.category &&
                  !categories.some((category) => category.name === form.category) && (
                    <option value={form.category}>{form.category}</option>
                  )}
              </select>
            </label>
            <label className="space-y-1">
              <span className="text-xs text-roast-500 dark:text-roast-400">сумма</span>
              <input
                className={fieldClass}
                type="number"
                step="0.01"
                value={form.amount ?? ""}
                onChange={(event) =>
                  setForm({
                    ...form,
                    amount: event.target.value === "" ? null : Number(event.target.value),
                  })
                }
              />
            </label>
            <label className="space-y-1">
              <span className="text-xs text-roast-500 dark:text-roast-400">валюта</span>
              <input
                className={fieldClass}
                value={form.currency ?? ""}
                onChange={(event) => setForm({ ...form, currency: event.target.value })}
              />
            </label>
            <label className="col-span-2 space-y-1">
              <span className="text-xs text-roast-500 dark:text-roast-400">дата</span>
              <input
                className={fieldClass}
                type="date"
                value={form.purchaseDate ?? ""}
                onChange={(event) =>
                  setForm({ ...form, purchaseDate: event.target.value || null })
                }
              />
            </label>
          </div>
          {detail.rawOcrText && (
            <details className="text-xs text-roast-500 dark:text-roast-400">
              <summary className="cursor-pointer">ocr</summary>
              <pre className="mt-2 whitespace-pre-wrap">{detail.rawOcrText}</pre>
            </details>
          )}
          {detail.receipt && (
            <details className="text-xs text-roast-500 dark:text-roast-400">
              <summary className="cursor-pointer">отладка</summary>
              <ul className="mt-2 space-y-1">
                <li>amount_matched_by: {detail.receipt.amountMatchedBy ?? "—"}</li>
                <li>date_matched_by: {detail.receipt.dateMatchedBy ?? "—"}</li>
                <li>merchant_matched_by: {detail.receipt.merchantMatchedBy ?? "—"}</li>
              </ul>
            </details>
          )}
          <div className="flex items-center justify-between gap-2">
            <Button variant="danger" onClick={remove} disabled={deleting || saving}>
              {deleting ? "…" : "удалить"}
            </Button>
            <div className="flex gap-2">
              <Button variant="ghost" onClick={onClose}>
                отмена
              </Button>
              <Button onClick={save} disabled={saving || deleting}>
                {saving ? "…" : "сохранить"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </Modal>
  );
}
