export type DocumentStatus = "pending" | "processing" | "done" | "failed";

export interface Receipt {
  amount: number | null;
  currency: string | null;
  merchantName: string | null;
  purchaseDate: string | null;
  category: string | null;
  isManuallyCorrected: boolean;
  amountMatchedBy: string | null;
  dateMatchedBy: string | null;
  merchantMatchedBy: string | null;
  needsManualReview: boolean;
}

export interface ReceiptDocument {
  id: number;
  status: DocumentStatus;
  createdAt: string;
  receipt: Receipt | null;
  lowQualityScan: boolean;
}

export interface DocumentDetail extends ReceiptDocument {
  rawOcrText: string | null;
  imageUrl: string;
  sharpnessScore: number | null;
}

export interface DocumentListResult {
  items: ReceiptDocument[];
  total: number;
  limit: number;
  offset: number;
}

export interface DocumentUpdate {
  amount?: number | null;
  currency?: string | null;
  merchantName?: string | null;
  purchaseDate?: string | null;
  category?: string | null;
}
