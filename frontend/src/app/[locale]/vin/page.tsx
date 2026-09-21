import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { VinTool } from "@/components/vin/VinTool";

export const metadata: Metadata = {
  title: "Підбір запчастин за VIN-кодом",
  description: "Введіть VIN — визначимо марку, модель і рік випуску та покажемо лише сумісні кузовні деталі. Або надішліть запит менеджеру.",
  alternates: { canonical: "/vin" },
};

export default async function VinPage({ params, searchParams }: PageProps<"/[locale]/vin">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const { vin } = await searchParams;
  const t = await getTranslations("vin");
  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs items={[{ name: "VIN" }]} />
      <h1 className="mt-4 font-display text-[30px] font-medium sm:text-[38px]">{t("title")}</h1>
      <p className="mt-2 mb-8 max-w-2xl text-[15px] text-platinum-600">{t("subtitle")}</p>
      <VinTool initialVin={typeof vin === "string" ? vin : ""} />
    </div>
  );
}
