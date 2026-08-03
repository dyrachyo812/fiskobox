import { useMemo, useState } from "react";

import { deleteDocument } from "@/api/documents";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { DocumentFilters, FilterState } from "@/features/documents/DocumentFilters";
import { DocumentList } from "@/features/documents/DocumentList";
import { EditDocumentModal } from "@/features/documents/EditDocumentModal";
import { useDocuments } from "@/hooks/useDocuments";

const pageSize = 10;

export function DocumentsPage() {
  const [filters, setFilters] = useState<FilterState>({
    status: "",
    category: "",
    dateFrom: "",
    dateTo: "",
  });
  const [page, setPage] = useState(0);
  const [editId, setEditId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const query = useMemo(
    () => ({
      limit: pageSize,
      offset: page * pageSize,
      status: filters.status || undefined,
      category: filters.category || undefined,
      dateFrom: filters.dateFrom || undefined,
      dateTo: filters.dateTo || undefined,
    }),
    [filters, page],
  );

  const { data, loading, reload } = useDocuments(query);
  const total = data?.total ?? 0;
  const maxPage = Math.max(0, Math.ceil(total / pageSize) - 1);

  const handleDelete = async (id: number) => {
    if (!window.confirm("удалить этот чек?")) {
      return;
    }
    setDeletingId(id);
    try {
      await deleteDocument(id);
      if (editId === id) {
        setEditId(null);
      }
      reload();
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-medium tracking-tight">чеки</h1>

      <DocumentFilters
        value={filters}
        onChange={(next) => {
          setPage(0);
          setFilters(next);
        }}
      />

      {loading ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : (
        <DocumentList
          documents={data?.items ?? []}
          onEdit={setEditId}
          onDelete={handleDelete}
          deletingId={deletingId}
        />
      )}

      <div className="flex items-center justify-between gap-3 text-sm text-roast-500 dark:text-roast-400">
        <p>{total}</p>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            disabled={page <= 0}
            onClick={() => setPage((current) => Math.max(0, current - 1))}
          >
            назад
          </Button>
          <span>
            {page + 1} / {maxPage + 1}
          </span>
          <Button
            variant="ghost"
            disabled={page >= maxPage}
            onClick={() => setPage((current) => Math.min(maxPage, current + 1))}
          >
            дальше
          </Button>
        </div>
      </div>

      <EditDocumentModal
        documentId={editId}
        onClose={() => setEditId(null)}
        onSaved={() => {
          setEditId(null);
          reload();
        }}
        onDeleted={() => {
          setEditId(null);
          reload();
        }}
      />
    </div>
  );
}
