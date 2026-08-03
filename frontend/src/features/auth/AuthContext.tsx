import { ReactNode, useCallback, useState } from "react";

import { linkTelegram } from "@/api/auth";
import { AuthContext } from "@/features/auth/authContextValue";
import { clearToken, getToken, setToken } from "@/lib/token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setTokenState] = useState<string | null>(() => getToken());

  const login = useCallback(async (code: string) => {
    const accessToken = await linkTelegram(code);
    setToken(accessToken);
    setTokenState(accessToken);
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated: token !== null, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
