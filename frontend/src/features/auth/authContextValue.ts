import { createContext } from "react";

export interface AuthContextValue {
  isAuthenticated: boolean;
  login: (code: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);
