import { defineRouting } from "next-intl/routing";

// Only Ukrainian for V1. Add a locale here (and messages/<locale>.json) to enable it —
// URLs for the default locale stay prefix-free.
export const routing = defineRouting({
  locales: ["uk"],
  defaultLocale: "uk",
  localePrefix: "as-needed",
});

export type Locale = (typeof routing.locales)[number];
