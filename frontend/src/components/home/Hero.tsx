"use client";

import { animate, stagger, svg } from "animejs";
import { useTranslations } from "next-intl";
import { useEffect, useRef } from "react";

import { Horseshoe } from "@/components/brand/Logo";
import { SearchBox } from "@/components/search/SearchBox";
import { Link } from "@/i18n/navigation";
import { formatCount } from "@/lib/format";

const EXAMPLES = ["фара пасат B7", "бампер камрі 50", "радіатор пічки", "дзеркало тойота рав4"];

export function Hero({ productCount }: { productCount: number }) {
  const t = useTranslations("home");
  const tSearch = useTranslations("search");
  const root = useRef<HTMLDivElement>(null);
  const counter = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const el = root.current;
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const lines = animate(svg.createDrawable(el.querySelectorAll(".hero-line")), {
      draw: ["0 0", "0 1"],
      ease: "inOutQuad",
      duration: 2200,
      delay: stagger(160, { start: 200 }),
    });
    const shoe = animate(el.querySelectorAll(".hero-shoe"), {
      opacity: [0, 0.14],
      translateY: [18, 0],
      rotate: [-8, 0],
      duration: 1400,
      ease: "outExpo",
      delay: 300,
    });
    const value = { n: Math.round(productCount * 0.6) };
    const count = animate(value, {
      n: productCount,
      duration: 1800,
      ease: "outExpo",
      onUpdate: () => {
        if (counter.current) counter.current.textContent = formatCount(Math.round(value.n));
      },
    });
    return () => {
      lines.revert();
      shoe.revert();
      count.pause();
    };
  }, [productCount]);

  return (
    <section ref={root} className="relative isolate overflow-hidden bg-platinum">
      {/* metallic sheen */}
      <div className="pointer-events-none absolute -top-72 left-1/2 -z-10 h-[620px] w-[1100px] -translate-x-1/2 rounded-full bg-[conic-gradient(from_200deg,#d7dbe0,#ffffff,#c9ced4,#f4f5f7,#d7dbe0)] opacity-90 blur-3xl" />
      {/* golden curves */}
      <svg
        className="pointer-events-none absolute inset-0 -z-10 h-full w-full"
        viewBox="0 0 1440 640"
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="hero-gold" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0" stopColor="#c9a04a" stopOpacity="0" />
            <stop offset=".45" stopColor="#e7c573" />
            <stop offset="1" stopColor="#b98e3a" stopOpacity="0" />
          </linearGradient>
        </defs>
        <path className="hero-line" d="M-40 520 C 280 380, 520 620, 820 470 S 1300 300, 1480 380" stroke="url(#hero-gold)" strokeWidth="1.4" fill="none" />
        <path className="hero-line" d="M-40 560 C 300 430, 560 660, 860 510 S 1320 350, 1480 430" stroke="url(#hero-gold)" strokeWidth="1" fill="none" opacity=".6" />
        <path className="hero-line" d="M-40 120 C 240 200, 460 40, 760 120 S 1240 260, 1480 140" stroke="url(#hero-gold)" strokeWidth=".8" fill="none" opacity=".45" />
      </svg>
      <Horseshoe className="hero-shoe pointer-events-none absolute top-16 -right-10 -z-10 hidden size-[340px] opacity-[0.12] lg:block" />

      <div className="mx-auto flex max-w-[1320px] flex-col items-center px-4 pt-14 pb-16 text-center sm:px-6 sm:pt-20 sm:pb-20">
        <span className="inline-flex items-center gap-2 rounded-full bg-white/90 px-3.5 py-1.5 text-[12px] font-medium text-platinum-600 ring-1 ring-platinum-200 backdrop-blur">
          <span className="size-1.5 rounded-full bg-gold-500 shadow-[0_0_0_4px_rgba(201,160,74,.18)]" />
          <span>
            <span ref={counter} className="font-bold text-gold-700">
              {formatCount(productCount)}
            </span>{" "}
            {t("pill")}
          </span>
        </span>
        <h1 className="mt-6 max-w-[860px] font-display text-[34px] leading-[1.08] font-medium tracking-[-0.01em] text-ink sm:text-[52px]">
          {t.rich("title", {
            accent: (chunks) => <span className="text-gold">{chunks}</span>,
          })}
        </h1>
        <p className="mt-5 max-w-[620px] text-[15px] leading-7 text-platinum-600 sm:text-[17px]">{t("subtitle")}</p>

        <div className="mt-9 w-full max-w-[820px]">
          <SearchBox size="hero" />
        </div>

        <div className="mt-5 flex flex-wrap items-center justify-center gap-2 text-[13px] text-platinum-500">
          <span>{tSearch("tryExamples")}</span>
          {EXAMPLES.map((q) => (
            <Link
              key={q}
              href={`/search?q=${encodeURIComponent(q)}`}
              className="rounded-full bg-white px-3 py-1 font-medium text-platinum-700 ring-1 ring-platinum-200 transition hover:text-ink hover:ring-gold-400"
            >
              {q}
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
