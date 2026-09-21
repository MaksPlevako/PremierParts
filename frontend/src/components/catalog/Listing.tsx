import { PackageSearch } from "lucide-react";
import { getTranslations } from "next-intl/server";
import type { ReactNode } from "react";

import { ProductGrid } from "@/components/product/ProductCard";
import type { ListingResult } from "@/lib/types";

import { ActiveCarBanner } from "./ActiveCarBanner";
import { Filters } from "./Filters";
import { Pagination } from "./Pagination";
import { SortSelect } from "./SortSelect";

interface Props {
  data: ListingResult;
  path: string;
  searchParams: Record<string, string | undefined>;
  categoryHrefPrefix?: string;
  showCategories?: boolean;
  aside?: ReactNode;
  top?: ReactNode;
}

export async function Listing({ data, path, searchParams, categoryHrefPrefix, showCategories = true, aside, top }: Props) {
  const t = await getTranslations();
  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr] lg:gap-8">
      <div className="flex flex-col gap-4">
        <Filters
          facets={data.facets}
          priceRange={data.price_range}
          count={data.count}
          categoryHrefPrefix={categoryHrefPrefix}
          showCategories={showCategories}
        />
        {aside}
      </div>
      <div className="flex min-w-0 flex-col gap-4">
        <ActiveCarBanner car={data.car} source={data.car_source} />
        {top}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-[14px] text-platinum-600">
            Знайдено <b className="text-ink">{t("common.items", { count: data.count })}</b>
          </p>
          <SortSelect />
        </div>
        {data.relaxed && (
          <p className="rounded-[12px] bg-gold-50 px-4 py-2.5 text-[13px] font-medium text-warning ring-1 ring-gold-200">
            {t("search.relaxed")}
          </p>
        )}
        {data.results.length ? (
          <ProductGrid products={data.results} className="xl:grid-cols-3 2xl:grid-cols-4" />
        ) : (
          <div className="flex flex-col items-center gap-3 rounded-[22px] bg-platinum-50 px-6 py-16 text-center ring-1 ring-platinum-200">
            <PackageSearch className="size-10 text-gold-600" />
            <p className="font-display text-[18px] font-medium">{t("catalog.empty")}</p>
            <p className="max-w-md text-[14px] text-platinum-600">{t("catalog.emptyHint")}</p>
          </div>
        )}
        <Pagination page={data.page} total={data.pages} path={path} searchParams={searchParams} />
      </div>
    </div>
  );
}
