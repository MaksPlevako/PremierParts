import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { Link } from "@/i18n/navigation";
import { getMakes } from "@/lib/api";
import { readCarCookie } from "@/lib/car-cookie";

export const metadata: Metadata = {
  title: "Запчастини за марками авто",
  description: "Кузовні запчастини для 50+ марок: Toyota, Volkswagen, Hyundai, Kia, Ford, Mercedes-Benz та інших.",
  alternates: { canonical: "/cars" },
};

export default async function CarsPage({ params }: PageProps<"/[locale]/cars">) {
  const { locale } = await params;
  setRequestLocale(locale);
  await readCarCookie();
  const [makes, t] = await Promise.all([getMakes(), getTranslations()]);
  const list = (makes ?? []).filter((m) => m.product_count > 0 || m.is_popular);
  const popular = list.filter((m) => m.is_popular);
  const byLetter = new Map<string, typeof list>();
  for (const m of [...list].sort((a, b) => a.name.localeCompare(b.name))) {
    const letter = m.name[0].toUpperCase();
    byLetter.set(letter, [...(byLetter.get(letter) ?? []), m]);
  }

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs items={[{ name: t("common.cars") }]} />
      <h1 className="mt-4 font-display text-[30px] font-medium sm:text-[38px]">{t("common.cars")}</h1>
      <p className="mt-2 text-[15px] text-platinum-600">Оберіть марку — далі модель і роки випуску. Ми покажемо лише сумісні деталі.</p>

      <h2 className="mt-10 mb-4 text-[12px] font-bold tracking-[0.2em] text-platinum-400">{t("car.popular").toUpperCase()}</h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-8">
        {popular.map((m) => (
          <Link
            key={m.id}
            href={`/cars/${m.slug}`}
            className="flex flex-col items-center gap-1 rounded-[18px] bg-platinum-50 px-3 py-6 ring-1 ring-platinum-200 transition hover:bg-white hover:ring-gold-400"
          >
            <span className="font-display text-[16px] font-medium">{m.name}</span>
            <span className="text-[12px] text-platinum-500">{t("common.parts", { count: m.product_count })}</span>
          </Link>
        ))}
      </div>

      <h2 className="mt-12 mb-4 text-[12px] font-bold tracking-[0.2em] text-platinum-400">{t("car.allMakes").toUpperCase()}</h2>
      <div className="columns-2 gap-8 sm:columns-3 lg:columns-5">
        {[...byLetter.entries()].map(([letter, items]) => (
          <div key={letter} className="mb-6 break-inside-avoid">
            <p className="mb-2 font-display text-[20px] font-medium text-gold-600">{letter}</p>
            <ul className="flex flex-col gap-1">
              {items.map((m) => (
                <li key={m.id}>
                  <Link href={`/cars/${m.slug}`} className="flex justify-between gap-2 py-0.5 text-[14.5px] hover:text-gold-800">
                    <span>{m.name}</span>
                    <span className="text-[12px] text-platinum-400">{m.product_count || ""}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
