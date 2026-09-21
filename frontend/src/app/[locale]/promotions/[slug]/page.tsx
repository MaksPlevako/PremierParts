import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { Listing } from "@/components/catalog/Listing";
import { getPromotion, listProducts } from "@/lib/api";
import { readCarCookie } from "@/lib/car-cookie";
import { listingQuery, pickListingParams } from "@/lib/listing-params";

export async function generateMetadata({ params }: PageProps<"/[locale]/promotions/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const promo = await getPromotion(slug);
  return promo ? { title: promo.title, description: promo.description, alternates: { canonical: `/promotions/${slug}` } } : {};
}

export default async function PromotionPage({ params, searchParams }: PageProps<"/[locale]/promotions/[slug]">) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const sp = await searchParams;
  const car = await readCarCookie();
  const [promo, t] = await Promise.all([getPromotion(slug), getTranslations()]);
  if (!promo) notFound();
  const listing = await listProducts(listingQuery(sp, { promo: slug }, car));

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs items={[{ name: t("common.promotions"), href: "/promotions" }, { name: promo.title, href: `/promotions/${slug}` }]} />
      <div className="mt-4 mb-8 flex flex-col gap-4 rounded-[26px] bg-lux p-7 text-white sm:flex-row sm:items-center sm:p-9">
        <span className="font-display text-[64px] leading-none font-medium text-gold">−{promo.discount_percent}%</span>
        <div>
          <h1 className="font-display text-[26px] font-medium sm:text-[32px]">{promo.title}</h1>
          <p className="mt-1 text-[15px] text-platinum-300">{promo.description}</p>
        </div>
      </div>
      {listing && <Listing data={listing} path={`/promotions/${slug}`} searchParams={pickListingParams(sp)} />}
    </div>
  );
}
