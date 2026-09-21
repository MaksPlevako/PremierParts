import type { Metadata, Viewport } from "next";
import { Onest, Unbounded } from "next/font/google";
import { notFound } from "next/navigation";
import { connection } from "next/server";
import { hasLocale, NextIntlClientProvider } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { MyCarPicker } from "@/components/car/MyCarPicker";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { Toaster } from "@/components/ui/Toaster";
import { getCategories, getSettingsSafe } from "@/lib/api";
import { siteUrl } from "@/lib/seo";
import { routing } from "@/i18n/routing";

const onest = Onest({ subsets: ["latin", "cyrillic"], variable: "--font-onest", display: "swap" });
const unbounded = Unbounded({
  subsets: ["latin", "cyrillic"],
  variable: "--font-unbounded",
  weight: ["400", "500", "600"],
  display: "swap",
});

export const viewport: Viewport = {
  themeColor: "#15181C",
  width: "device-width",
  initialScale: 1,
};

export async function generateMetadata({ params }: LayoutProps<"/[locale]">): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "meta" });
  const settings = await getSettingsSafe();
  const title = settings?.seo_title || t("defaultTitle");
  const description = settings?.seo_description || t("defaultDescription");
  return {
    metadataBase: new URL(siteUrl()),
    title: { default: title, template: `%s | ${t("siteName")}` },
    description,
    applicationName: t("siteName"),
    openGraph: { type: "website", siteName: t("siteName"), locale: "uk_UA", title, description },
    twitter: { card: "summary_large_image" },
    alternates: { canonical: "/" },
    formatDetection: { telephone: true },
  };
}

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({ children, params }: LayoutProps<"/[locale]">) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();
  setRequestLocale(locale);
  // Every page renders at request time (data itself is cached per tag), so a Docker build never needs the API.
  await connection();

  const [settings, categories] = await Promise.all([getSettingsSafe(), getCategories().catch(() => null)]);

  return (
    <html lang={locale} className={`${onest.variable} ${unbounded.variable}`} data-scroll-behavior="smooth">
      <body className="flex min-h-dvh flex-col">
        <NextIntlClientProvider>
          <Header settings={settings} categories={categories ?? []} />
          <main className="flex-1">{children}</main>
          <Footer settings={settings} categories={categories ?? []} />
          <MyCarPicker />
          <Toaster />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
