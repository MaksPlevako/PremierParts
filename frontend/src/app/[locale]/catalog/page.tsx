import type { Metadata } from "next";
import { ArrowRight } from "lucide-react";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { CategoryIcon } from "@/components/catalog/CategoryIcon";
import { Link } from "@/i18n/navigation";
import { getCategories } from "@/lib/api";
import { readCarCookie } from "@/lib/car-cookie";
import { formatCount } from "@/lib/format";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("catalog");
  return { title: t("title"), description: t("subtitle"), alternates: { canonical: "/catalog" } };
}

export default async function CatalogPage({ params }: PageProps<"/[locale]/catalog">) {
  const { locale } = await params;
  setRequestLocale(locale);
  await readCarCookie();
  const [categories, t] = await Promise.all([getCategories(), getTranslations()]);

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs items={[{ name: t("common.catalog") }]} />
      <h1 className="mt-4 font-display text-[30px] font-medium sm:text-[38px]">{t("catalog.title")}</h1>
      <p className="mt-2 text-[15px] text-platinum-600">{t("catalog.subtitle")}</p>
      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {(categories ?? []).map((cat) => (
          <section key={cat.id} className="flex flex-col rounded-[24px] bg-white p-6 ring-1 ring-platinum-200">
            <Link href={`/category/${cat.slug}`} className="group flex items-center gap-4">
              <span className="grid size-14 place-items-center rounded-[16px] bg-ink text-gold-300">
                <CategoryIcon name={cat.icon} className="size-7" />
              </span>
              <span className="flex-1">
                <span className="block font-display text-[19px] font-medium group-hover:text-gold-800">{cat.name}</span>
                <span className="text-[13px] text-platinum-500">{t("common.items", { count: cat.product_count })}</span>
              </span>
              <ArrowRight className="size-5 text-platinum-300 transition group-hover:translate-x-1 group-hover:text-gold-600" />
            </Link>
            {cat.children.length > 0 && (
              <ul className="mt-5 grid gap-1 border-t border-platinum-100 pt-4">
                {cat.children.map((child) => (
                  <li key={child.id}>
                    <Link
                      href={`/category/${child.slug}`}
                      className="flex items-center gap-3 rounded-[10px] px-2 py-2 text-[14px] text-platinum-700 hover:bg-platinum-50 hover:text-ink"
                    >
                      <CategoryIcon name={child.icon} className="size-4.5 text-gold-600" />
                      <span className="flex-1">{child.name}</span>
                      <span className="text-[12px] text-platinum-400">{formatCount(child.product_count)}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
