"use client";

import { RotateCw } from "lucide-react";
import { useTranslations } from "next-intl";

import { CarMark } from "@/components/brand/Logo";

export default function ErrorPage({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const t = useTranslations();
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center px-4 py-24 text-center">
      <CarMark className="size-20 opacity-70" />
      <h1 className="mt-6 font-display text-[26px] font-medium">{t("errors.generic")}</h1>
      <p className="mt-3 text-[15px] text-platinum-600">{t("errors.genericText")}</p>
      <button type="button" onClick={reset} className="mt-8 inline-flex h-12 items-center gap-2 rounded-[14px] bg-ink px-6 font-semibold text-white">
        <RotateCw className="size-4" /> {t("common.retry")}
      </button>
    </div>
  );
}
