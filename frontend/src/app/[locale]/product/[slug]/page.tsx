import { BadgeCheck, Car, CreditCard, MapPin, RotateCcw, ShieldCheck, Truck } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { BannerCard } from "@/components/catalog/BannerCard";
import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { BuyBox } from "@/components/product/BuyBox";
import { Gallery } from "@/components/product/Gallery";
import { PartNumbers } from "@/components/product/PartNumbers";
import { ProductGrid } from "@/components/product/ProductCard";
import { Link } from "@/i18n/navigation";
import { getBanners, getProduct, getSettingsSafe } from "@/lib/api";
import { readCarCookie } from "@/lib/car-cookie";
import { formatPrice } from "@/lib/format";
import { JsonLd, productJsonLd } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/product/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const p = await getProduct(slug);
  if (!p) return {};
  const price = p.sale_price ?? p.price;
  const description = [
    p.name,
    p.manufacturer && `Виробник ${p.manufacturer}`,
    p.sku && `арт. ${p.sku}`,
    price ? `Ціна ${formatPrice(price)}` : null,
    "Доставка по Україні, самовивіз у Києві.",
  ]
    .filter(Boolean)
    .join(". ");
  return {
    title: `${p.name} — купити`,
    description,
    alternates: { canonical: `/product/${p.slug}` },
    openGraph: { type: "website", title: p.name, description, images: p.images.slice(0, 1).map((i) => ({ url: i.url, alt: p.name })) },
  };
}

export default async function ProductPage({ params }: PageProps<"/[locale]/product/[slug]">) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  await readCarCookie();
  const [product, settings, sideBanners, t] = await Promise.all([
    getProduct(slug),
    getSettingsSafe(),
    getBanners("product_side").catch(() => null),
    getTranslations(),
  ]);
  if (!product) notFound();

  const specs = [
    [t("product.manufacturer"), product.manufacturer],
    [t("common.sku"), product.sku],
    [t("product.condition"), t("product.new")],
    [t("product.side"), product.side === "left" ? t("catalog.left") : product.side === "right" ? t("catalog.right") : null],
    [t("product.position"), product.position === "front" ? t("product.front") : product.position === "rear" ? t("product.rear") : null],
  ].filter(([, v]) => v) as [string, string][];

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <JsonLd data={productJsonLd(product)} />
      <Breadcrumbs items={[...product.breadcrumbs, { name: product.name, href: `/product/${product.slug}` }]} />

      <div className="mt-5 grid gap-8 lg:grid-cols-[1.1fr_1fr] lg:gap-12">
        <Gallery images={product.images} name={product.name} />

        <div className="flex flex-col gap-6">
          <div>
            {product.manufacturer && (
              <p className="text-[12px] font-bold tracking-[0.2em] text-gold-700">{product.manufacturer.toUpperCase()}</p>
            )}
            <h1 className="mt-2 font-display text-[24px] leading-[1.2] font-medium sm:text-[30px]">{product.name}</h1>
          </div>
          <PartNumbers numbers={product.part_numbers} />
          <BuyBox product={product} />
          <ul className="grid gap-2 text-[13.5px] text-platinum-700 sm:grid-cols-2">
            <li className="flex items-center gap-2">
              <Truck className="size-4 text-gold-600" /> Нова Пошта 1–2 дні
            </li>
            <li className="flex items-center gap-2">
              <MapPin className="size-4 text-gold-600" /> Самовивіз: Беретті, 6Б
            </li>
            <li className="flex items-center gap-2">
              <ShieldCheck className="size-4 text-gold-600" /> {t("product.guarantee")}
            </li>
            <li className="flex items-center gap-2">
              <RotateCcw className="size-4 text-gold-600" /> {t("product.returns")}
            </li>
          </ul>
        </div>
      </div>

      <div className="mt-12 grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="flex flex-col gap-6">
          <section className="rounded-[24px] bg-white p-6 ring-1 ring-platinum-200">
            <h2 className="mb-4 flex items-center gap-2 font-display text-[19px] font-medium">
              <Car className="size-5 text-gold-600" /> {t("product.fitment")}
            </h2>
            {product.fitments.length ? (
              <ul className="divide-y divide-platinum-100">
                {product.fitments.map((f) => (
                  <li key={f.generation_id}>
                    <Link
                      href={`/cars/${f.make_slug}/${f.model_slug}/${f.generation_slug}`}
                      className="flex items-center justify-between gap-4 py-3 hover:text-gold-800"
                    >
                      <span className="font-semibold">
                        {f.make} {f.model}
                      </span>
                      <span className="text-[13px] text-platinum-500">{f.years_label || "усі роки"}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-[14px] text-platinum-600">
                {t("product.fitmentEmpty")}{" "}
                <Link href="/vin#request" className="font-semibold text-gold-700">
                  {t("search.vinRequest")} →
                </Link>
              </p>
            )}
          </section>

          <section className="rounded-[24px] bg-white p-6 ring-1 ring-platinum-200">
            <h2 className="mb-4 font-display text-[19px] font-medium">{t("product.specs")}</h2>
            <dl className="grid gap-x-8 sm:grid-cols-2">
              {specs.map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4 border-b border-platinum-100 py-2.5 text-[14px]">
                  <dt className="text-platinum-500">{k}</dt>
                  <dd className="text-right font-semibold">{v}</dd>
                </div>
              ))}
            </dl>
            {product.description && (
              <>
                <h3 className="mt-6 mb-2 font-semibold">{t("product.description")}</h3>
                <p className="text-[14.5px] leading-7 whitespace-pre-line text-platinum-700">{product.description}</p>
              </>
            )}
          </section>
        </div>

        <aside className="flex flex-col gap-4">
          <section className="rounded-[24px] bg-platinum-50 p-6 ring-1 ring-platinum-200">
            <h2 className="mb-4 font-display text-[17px] font-medium">{t("product.delivery")}</h2>
            <ul className="flex flex-col gap-4 text-[13.5px] text-platinum-700">
              <li className="flex gap-3">
                <Truck className="size-5 shrink-0 text-gold-600" />
                <span>
                  <b className="text-ink">Нова Пошта</b> — відділення, поштомат або кур&apos;єр. 100% передоплата на рахунок ФОП.
                </span>
              </li>
              <li className="flex gap-3">
                <MapPin className="size-5 shrink-0 text-gold-600" />
                <span>
                  <b className="text-ink">Самовивіз</b> — {settings?.address}. {settings?.pickup_note}.
                </span>
              </li>
              <li className="flex gap-3">
                <CreditCard className="size-5 shrink-0 text-gold-600" />
                <span>
                  <b className="text-ink">Оплата</b> — на рахунок ФОП, карткою або готівкою при самовивозі.
                </span>
              </li>
              <li className="flex gap-3">
                <BadgeCheck className="size-5 shrink-0 text-gold-600" />
                <span>Нові деталі від перевірених виробників з гарантією.</span>
              </li>
            </ul>
          </section>
          {sideBanners?.[0] && <BannerCard banner={sideBanners[0]} compact />}
        </aside>
      </div>

      {product.related.length > 0 && (
        <section className="mt-14">
          <h2 className="mb-5 font-display text-[22px] font-medium sm:text-[26px]">{t("product.related")}</h2>
          <ProductGrid products={product.related} />
        </section>
      )}
    </div>
  );
}
