import { apiClient } from "@/api/client";

interface TokenResponse {
  access_token: string;
}

export async function linkTelegram(code: string): Promise<string> {
  const { data } = await apiClient.post<TokenResponse>("/auth/link-telegram", { code });
  return data.access_token;
}
