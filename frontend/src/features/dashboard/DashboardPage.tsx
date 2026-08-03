import { useState } from "react";

import { Spinner } from "@/components/ui/Spinner";
import { CategoryChart } from "@/features/dashboard/CategoryChart";
import { RecentDocuments } from "@/features/dashboard/RecentDocuments";
import { SummaryCards } from "@/features/dashboard/SummaryCards";
import { EditDocumentModal } from "@/features/documents/EditDocumentModal";
import { useDocuments } from "@/hooks/useDocuments";
import { useSummary } from "@/hooks/useSummary";

export function DashboardPage() {
  const { data: summary, loading } = useSummary("all");
  const { data: documents, reload } = useDocuments({ limit: 5, offset: 0 });
  const [editId, setEditId] = useState<number | null>(null);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-medium tracking-tight">обзор</h1>

      {loading || !summary ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : (
        <>
          <SummaryCards summary={summary} />
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            <CategoryChart summary={summary} />
            <RecentDocuments documents={documents?.items ?? []} onOpen={setEditId} />
          </div>
        </>
      )}

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
