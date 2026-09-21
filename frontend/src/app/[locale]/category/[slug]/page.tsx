import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { BannerCard } from "@/components/catalog/BannerCard";
import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { CategoryIcon } from "@/components/catalog/CategoryIcon";
import { Listing } from "@/components/catalog/Listing";
import { Link } from "@/i18n/navigation";
import { getBanners, getCategory, listProducts } from "@/lib/api";
import { readCarCookie } from "@/lib/car-cookie";
import { cn } from "@/lib/format";
import { listingQuery, pickListingParams } from "@/lib/listing-params";

export async function generateMetadata({ params }: PageProps<"/[locale]/category/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const cat = await getCategory(slug);
  if (!cat) return {};
  const title = `${cat.name} — купити з доставкою по Україні`;
  return {
    title,
    description: `${cat.name}: ${cat.product_count} позицій для 50+ марок авто. Фото, OEM-номери, перевірка сумісності з вашим авто. Доставка Новою Поштою.`,
    alternates: { canonical: `/category/${cat.slug}` },
  };
}

export default async function CategoryPage({ params, searchParams }: PageProps<"/[locale]/category/[slug]">) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const sp = await searchParams;
  const car = await readCarCookie();
  const [category, t] = await Promise.all([getCategory(slug), getTranslations()]);
  if (!category) notFound();
  const [data, banners] = await Promise.all([
    listProducts(listingQuery(sp, { category: slug }, car)),
    getBanners("catalog_top").catch(() => null),
  ]);
  if (!data) notFound();

  const crumbs = [{ name: t("common.catalog"), href: "/catalog" }];
  if (category.parent) crumbs.push({ name: category.parent.name, href: `/category/${category.parent.slug}` });
  crumbs.push({ name: category.name, href: `/category/${category.slug}` });

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs items={crumbs} />
      <div className="mt-4 mb-6 flex items-center gap-4">
        <span className="hidden size-14 place-items-center rounded-[16px] bg-ink text-gold-300 sm:grid">
          <CategoryIcon name={category.icon} className="size-7" />
        </span>
        <div>
          <h1 className="font-display text-[28px] leading-tight font-medium sm:text-[36px]">{category.name}</h1>
          <p className="mt-1 text-[14px] text-platinum-500">{t("common.items", { count: category.product_count })}</p>
        </div>
      </div>
      {category.children.length > 0 && (
        <div className="-mx-4 mb-6 flex gap-2 overflow-x-auto px-4 pb-1 scrollbar-none sm:mx-0 sm:flex-wrap sm:px-0">
          {category.children.map((child) => (
            <Link
              key={child.id}
              href={`/category/${child.slug}`}
              className={cn(
                "inline-flex shrink-0 items-center gap-2 rounded-[12px] bg-white px-3.5 py-2 text-[13.5px] font-semibold ring-1 ring-platinum-200 transition hover:ring-gold-400",
              )}
            >
              <CategoryIcon name={child.icon} className="size-4 text-gold-600" />
              {child.name}
              <span className="font-normal text-platinum-400">{child.product_count}</span>
            </Link>
          ))}
        </div>
      )}
      <Listing
        data={data}
        path={`/category/${slug}`}
        searchParams={pickListingParams(sp)}
        showCategories={false}
        top={banners?.[0] ? <BannerCard banner={banners[0]} /> : null}
      />
    </div>
  );
}
