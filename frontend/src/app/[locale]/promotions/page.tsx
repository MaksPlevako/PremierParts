import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { Link } from "@/i18n/navigation";
import { getPromotions } from "@/lib/api";
import { readCarCookie } from "@/lib/car-cookie";

export const metadata: Metadata = { title: "Акції та знижки", alternates: { canonical: "/promotions" } };

const dateFmt = new Intl.DateTimeFormat("uk-UA", { day: "numeric", month: "long" });

export default async function PromotionsPage({ params }: PageProps<"/[locale]/promotions">) {
  const { locale } = await params;
  setRequestLocale(locale);
  await readCarCookie();
  const [promos, t] = await Promise.all([getPromotions(), getTranslations()]);

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs items={[{ name: t("common.promotions") }]} />
      <h1 className="mt-4 font-display text-[30px] font-medium sm:text-[38px]">{t("home.promotions")}</h1>
      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(promos ?? []).map((p, i) => (
          <Link
            key={p.id}
            href={`/promotions/${p.slug}`}
            className={`group relative flex min-h-[220px] flex-col justify-between overflow-hidden rounded-[24px] p-7 transition ${
              i === 0 ? "bg-lux text-white" : "bg-white ring-1 ring-platinum-200 hover:ring-gold-400"
            }`}
          >
            <span className="font-display text-[56px] leading-none font-medium text-gold">−{p.discount_percent}%</span>
            <div>
              <p className="font-display text-[20px] font-medium">{p.title}</p>
              <p className={`mt-1 text-[14px] ${i === 0 ? "text-platinum-300" : "text-platinum-600"}`}>{p.description}</p>
              {p.ends_at && (
                <p className={`mt-3 text-[12px] font-semibold ${i === 0 ? "text-gold-300" : "text-gold-700"}`}>
                  до {dateFmt.format(new Date(p.ends_at))}
                </p>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
