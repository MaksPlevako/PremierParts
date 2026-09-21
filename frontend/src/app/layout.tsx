import type { ReactNode } from "react";

import "./globals.css";

// The real <html> lives in app/[locale]/layout.tsx (next-intl). This root layout only exists so
// that app-level files such as not-found.tsx have a parent.
export default function RootLayout({ children }: { children: ReactNode }) {
  return children;
}
