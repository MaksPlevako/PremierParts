import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { CheckoutForm } from "@/components/checkout/CheckoutForm";

export const metadata: Metadata = { title: "Оформлення замовлення", robots: { index: false } };

export default async function CheckoutPage({ params }: PageProps<"/[locale]/checkout">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations();
  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs items={[{ name: t("cart.title"), href: "/cart" }, { name: t("checkout.title") }]} />
      <h1 className="mt-4 mb-6 font-display text-[30px] font-medium sm:text-[38px]">{t("checkout.title")}</h1>
      <CheckoutForm />
    </div>
  );
}
