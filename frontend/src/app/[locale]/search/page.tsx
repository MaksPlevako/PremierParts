import type { Metadata } from "next";
import { Car, Sparkles } from "lucide-react";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { Listing } from "@/components/catalog/Listing";
import { SearchBox } from "@/components/search/SearchBox";
import { SetMyCarButton } from "@/components/car/SetMyCarButton";
import { searchProducts } from "@/lib/api";
import { readCarCookie } from "@/lib/car-cookie";
import { listingQuery, pickListingParams } from "@/lib/listing-params";
import type { CarRef } from "@/lib/types";

export async function generateMetadata({ searchParams }: PageProps<"/[locale]/search">): Promise<Metadata> {
  const sp = await searchParams;
  const q = typeof sp.q === "string" ? sp.q : "";
  return { title: q ? `«${q}» — пошук запчастин` : "Пошук запчастин", robots: { index: false, follow: true } };
}

export default async function SearchPage({ params, searchParams }: PageProps<"/[locale]/search">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const sp = await searchParams;
  const q = typeof sp.q === "string" ? sp.q.trim() : "";
  const car = await readCarCookie();
  const [data, t] = await Promise.all([q ? searchProducts(listingQuery(sp, {}, car)) : null, getTranslations()]);
  const understood = data?.understood;
  const vinCar = data?.car_source === "vin" ? (data.car as CarRef) : null;
  const picked = pickListingParams(sp);

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs items={[{ name: t("search.searchTitle") }]} />
      <div className="mt-4 mb-6 flex flex-col gap-4">
        <h1 className="font-display text-[26px] leading-tight font-medium sm:text-[32px]">
          {q ? t("search.resultsFor", { q }) : t("search.searchTitle")}
        </h1>
        <div className="max-w-3xl">
          <SearchBox size="hero" initialQuery={q} />
        </div>
        {understood && (understood.category || understood.car) && (
          <div className="flex flex-wrap items-center gap-2 text-[13.5px] text-platinum-600">
            <Sparkles className="size-4 text-gold-600" />
            {t("search.understood")}
            {understood.category && (
              <span className="rounded-[9px] bg-gold-100 px-2.5 py-1 font-semibold text-gold-800">{understood.category.name}</span>
            )}
            {understood.car && (
              <span className="inline-flex items-center gap-1.5 rounded-[9px] bg-ink px-2.5 py-1 font-semibold text-white">
                <Car className="size-3.5" />
                {("full_label" in understood.car && understood.car.full_label) || `${understood.car.make} ${understood.car.label}`}
              </span>
            )}
          </div>
        )}
        {vinCar && (
          <div className="flex flex-wrap items-center gap-4 rounded-[18px] bg-lux p-5 text-white">
            <Car className="size-6 text-gold-300" />
            <div className="flex-1">
              <p className="text-[12px] text-platinum-300">VIN {data?.vin?.vin}</p>
              <p className="font-display text-[18px] font-medium">{vinCar.full_label}</p>
            </div>
            <SetMyCarButton car={vinCar} />
          </div>
        )}
      </div>
      {data && (
        <Listing
          data={data}
          path="/search"
          searchParams={picked}
          categoryHrefPrefix={`/search?q=${encodeURIComponent(q)}&category=`}
        />
      )}
    </div>
  );
}
