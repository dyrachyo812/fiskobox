import { useContext } from "react";

import { AuthContext, AuthContextValue } from "@/features/auth/authContextValue";

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
