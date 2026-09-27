import type { Metadata } from "next";

import { AuthScreen } from "@/components/account/AuthScreen";

export const metadata: Metadata = { title: "Вхід і реєстрація | Premier Parts", robots: { index: false } };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const query = await searchParams;
  return <AuthScreen oauthError={query.error === "oauth"} />;
}
