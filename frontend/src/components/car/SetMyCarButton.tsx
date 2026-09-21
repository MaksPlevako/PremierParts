"use client";

import { BadgeCheck, Car } from "lucide-react";
import { useTranslations } from "next-intl";

import { toast } from "@/components/ui/Toaster";
import { useHydrated } from "@/lib/use-hydrated";
import { useRouter } from "@/i18n/navigation";
import { cn } from "@/lib/format";
import type { CarRef } from "@/lib/types";
import { useMyCar } from "@/stores/my-car";

export function SetMyCarButton({ car, className }: { car: CarRef; className?: string }) {
  const t = useTranslations("car");
  const tSearch = useTranslations("search");
  const router = useRouter();
  const { car: current, setCar } = useMyCar();
  const mounted = useHydrated();
  const active = mounted && current?.generation_id === car.generation_id;

  return (
    <button
      type="button"
      disabled={active}
      onClick={() => {
        setCar(car);
        toast({ title: t("saved", { car: car.full_label }), text: t("chooseCarHint") });
        router.refresh();
      }}
      className={cn(
        "inline-flex h-11 items-center gap-2 rounded-[13px] px-5 text-[14px] font-bold transition",
        active ? "bg-success-soft text-success" : "bg-gold text-[#1e1606] shadow-gold",
        className,
      )}
    >
      {active ? <BadgeCheck className="size-4" /> : <Car className="size-4" />}
      {active ? t("myCar") : tSearch("makeMyCar")}
    </button>
  );
}
