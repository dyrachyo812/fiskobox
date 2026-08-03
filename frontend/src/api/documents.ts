import { apiClient } from "@/api/client";
import {
  DocumentDetail,
  DocumentListResult,
  DocumentUpdate,
  Receipt,
  ReceiptDocument,
} from "@/types/document";

interface RawReceipt {
  amount: number | string | null;
  currency: string | null;
  merchant_name: string | null;
  purchase_date: string | null;
  category: string | null;
  is_manually_corrected: boolean;
  amount_matched_by: string | null;
  date_matched_by: string | null;
  merchant_matched_by: string | null;
  needs_manual_review: boolean;
}

interface RawDocument {
  id: number;
  status: ReceiptDocument["status"];
  created_at: string;
  receipt: RawReceipt | null;
  low_quality_scan: boolean;
}

interface RawDetail extends RawDocument {
  raw_ocr_text: string | null;
  image_url: string;
  sharpness_score: number | null;
}

interface RawList {
  items: RawDocument[];
  total: number;
  limit: number;
  offset: number;
}

function toReceipt(raw: RawReceipt | null): Receipt | null {
  if (!raw) {
    return null;
  }
  return {
    amount: raw.amount === null ? null : Number(raw.amount),
    currency: raw.currency,
    merchantName: raw.merchant_name,
    purchaseDate: raw.purchase_date,
    category: raw.category,
    isManuallyCorrected: raw.is_manually_corrected,
    amountMatchedBy: raw.amount_matched_by ?? null,
    dateMatchedBy: raw.date_matched_by ?? null,
    merchantMatchedBy: raw.merchant_matched_by ?? null,
    needsManualReview: Boolean(raw.needs_manual_review),
  };
}

function toDocument(raw: RawDocument): ReceiptDocument {
  return {
    id: raw.id,
    status: raw.status,
    createdAt: raw.created_at,
    receipt: toReceipt(raw.receipt),
    lowQualityScan: Boolean(raw.low_quality_scan),
  };
}

function toDetail(raw: RawDetail): DocumentDetail {
  return {
    ...toDocument(raw),
    rawOcrText: raw.raw_ocr_text,
    imageUrl: raw.image_url,
    sharpnessScore: raw.sharpness_score,
  };
}

export interface DocumentQuery {
  limit: number;
  offset: number;
  status?: string;
  category?: string;
  dateFrom?: string;
  dateTo?: string;
}

export async function listDocuments(query: DocumentQuery): Promise<DocumentListResult> {
  const params: Record<string, string | number> = {
    limit: query.limit,
    offset: query.offset,
  };
  if (query.status) {
    params["status"] = query.status;
  }
  if (query.category) {
    params["category"] = query.category;
  }
  if (query.dateFrom) {
    params["date_from"] = query.dateFrom;
  }
  if (query.dateTo) {
    params["date_to"] = query.dateTo;
  }

  const { data } = await apiClient.get<RawList>("/documents", { params });
  return {
    items: data.items.map(toDocument),
    total: data.total,
    limit: data.limit,
    offset: data.offset,
  };
}

export async function getDocument(id: number): Promise<DocumentDetail> {
  const { data } = await apiClient.get<RawDetail>(`/documents/${id}`);
  return toDetail(data);
}

export async function updateDocument(
  id: number,
  update: DocumentUpdate,
): Promise<DocumentDetail> {
  const body: Record<string, unknown> = {};
  if (update.amount !== undefined) {
    body["amount"] = update.amount;
  }
  if (update.currency !== undefined) {
    body["currency"] = update.currency;
  }
  if (update.merchantName !== undefined) {
    body["merchant_name"] = update.merchantName;
  }
  if (update.purchaseDate !== undefined) {
    body["purchase_date"] = update.purchaseDate;
  }
  if (update.category !== undefined) {
    body["category"] = update.category;
  }

  const { data } = await apiClient.patch<RawDetail>(`/documents/${id}`, body);
  return toDetail(data);
}

export async function getImageObjectUrl(id: number): Promise<string> {
  const { data } = await apiClient.get<Blob>(`/documents/${id}/image`, {
    responseType: "blob",
  });
  return URL.createObjectURL(data);
}

export async function deleteDocument(id: number): Promise<void> {
  await apiClient.delete(`/documents/${id}`);
}
