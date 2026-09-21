"use client";

import { BadgeCheck, Car } from "lucide-react";
import { useTranslations } from "next-intl";

import type { CarRef, UnderstoodCar } from "@/lib/types";
import { useMyCar } from "@/stores/my-car";

import { useQueryState } from "./useQueryState";

/** Explains why the listing is narrowed and offers a one-click way out. */
export function ActiveCarBanner({ car, source }: { car: CarRef | UnderstoodCar | null; source: string | null }) {
  const t = useTranslations("car");
  const { params, update } = useQueryState();
  const openPicker = useMyCar((s) => s.openPicker);
  const allCars = params.get("all_cars") === "1";
  const myCar = useMyCar((s) => s.car);

  if (allCars && myCar) {
    return (
      <div className="flex flex-wrap items-center gap-3 rounded-[14px] bg-platinum-50 px-4 py-3 text-[13.5px] text-platinum-700 ring-1 ring-platinum-200">
        <Car className="size-4 text-gold-700" />
        <span className="flex-1">Показано для всіх авто</span>
        <button type="button" onClick={() => update({ all_cars: null })} className="font-semibold text-gold-700 hover:text-gold-800">
          {t("fitsYour", { car: myCar.full_label })}
        </button>
      </div>
    );
  }
  if (!car || source !== "my_car") return null;
  const label = "full_label" in car && car.full_label ? car.full_label : `${car.make} ${car.label}`;
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-[14px] bg-success-soft/70 px-4 py-3 text-[13.5px] text-platinum-700 ring-1 ring-success/15">
      <BadgeCheck className="size-4 text-success" />
      <span className="flex-1">
        {t("filteredFor")} <b className="text-ink">{label}</b>
      </span>
      <button type="button" onClick={openPicker} className="font-semibold text-platinum-600 hover:text-ink">
        Змінити
      </button>
      <button type="button" onClick={() => update({ all_cars: "1" })} className="font-semibold text-gold-700 hover:text-gold-800">
        {t("showAllCars")}
      </button>
    </div>
  );
}
