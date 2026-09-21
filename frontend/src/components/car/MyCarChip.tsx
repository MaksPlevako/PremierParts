"use client";

import { Car, X } from "lucide-react";
import { useTranslations } from "next-intl";

import { useHydrated } from "@/lib/use-hydrated";
import { useRouter } from "@/i18n/navigation";
import { cn } from "@/lib/format";
import { useMyCar } from "@/stores/my-car";

export function MyCarChip({ className }: { className?: string }) {
  const t = useTranslations("car");
  const router = useRouter();
  const { car, openPicker, setCar } = useMyCar();
  const mounted = useHydrated();

  if (!mounted || !car) {
    return (
      <button
        type="button"
        onClick={openPicker}
        className={cn(
          "inline-flex h-10 items-center gap-2 rounded-[12px] px-3 text-[13px] font-semibold text-ink ring-1 ring-platinum-200 transition hover:ring-gold-400",
          className,
        )}
      >
        <Car className="size-4 text-gold-600" />
        <span className="hidden sm:inline">{t("chooseCar")}</span>
      </button>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex h-10 max-w-[240px] items-center gap-1 rounded-[12px] bg-gold pr-1 pl-3 text-[13px] font-bold text-[#1e1606] shadow-gold",
        className,
      )}
    >
      <button type="button" onClick={openPicker} className="flex min-w-0 items-center gap-2" title={car.full_label}>
        <Car className="size-4 shrink-0" />
        <span className="hidden truncate sm:inline">
          {car.label}
        </span>
        <span className="sm:hidden">{t("myCar")}</span>
      </button>
      <button
        type="button"
        onClick={() => {
          setCar(null);
          router.refresh();
        }}
        className="grid size-7 shrink-0 place-items-center rounded-[9px] hover:bg-black/10"
        aria-label={t("clear")}
      >
        <X className="size-3.5" />
      </button>
    </span>
  );
}
