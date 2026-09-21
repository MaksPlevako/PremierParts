"use client";

import { ArrowRight, Car, ScanLine } from "lucide-react";
import { useTranslations } from "next-intl";

import { Link } from "@/i18n/navigation";
import { useHydrated } from "@/lib/use-hydrated";
import { useMyCar } from "@/stores/my-car";

export function MyCarStrip() {
  const t = useTranslations("home");
  const { car, openPicker } = useMyCar();
  const mounted = useHydrated();
  const active = mounted && car;

  return (
    <section className="mx-auto w-full max-w-[1320px] px-4 sm:px-6">
      <div className="relative flex flex-col gap-5 overflow-hidden rounded-[24px] bg-white p-6 ring-1 ring-platinum-200 sm:flex-row sm:items-center sm:p-7">
        <div className="pointer-events-none absolute -right-24 -bottom-24 size-72 rounded-full bg-gold-200/30 blur-3xl" />
        <span className="grid size-14 shrink-0 place-items-center rounded-[16px] bg-ink text-gold-300">
          <Car className="size-7" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-display text-[18px] font-medium text-ink sm:text-[20px]">
            {active ? t("myCarActive", { car: car.full_label }) : t("myCarTitle")}
          </p>
          <p className="mt-1 text-[14px] text-platinum-600">{t("myCarText")}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {active ? (
            <>
              <Link
                href={`/cars/${car.make_slug}/${car.model_slug}/${car.generation_slug}`}
                className="inline-flex h-12 items-center gap-2 rounded-[14px] bg-ink px-5 font-semibold text-white hover:bg-graphite-700"
              >
                {t("categories")} <ArrowRight className="size-4" />
              </Link>
              <button type="button" onClick={openPicker} className="h-12 rounded-[14px] px-5 font-semibold ring-1 ring-platinum-200 hover:ring-gold-400">
                {t("myCarChange")}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={openPicker}
                className="inline-flex h-12 items-center gap-2 rounded-[14px] bg-gold px-6 font-bold text-[#1e1606] shadow-gold"
              >
                <Car className="size-4" /> {t("myCarCta")}
              </button>
              <Link href="/vin" className="inline-flex h-12 items-center gap-2 rounded-[14px] px-5 font-semibold ring-1 ring-platinum-200 hover:ring-gold-400">
                <ScanLine className="size-4 text-gold-700" /> VIN
              </Link>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
