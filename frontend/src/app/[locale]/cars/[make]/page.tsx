import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { Link } from "@/i18n/navigation";
import { getMake } from "@/lib/api";
import { readCarCookie } from "@/lib/car-cookie";
import { cn } from "@/lib/format";

export async function generateMetadata({ params }: PageProps<"/[locale]/cars/[make]">): Promise<Metadata> {
  const { make } = await params;
  const data = await getMake(make);
  if (!data) return {};
  return {
    title: `Запчастини ${data.name} — фари, бампери, радіатори`,
    description: `Кузовні запчастини для ${data.name}: оптика, кузов, радіатори, скло та дзеркала. Підбір за моделлю, роками та VIN.`,
    alternates: { canonical: `/cars/${data.slug}` },
  };
}

export default async function MakePage({ params }: PageProps<"/[locale]/cars/[make]">) {
  const { locale, make } = await params;
  setRequestLocale(locale);
  await readCarCookie();
  const [data, t] = await Promise.all([getMake(make), getTranslations()]);
  if (!data) notFound();

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs items={[{ name: t("common.cars"), href: "/cars" }, { name: data.name, href: `/cars/${data.slug}` }]} />
      <h1 className="mt-4 font-display text-[30px] font-medium sm:text-[38px]">
        Запчастини <span className="text-gold">{data.name}</span>
      </h1>
      <p className="mt-2 text-[15px] text-platinum-600">Оберіть модель і роки випуску.</p>

      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.families.map((fam) => (
          <section key={fam.family} className="rounded-[22px] bg-white p-5 ring-1 ring-platinum-200">
            <h2 className="mb-3 font-display text-[18px] font-medium">{fam.family}</h2>
            <ul className="flex flex-col gap-2">
              {fam.models.map((m) => (
                <li key={m.id} className="rounded-[14px] bg-platinum-50 p-3">
                  <div className="mb-2 flex items-center justify-between">
                    <Link href={`/cars/${data.slug}/${m.slug}`} className="font-semibold hover:text-gold-800">
                      {m.name}
                    </Link>
                    <span className="text-[12px] text-platinum-500">{m.product_count ? t("common.parts", { count: m.product_count }) : ""}</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {m.generations.map((g) => (
                      <Link
                        key={g.id}
                        href={`/cars/${data.slug}/${m.slug}/${g.slug}`}
                        className={cn(
                          "rounded-[9px] px-2.5 py-1 text-[12.5px] font-semibold ring-1 transition",
                          g.product_count ? "bg-white ring-platinum-200 hover:ring-gold-400" : "text-platinum-400 ring-platinum-100",
                        )}
                      >
                        {g.years_label || "усі роки"}
                        {g.product_count > 0 && <span className="ml-1 font-normal text-platinum-400">{g.product_count}</span>}
                      </Link>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}
