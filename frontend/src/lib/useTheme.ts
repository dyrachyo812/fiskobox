import { useContext } from "react";

import { ThemeContext, ThemeContextValue } from "@/lib/themeContextValue";

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}
