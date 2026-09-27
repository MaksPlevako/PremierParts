"use client";

import { BadgeCheck, CarFront, Search } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useRef } from "react";

import { LogoMark } from "@/components/brand/Logo";
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
    let cancelled = false;
    let cleanup = () => {};
    // anime.js is only needed for this decorative intro, so it is loaded after first paint
    import("animejs").then(({ animate, stagger, svg }) => {
      if (cancelled) return;
      const lines = animate(svg.createDrawable(el.querySelectorAll(".hero-line")), {
        draw: ["0 0", "0 1"],
        ease: "inOutQuad",
        duration: 2200,
        delay: stagger(160, { start: 200 }),
      });
      const visual = animate(el.querySelectorAll(".hero-visual"), {
        opacity: [0, 1],
        translateX: [28, 0],
        duration: 1300,
        ease: "outExpo",
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
      cleanup = () => {
        lines.revert();
        visual.revert();
        count.pause();
      };
    });
    return () => {
      cancelled = true;
      cleanup();
    };
  }, [productCount]);

  return (
    <section ref={root} className="relative z-20 bg-platinum">
      {/* decorative layer is clipped on its own so the search dropdown can overflow the hero */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      {/* metallic sheen */}
      <div className="absolute -top-72 left-1/2 h-[620px] w-[1100px] -translate-x-1/2 rounded-full bg-[conic-gradient(from_200deg,#d7dbe0,#ffffff,#c9ced4,#f4f5f7,#d7dbe0)] opacity-90 blur-3xl" />
      {/* golden curves */}
      <svg
        className="absolute inset-0 h-full w-full"
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
      </div>

      <div className="relative mx-auto grid max-w-[1320px] items-center gap-10 px-4 pt-14 pb-16 sm:px-6 sm:pt-20 sm:pb-20 lg:grid-cols-[minmax(0,1fr)_400px] lg:gap-12 lg:pt-16 lg:pb-20">
        <div className="flex min-w-0 flex-col items-center text-center lg:items-start lg:text-left">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/90 px-3.5 py-1.5 text-[12px] font-medium text-platinum-600 ring-1 ring-platinum-200 backdrop-blur">
            <span className="size-1.5 rounded-full bg-gold-500 shadow-[0_0_0_4px_rgba(201,160,74,.18)]" />
            <span>
              <span ref={counter} className="font-bold text-gold-700">
                {formatCount(productCount)}
              </span>{" "}
              {t("pill")}
            </span>
          </span>
          <h1 className="mt-6 max-w-[860px] font-display text-[34px] leading-[1.08] font-medium tracking-[-0.01em] text-ink sm:text-[52px] lg:text-[50px] xl:text-[56px]">
            {t.rich("title", {
              accent: (chunks) => <span className="text-gold">{chunks}</span>,
            })}
          </h1>
          <p className="mt-5 max-w-[620px] text-[15px] leading-7 text-platinum-600 sm:text-[17px]">{t("subtitle")}</p>

          <div className="mt-9 w-full max-w-[820px]">
            <SearchBox size="hero" />
          </div>

          <div className="mt-5 flex flex-wrap items-center justify-center gap-2 text-[13px] text-platinum-500 lg:justify-start">
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

        <div className="hero-visual pointer-events-none relative hidden h-[410px] lg:block" aria-hidden="true">
          <div className="absolute inset-y-4 left-3 right-0 overflow-hidden rounded-[32px] border border-white/10 bg-[radial-gradient(circle_at_76%_15%,rgba(231,197,115,.22),transparent_32%),linear-gradient(145deg,#252a30_0%,#111316_68%,#2e2618_115%)] shadow-[0_30px_70px_-32px_rgba(17,19,22,.75)]">
            <div className="absolute inset-0 opacity-[0.08] [background-image:linear-gradient(rgba(255,255,255,.35)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.35)_1px,transparent_1px)] [background-size:36px_36px] [mask-image:linear-gradient(to_bottom,black,transparent_78%)]" />
            <div className="absolute -right-16 -top-16 size-52 rounded-full border border-gold-300/25" />
            <div className="absolute -right-7 -top-7 size-32 rounded-full border border-gold-300/20" />

            <div className="absolute left-7 top-7 z-10 flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.07] px-3 py-1.5 text-[11px] font-semibold tracking-[0.08em] text-white/75 uppercase backdrop-blur-sm">
              <span className="size-1.5 rounded-full bg-gold-300 shadow-[0_0_12px_rgba(231,197,115,.8)]" />
              VIN · OEM · Артикул
            </div>

            <LogoMark tone="white" className="absolute left-1/2 top-[42%] size-[300px] -translate-x-1/2 -translate-y-1/2 object-contain drop-shadow-[0_20px_30px_rgba(0,0,0,.35)]" />

            <div className="absolute inset-x-0 bottom-0 border-t border-white/10 bg-black/20 p-6 backdrop-blur-md">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className="text-[11px] font-semibold tracking-[0.12em] text-gold-300 uppercase">Точний підбір</p>
                  <p className="mt-1.5 max-w-[220px] text-[18px] leading-6 font-semibold text-white">Деталь саме для вашого авто</p>
                </div>
                <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-gold text-ink shadow-gold">
                  <CarFront className="size-5" strokeWidth={1.8} />
                </div>
              </div>
            </div>
          </div>

          <div className="absolute left-0 top-[92px] flex items-center gap-3 rounded-2xl bg-white/95 px-4 py-3 shadow-[0_16px_36px_-18px_rgba(21,24,28,.55)] ring-1 ring-platinum-200 backdrop-blur">
            <span className="flex size-9 items-center justify-center rounded-xl bg-gold-50 text-gold-700">
              <Search className="size-4" strokeWidth={2} />
            </span>
            <span>
              <span className="block text-[11px] text-platinum-500">Пошук за номером</span>
              <span className="mt-0.5 block text-[13px] font-semibold text-ink">VIN або OEM</span>
            </span>
          </div>

          <div className="absolute -right-3 bottom-[82px] flex items-center gap-2 rounded-full bg-white px-3.5 py-2 text-[12px] font-semibold text-ink shadow-[0_14px_30px_-16px_rgba(21,24,28,.65)] ring-1 ring-platinum-200">
            <BadgeCheck className="size-4 text-gold-600" strokeWidth={2} />
            Сумісність перевірено
          </div>
        </div>
      </div>
    </section>
  );
}
