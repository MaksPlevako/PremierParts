import { ArrowUpRight } from "lucide-react";
import Image from "next/image";
import { getTranslations } from "next-intl/server";

import { CategoryIcon } from "@/components/catalog/CategoryIcon";
import { Link } from "@/i18n/navigation";
import { formatCount } from "@/lib/format";
import type { Banner, CategoryNode } from "@/lib/types";

export async function Bento({ banner, categories }: { banner?: Banner; categories: CategoryNode[] }) {
  const t = await getTranslations();
  const tiles = categories.slice(0, 6);

  return (
    <section className="mx-auto w-full max-w-[1320px] px-4 sm:px-6">
      <div className="mb-5 flex items-end justify-between">
        <h2 className="font-display text-[22px] font-medium sm:text-[26px]">{t("home.categories")}</h2>
        <Link href="/catalog" className="text-[14px] font-semibold text-gold-700 hover:text-gold-800">
          {t("home.allCatalog")}
        </Link>
      </div>
      <div className="grid gap-3 sm:gap-4 lg:grid-cols-[1.25fr_1fr_1fr] lg:grid-rows-[repeat(2,minmax(170px,auto))]">
        {banner && (
          <Link
            href={banner.link || "/promotions"}
            className="group relative flex min-h-[260px] flex-col justify-between overflow-hidden rounded-[24px] bg-lux p-7 text-white lg:row-span-2"
          >
            <div className="relative z-10 max-w-[58%]">
              {banner.eyebrow && <p className="text-[11px] font-bold tracking-[0.24em] text-gold-300">{banner.eyebrow}</p>}
              <p className="mt-3 font-display text-[34px] leading-[1.05] font-medium sm:text-[44px]">
                <span className="text-gold">{banner.title}</span>
              </p>
              {banner.subtitle && <p className="mt-3 text-[14px] text-platinum-300">{banner.subtitle}</p>}
            </div>
            {banner.cta_label && (
              <span className="relative z-10 inline-flex w-fit items-center gap-2 rounded-[12px] bg-white/10 px-4 py-2.5 text-[13px] font-semibold ring-1 ring-white/20 transition group-hover:bg-gold group-hover:text-[#1e1606]">
                {banner.cta_label} <ArrowUpRight className="size-4" />
              </span>
            )}
            {banner.image && (
              <div className="absolute -right-8 -bottom-10 h-[54%] w-[52%] rotate-[-6deg] overflow-hidden rounded-[18px] shadow-[0_30px_60px_rgba(0,0,0,.55)] ring-1 ring-white/10 transition-transform duration-700 ease-[var(--ease-lux)] group-hover:rotate-[-3deg] group-hover:scale-[1.03]">
                <Image src={banner.image} alt="" fill sizes="(min-width:1024px) 420px, 70vw" className="object-cover" />
              </div>
            )}
          </Link>
        )}
        {tiles.map((cat) => (
          <Link
            key={cat.id}
            href={`/category/${cat.slug}`}
            className="group relative flex min-h-[150px] flex-col justify-between overflow-hidden rounded-[22px] bg-white p-5 ring-1 ring-platinum-200 transition hover:ring-gold-400 hover:shadow-[0_20px_40px_-28px_rgba(156,116,36,.6)]"
          >
            <span className="grid size-12 place-items-center rounded-[14px] bg-platinum-50 text-gold-700 ring-1 ring-platinum-200 transition group-hover:bg-ink group-hover:text-gold-300">
              <CategoryIcon name={cat.icon} className="size-6" />
            </span>
            <div>
              <p className="font-display text-[17px] font-medium text-ink">{cat.name}</p>
              <p className="mt-0.5 text-[13px] text-platinum-500">
                {cat.children
                  .slice(0, 3)
                  .map((c) => c.name.split(/[,(]/)[0].trim().toLowerCase())
                  .join(", ") || t("common.items", { count: cat.product_count })}
              </p>
            </div>
            <span className="absolute top-5 right-5 text-[12px] font-semibold text-platinum-400">{formatCount(cat.product_count)}</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
