import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { Listing } from "@/components/catalog/Listing";
import { Link } from "@/i18n/navigation";
import { getModel, listProducts } from "@/lib/api";
import { readCarCookie } from "@/lib/car-cookie";
import { listingQuery, pickListingParams } from "@/lib/listing-params";
import { listingSeo, seoMetadata } from "@/lib/seo";

export async function generateMetadata({ params, searchParams }: PageProps<"/[locale]/cars/[make]/[model]">): Promise<Metadata> {
  const { make, model } = await params;
  const data = await getModel(make, model);
  if (!data) return {};
  const path = `/cars/${data.make.slug}/${data.slug}`;
  return {
    ...seoMetadata(`Запчастини ${data.make.name} ${data.name}`, `Кузовні запчастини для ${data.make.name} ${data.name}. Оберіть покоління та роки випуску, перегляньте сумісні деталі з доставкою по Україні.`, path),
    ...listingSeo(path, await searchParams),
  };
}

export default async function ModelPage({ params, searchParams }: PageProps<"/[locale]/cars/[make]/[model]">) {
  const { locale, make, model } = await params;
  setRequestLocale(locale);
  const sp = await searchParams;
  await readCarCookie();
  const [data, t] = await Promise.all([getModel(make, model), getTranslations()]);
  if (!data) notFound();
  const listing = await listProducts(listingQuery(sp, { make, model }, null));

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs
        items={[
          { name: t("common.cars"), href: "/cars" },
          { name: data.make.name, href: `/cars/${make}` },
          { name: data.name, href: `/cars/${make}/${model}` },
        ]}
      />
      <h1 className="mt-4 font-display text-[28px] font-medium sm:text-[36px]">
        {data.make.name} <span className="text-gold">{data.name}</span>
      </h1>
      <div className="mt-5 mb-8 flex flex-wrap gap-2">
        {data.generations.map((g) => (
          <Link
            key={g.id}
            href={`/cars/${make}/${model}/${g.slug}`}
            className="rounded-[12px] bg-white px-4 py-2.5 text-[14px] font-semibold ring-1 ring-platinum-200 hover:ring-gold-400"
          >
            {g.years_label || "усі роки"} <span className="font-normal text-platinum-400">{g.product_count}</span>
          </Link>
        ))}
      </div>
      {listing && <Listing data={listing} path={`/cars/${make}/${model}`} searchParams={pickListingParams(sp)} showCategories={false} />}
    </div>
  );
}
