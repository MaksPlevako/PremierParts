import { ArrowUpRight } from "lucide-react";
import Image from "next/image";

import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/format";
import type { Banner } from "@/lib/types";

const THEMES = {
  dark: "bg-lux text-white",
  gold: "bg-[linear-gradient(135deg,#f7efdc_0%,#f1d78e_55%,#d9b45e_120%)] text-ink",
  light: "bg-white text-ink ring-1 ring-platinum-200",
};

/** Admin-managed banner / ad block. Works for home strips, catalog tops and product sidebars. */
export function BannerCard({ banner, compact = false }: { banner: Banner; compact?: boolean }) {
  const dark = banner.theme === "dark";
  return (
    <Link
      href={banner.link || "#"}
      className={cn(
        "group relative flex overflow-hidden rounded-[22px] transition-shadow hover:shadow-[0_24px_50px_-30px_rgba(21,24,28,.6)]",
        THEMES[banner.theme],
        compact ? "min-h-[150px] flex-col p-5" : "min-h-[180px] items-center gap-6 p-6 sm:p-8",
      )}
    >
      <div className={cn("relative z-10 flex min-w-0 flex-1 flex-col", compact ? "gap-2" : "max-w-[62%] gap-2")}>
        {banner.eyebrow && (
          <p className={cn("text-[10.5px] font-bold tracking-[0.24em]", dark ? "text-gold-300" : "text-gold-800")}>{banner.eyebrow}</p>
        )}
        <p className={cn("font-display leading-tight font-medium", compact ? "text-[17px]" : "text-[22px] sm:text-[26px]")}>{banner.title}</p>
        {banner.subtitle && <p className={cn("text-[13.5px]", dark ? "text-platinum-300" : "text-platinum-700")}>{banner.subtitle}</p>}
        {banner.cta_label && (
          <span
            className={cn(
              "mt-2 inline-flex w-fit items-center gap-1.5 rounded-[11px] px-3.5 py-2 text-[13px] font-semibold transition",
              dark ? "bg-white/10 ring-1 ring-white/20 group-hover:bg-gold group-hover:text-[#1e1606]" : "bg-ink text-white",
            )}
          >
            {banner.cta_label} <ArrowUpRight className="size-4" />
          </span>
        )}
      </div>
      {banner.image && !compact && (
        <div className="absolute top-1/2 -right-6 h-[140%] w-[42%] -translate-y-1/2 rotate-[-5deg] overflow-hidden rounded-[18px] shadow-[0_20px_50px_rgba(0,0,0,.45)] transition-transform duration-700 group-hover:rotate-[-2deg]">
          <Image src={banner.image} alt="" fill sizes="(min-width:1024px) 300px, 40vw" className="object-cover" />
        </div>
      )}
    </Link>
  );
}
