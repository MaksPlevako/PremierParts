import { BadgeCheck, MapPin, RotateCcw, Truck } from "lucide-react";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { BannerCard } from "@/components/catalog/BannerCard";
import { Bento } from "@/components/home/Bento";
import { Hero } from "@/components/home/Hero";
import { MyCarStrip } from "@/components/home/MyCarStrip";
import { ProductGrid } from "@/components/product/ProductCard";
import { Link } from "@/i18n/navigation";
import { getHome, getSettingsSafe } from "@/lib/api";
import { readCarCookie } from "@/lib/car-cookie";
import { formatCount } from "@/lib/format";
import { JsonLd, storeJsonLd } from "@/lib/seo";

export default async function HomePage({ params }: PageProps<"/[locale]">) {
  const { locale } = await params;
  setRequestLocale(locale);
  await readCarCookie(); // personalised (dynamic) page
  const [home, settings, t] = await Promise.all([getHome(), getSettingsSafe(), getTranslations()]);
  if (!home) return null;

  const benefits = [
    { icon: BadgeCheck, title: t("home.b1"), text: t("home.b1t") },
    { icon: Truck, title: t("home.b2"), text: t("home.b2t") },
    { icon: RotateCcw, title: t("home.b3"), text: t("home.b3t") },
    { icon: MapPin, title: t("home.b4"), text: t("home.b4t") },
  ];

  return (
    <>
      <JsonLd data={storeJsonLd(settings)} />
      <Hero productCount={home.stats.products} />

      <div className="flex flex-col gap-16 pt-4 sm:gap-20">
        <Bento banner={home.banners.bento[0]} categories={home.categories} />

        <MyCarStrip />

        {home.banners.home_strip.length > 0 && (
          <section className="mx-auto grid w-full max-w-[1320px] gap-4 px-4 sm:px-6 lg:grid-cols-2">
            {home.banners.home_strip.slice(0, 2).map((b) => (
              <BannerCard key={b.id} banner={b} />
            ))}
          </section>
        )}

        <section className="mx-auto w-full max-w-[1320px] px-4 sm:px-6">
          <div className="mb-5 flex items-end justify-between">
            <h2 className="font-display text-[22px] font-medium sm:text-[26px]">{t("home.featured")}</h2>
            <Link href="/catalog" className="text-[14px] font-semibold text-gold-700 hover:text-gold-800">
              {t("home.allCatalog")}
            </Link>
          </div>
          <ProductGrid products={home.featured.slice(0, 8)} />
        </section>

        <section className="mx-auto w-full max-w-[1320px] px-4 sm:px-6">
          <div className="mb-5 flex items-end justify-between">
            <h2 className="font-display text-[22px] font-medium sm:text-[26px]">{t("home.popularMakes")}</h2>
            <Link href="/cars" className="text-[14px] font-semibold text-gold-700 hover:text-gold-800">
              {t("home.allMakes")}
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4 lg:grid-cols-8">
            {home.popular_makes.map((m) => (
              <Link
                key={m.id}
                href={`/cars/${m.slug}`}
                className="group flex flex-col items-center justify-center gap-1 rounded-[18px] bg-platinum-50 px-3 py-5 ring-1 ring-platinum-200 transition hover:bg-white hover:ring-gold-400"
              >
                <span className="font-display text-[15px] font-medium text-ink">{m.name}</span>
                <span className="text-[11.5px] text-platinum-500">{t("common.parts", { count: m.product_count })}</span>
              </Link>
            ))}
          </div>
        </section>

        {home.featured.length > 8 && (
          <section className="mx-auto w-full max-w-[1320px] px-4 sm:px-6">
            <ProductGrid products={home.featured.slice(8, 16)} />
          </section>
        )}

        <section className="mx-auto w-full max-w-[1320px] px-4 sm:px-6">
          <h2 className="mb-5 font-display text-[22px] font-medium sm:text-[26px]">{t("home.benefits")}</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {benefits.map(({ icon: Icon, title, text }) => (
              <div key={title} className="rounded-[22px] bg-white p-6 ring-1 ring-platinum-200">
                <Icon className="size-6 text-gold-600" />
                <p className="mt-4 font-display text-[22px] font-medium text-ink">{title}</p>
                <p className="mt-1 text-[14px] text-platinum-600">{text}</p>
              </div>
            ))}
          </div>
        </section>

        {home.promotions.length > 0 && (
          <section className="mx-auto w-full max-w-[1320px] px-4 sm:px-6">
            <h2 className="mb-5 font-display text-[22px] font-medium sm:text-[26px]">{t("home.promotions")}</h2>
            <div className="grid gap-3 md:grid-cols-3">
              {home.promotions.map((p) => (
                <Link
                  key={p.id}
                  href={`/promotions/${p.slug}`}
                  className="group flex items-center gap-5 rounded-[22px] bg-white p-5 ring-1 ring-platinum-200 transition hover:ring-gold-400"
                >
                  <span className="font-display text-[34px] font-medium text-gold">−{p.discount_percent}%</span>
                  <span className="min-w-0">
                    <span className="block font-semibold text-ink">{p.title}</span>
                    <span className="line-clamp-2 text-[13px] text-platinum-500">{p.description}</span>
                  </span>
                </Link>
              ))}
            </div>
          </section>
        )}

        {settings?.about_short && (
          <section className="mx-auto w-full max-w-[1320px] px-4 sm:px-6">
            <div className="grid gap-6 rounded-[26px] bg-platinum-50 p-7 ring-1 ring-platinum-200 sm:p-10 lg:grid-cols-[1fr_1.4fr]">
              <div>
                <p className="text-[11px] font-bold tracking-[0.24em] text-gold-700">{t("home.about").toUpperCase()}</p>
                <p className="mt-3 font-display text-[26px] leading-tight font-medium">
                  Premier Parts — <span className="text-gold">{formatCount(home.stats.products)}+</span> деталей для {home.stats.makes} марок
                </p>
              </div>
              <p className="text-[15px] leading-7 text-platinum-700">{settings.about_short}</p>
            </div>
          </section>
        )}
      </div>
    </>
  );
}
