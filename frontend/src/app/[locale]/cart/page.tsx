import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { CartView } from "@/components/cart/CartView";
import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";

export const metadata: Metadata = { title: "Кошик", robots: { index: false } };

export default async function CartPage({ params }: PageProps<"/[locale]/cart">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("cart");
  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs items={[{ name: t("title") }]} />
      <h1 className="mt-4 mb-6 font-display text-[30px] font-medium sm:text-[38px]">{t("title")}</h1>
      <CartView />
    </div>
  );
}
