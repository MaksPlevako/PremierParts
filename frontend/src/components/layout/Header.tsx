import { Clock, MapPin } from "lucide-react";

import type { CategoryNode, SiteSettings } from "@/lib/types";
import { formatPhoneHref } from "@/lib/format";

import { HeaderBar } from "./HeaderBar";

export function Header({ settings, categories }: { settings: SiteSettings | null; categories: CategoryNode[] }) {
  const phones = settings?.phones ?? [];
  return (
    <>
      <div className="hidden border-b border-platinum-200/70 bg-platinum-50 text-[12px] text-platinum-600 md:block">
        <div className="mx-auto flex h-9 max-w-[1320px] items-center justify-between gap-6 px-6">
          <div className="flex items-center gap-5">
            {settings?.address && (
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="size-3.5 text-gold-600" />
                {settings.address}
              </span>
            )}
            {settings?.work_hours && (
              <span className="inline-flex items-center gap-1.5">
                <Clock className="size-3.5 text-gold-600" />
                {settings.work_hours}
              </span>
            )}
          </div>
          <div className="flex items-center gap-5">
            {phones.map((p) => (
              <a key={p.number} href={formatPhoneHref(p.number)} className="font-semibold text-ink hover:text-gold-700">
                {p.label}
                {p.viber && <span className="ml-1.5 rounded-md bg-[#7360f2]/10 px-1.5 py-0.5 text-[10px] font-bold text-[#7360f2]">Viber</span>}
              </a>
            ))}
          </div>
        </div>
      </div>
      <HeaderBar categories={categories} phone={phones[0] ?? null} />
    </>
  );
}
