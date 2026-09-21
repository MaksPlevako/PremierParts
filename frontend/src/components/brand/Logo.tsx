import { useId } from "react";

import { cn } from "@/lib/format";

/** Vector take on the original logo: a gold horseshoe on a graphite badge. */
export function LogoMark({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <defs>
        <linearGradient id={`g${id}`} x1="8" y1="4" x2="58" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#9C7424" />
          <stop offset=".42" stopColor="#E7C573" />
          <stop offset=".55" stopColor="#F7E6B0" />
          <stop offset="1" stopColor="#B98E3A" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="16" fill="#15181C" />
      <path
        fill={`url(#g${id})`}
        d="M11 9h14v4h-2v20a9 9 0 0 0 18 0V13h-2V9h14v4h-2v20a19 19 0 0 1-38 0V13h-2z"
      />
      <g fill="#15181C" opacity=".6">
        <circle cx="18" cy="18" r="1.7" />
        <circle cx="18" cy="26" r="1.7" />
        <circle cx="19.2" cy="34" r="1.7" />
        <circle cx="23.5" cy="41.5" r="1.7" />
        <circle cx="46" cy="18" r="1.7" />
        <circle cx="46" cy="26" r="1.7" />
        <circle cx="44.8" cy="34" r="1.7" />
        <circle cx="40.5" cy="41.5" r="1.7" />
      </g>
    </svg>
  );
}

/** The bare horseshoe (no badge) for large decorative use. */
export function Horseshoe({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <defs>
        <linearGradient id={`h${id}`} x1="8" y1="4" x2="58" y2="60" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#9C7424" />
          <stop offset=".42" stopColor="#E7C573" />
          <stop offset=".55" stopColor="#F7E6B0" />
          <stop offset="1" stopColor="#B98E3A" />
        </linearGradient>
      </defs>
      <path
        fill={`url(#h${id})`}
        d="M11 9h14v4h-2v20a9 9 0 0 0 18 0V13h-2V9h14v4h-2v20a19 19 0 0 1-38 0V13h-2z"
      />
    </svg>
  );
}

export function Logo({ className, tone = "dark" }: { className?: string; tone?: "dark" | "light" }) {
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark className="size-9 shrink-0 drop-shadow-sm" />
      <span className="flex flex-col leading-none">
        <span
          className={cn(
            "font-display text-[15px] font-semibold tracking-[0.08em]",
            tone === "dark" ? "text-ink" : "text-white",
          )}
        >
          PREMIER
        </span>
        <span className="mt-1 font-display text-[10px] font-medium tracking-[0.42em] text-gold-600">PARTS</span>
      </span>
    </span>
  );
}
