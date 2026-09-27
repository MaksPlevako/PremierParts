import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { SetMyCarButton } from "@/components/car/SetMyCarButton";
import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { Listing } from "@/components/catalog/Listing";
import { Link } from "@/i18n/navigation";
import { getCar, listProducts } from "@/lib/api";
import { readCarCookie } from "@/lib/car-cookie";
import { cn } from "@/lib/format";
import { listingQuery, pickListingParams } from "@/lib/listing-params";
import { listingSeo, seoMetadata } from "@/lib/seo";

type Props = PageProps<"/[locale]/cars/[make]/[model]/[generation]">;

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { make, model, generation } = await params;
  const car = await getCar(make, model, generation);
  if (!car) return {};
  const path = `/cars/${car.make_slug}/${car.model_slug}/${car.generation_slug}`;
  return {
    ...seoMetadata(`Запчастини для ${car.full_label}`, `Фари, ліхтарі, бампери, крила, радіатори та скло для ${car.full_label}. Перевірена сумісність, доставка по Україні.`, path),
    ...listingSeo(path, await searchParams),
  };
}

export default async function GenerationPage({ params, searchParams }: Props) {
  const { locale, make, model, generation } = await params;
  setRequestLocale(locale);
  const sp = await searchParams;
  await readCarCookie();
  const [car, t] = await Promise.all([getCar(make, model, generation), getTranslations()]);
  if (!car) notFound();
  const category = typeof sp.category === "string" ? sp.category : undefined;
  const listing = await listProducts(listingQuery(sp, { generation: car.generation_id, category }, null));
  const path = `/cars/${make}/${model}/${generation}`;

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs
        items={[
          { name: t("common.cars"), href: "/cars" },
          { name: car.make, href: `/cars/${make}` },
          { name: car.model, href: `/cars/${make}/${model}` },
          { name: car.years_label || "усі роки", href: path },
        ]}
      />
      <div className="mt-4 mb-6 flex flex-col gap-5 rounded-[26px] bg-lux p-6 text-white sm:flex-row sm:items-center sm:p-8">
        <div className="flex-1">
          <p className="text-[11px] font-bold tracking-[0.24em] text-gold-300">ЗАПЧАСТИНИ ДЛЯ</p>
          <h1 className="mt-2 font-display text-[26px] leading-tight font-medium sm:text-[34px]">{car.full_label}</h1>
          <p className="mt-2 text-[14px] text-platinum-300">{t("common.parts", { count: listing?.count ?? 0 })} з перевіреною сумісністю</p>
        </div>
        <SetMyCarButton car={car} />
      </div>
      {car.categories.length > 0 && (
        <div className="-mx-4 mb-6 flex gap-2 overflow-x-auto px-4 pb-1 scrollbar-none sm:mx-0 sm:flex-wrap sm:px-0">
          <Link
            href={path}
            className={cn(
              "shrink-0 rounded-[12px] px-3.5 py-2 text-[13.5px] font-semibold ring-1",
              !category ? "bg-ink text-white ring-ink" : "bg-white ring-platinum-200 hover:ring-gold-400",
            )}
          >
            Усі
          </Link>
          {car.categories.map((c) => (
            <Link
              key={c.id}
              href={`${path}?category=${c.slug}`}
              className={cn(
                "shrink-0 rounded-[12px] px-3.5 py-2 text-[13.5px] font-semibold ring-1",
                category === c.slug ? "bg-ink text-white ring-ink" : "bg-white ring-platinum-200 hover:ring-gold-400",
              )}
            >
              {c.name} <span className="font-normal opacity-60">{c.count}</span>
            </Link>
          ))}
        </div>
      )}
      {listing && <Listing data={listing} path={path} searchParams={pickListingParams(sp)} showCategories={false} />}
    </div>
  );
}
