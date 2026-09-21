"use client";

import { Hash, Loader2, ScanLine, Search, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";

import { useRouter } from "@/i18n/navigation";
import { browserApi } from "@/lib/browser-api";
import { cn } from "@/lib/format";
import type { Suggest } from "@/lib/types";
import { looksLikeVin } from "@/lib/vin";
import { useMyCar } from "@/stores/my-car";

import { SuggestPanel } from "./SuggestPanel";

interface Props {
  size?: "hero" | "header";
  autoFocus?: boolean;
  placeholder?: string;
  className?: string;
  initialQuery?: string;
}

export function SearchBox({ size = "header", autoFocus, placeholder, className, initialQuery = "" }: Props) {
  const t = useTranslations("search");
  const tHeader = useTranslations("header");
  const router = useRouter();
  const car = useMyCar((s) => s.car);
  const listId = useId();
  const root = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLInputElement>(null);

  const [q, setQ] = useState(initialQuery);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<Suggest | null>(null);
  const [active, setActive] = useState(-1);

  const trimmed = q.trim();
  const isVin = looksLikeVin(trimmed);

  useEffect(() => {
    if (trimmed.length < 2) return;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true);
      browserApi
        .suggest(trimmed, car?.generation_id, controller.signal)
        .then((res) => {
          setData(res);
          setActive(-1);
        })
        .catch(() => {})
        .finally(() => !controller.signal.aborted && setLoading(false));
    }, isVin ? 0 : 140);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [trimmed, car?.generation_id, isVin]);

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (root.current && !root.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  const hrefs = useMemo(() => {
    if (!data) return [] as string[];
    const list = [...(data.products ?? []), ...(data.analogs ?? [])].map((p) => `/product/${p.slug}`);
    if (trimmed) list.push(`/search?q=${encodeURIComponent(trimmed)}`);
    return list;
  }, [data, trimmed]);

  const go = useCallback(
    (href: string) => {
      setOpen(false);
      input.current?.blur();
      router.push(href);
    },
    [router],
  );

  const submit = () => {
    if (!trimmed) return;
    if (active >= 0 && hrefs[active]) return go(hrefs[active]);
    if (isVin) return go(`/vin?vin=${encodeURIComponent(trimmed)}`);
    go(`/search?q=${encodeURIComponent(trimmed)}`);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpen(true);
      setActive((i) => Math.min(i + 1, hrefs.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, -1));
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const hero = size === "hero";
  const badge = isVin ? (
    <span className="hidden items-center gap-1.5 rounded-[10px] bg-gold-100 px-2.5 py-1.5 text-[11.5px] font-bold text-gold-800 sm:inline-flex">
      <ScanLine className="size-3.5" /> {t("detectedVin")}
    </span>
  ) : data?.kind === "part_number" ? (
    <span className="hidden items-center gap-1.5 rounded-[10px] bg-gold-100 px-2.5 py-1.5 text-[11.5px] font-bold text-gold-800 sm:inline-flex">
      <Hash className="size-3.5" /> {t("detectedNumber")}
    </span>
  ) : null;

  const showPanel = open && trimmed.length >= 2 && (data || loading);

  return (
    <div ref={root} className={cn("relative w-full", className)}>
      <form
        role="search"
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className={cn(
          "relative flex items-center gap-2 bg-white transition-shadow",
          hero
            ? "rounded-[22px] p-2 pl-5 shadow-float focus-within:shadow-[0_1px_0_#fff_inset,0_28px_70px_-26px_rgba(20,30,45,.45),0_0_0_2px_#d9b45e]"
            : "h-11 rounded-[14px] pr-1 pl-3.5 ring-1 ring-platinum-200 focus-within:ring-2 focus-within:ring-gold-400",
        )}
      >
        {loading ? (
          <Loader2 className={cn("shrink-0 animate-spin text-gold-600", hero ? "size-5" : "size-4")} />
        ) : (
          <Search className={cn("shrink-0 text-gold-600", hero ? "size-5" : "size-4")} />
        )}
        <input
          ref={input}
          value={q}
          autoFocus={autoFocus}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder={placeholder ?? (hero ? t("heroPlaceholder") : tHeader("searchPlaceholder"))}
          role="combobox"
          aria-expanded={Boolean(showPanel)}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={active >= 0 ? `${listId}-${active}` : undefined}
          autoComplete="off"
          spellCheck={false}
          enterKeyHint="search"
          className={cn(
            "min-w-0 flex-1 bg-transparent font-medium text-ink outline-none placeholder:font-normal placeholder:text-platinum-400",
            hero ? "h-12 text-[16px] sm:text-[17px]" : "h-full text-[14px]",
          )}
        />
        {q && (
          <button
            type="button"
            onClick={() => {
              setQ("");
              setData(null);
              input.current?.focus();
            }}
            className="grid size-8 shrink-0 place-items-center rounded-full text-platinum-400 hover:bg-platinum-100 hover:text-ink"
            aria-label="Очистити"
          >
            <X className="size-4" />
          </button>
        )}
        {badge}
        <button
          type="submit"
          className={cn(
            "shrink-0 font-semibold transition-colors",
            hero
              ? "inline-flex h-12 items-center gap-2 rounded-[15px] bg-ink px-5 text-white hover:bg-graphite-700 sm:px-7"
              : "grid size-9 place-items-center rounded-[11px] bg-ink text-white hover:bg-graphite-700",
          )}
          aria-label={t("submit")}
        >
          {hero ? (
            <>
              <Search className="size-4 sm:hidden" />
              <span className="hidden sm:inline">{t("submit")}</span>
            </>
          ) : (
            <Search className="size-4" />
          )}
        </button>
      </form>

      <AnimatePresence>
        {showPanel && (
          <motion.div
            id={listId}
            role="listbox"
            initial={{ opacity: 0, y: -6, scale: 0.99 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.99 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            className={cn(
              "absolute inset-x-0 z-50 mt-2 overflow-hidden rounded-[20px] bg-white text-left shadow-float",
              hero ? "top-full" : "top-full min-w-[min(640px,92vw)]",
            )}
          >
            <SuggestPanel
              q={trimmed}
              data={data}
              loading={loading && !data}
              activeIndex={active}
              optionId={(i) => `${listId}-${i}`}
              onNavigate={go}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
