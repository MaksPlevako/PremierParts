"use client";

import { AlertTriangle, BadgeCheck } from "lucide-react";
import { useTranslations } from "next-intl";

import { cn } from "@/lib/format";
import { fitsCar, useMyCar } from "@/stores/my-car";
import { useHydrated } from "@/lib/use-hydrated";

/** «Підходить / Може не підходити» for the car chosen in «Моє авто». Renders nothing without a car. */
export function FitBadge({ generationIds, size = "sm" }: { generationIds: number[]; size?: "sm" | "lg" }) {
  const t = useTranslations("car");
  const car = useMyCar((s) => s.car);
  const mounted = useHydrated();
  const fits = mounted ? fitsCar(generationIds, car) : null;
  if (fits === null || (!fits && generationIds.length === 0)) return null;

  if (size === "lg") {
    return (
      <div
        className={cn(
          "flex items-center gap-3 rounded-[14px] px-4 py-3 text-[14px] font-semibold",
          fits ? "bg-success-soft text-success" : "bg-gold-50 text-warning ring-1 ring-gold-200",
        )}
      >
        {fits ? <BadgeCheck className="size-5 shrink-0" /> : <AlertTriangle className="size-5 shrink-0" />}
        {fits ? t("fitsYour", { car: car!.full_label }) : t("mayNotFit", { car: car!.full_label })}
      </div>
    );
  }

  return fits ? (
    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-success">
      <BadgeCheck className="size-3.5" /> {t("fits")}
    </span>
  ) : null;
}
