"use client";

import { ArrowRight, Car, Check, MessageSquareText, Sparkles } from "lucide-react";
import Image from "next/image";
import { useTranslations } from "next-intl";
import type { ReactNode } from "react";

import { Link } from "@/i18n/navigation";
import { cn, formatPrice } from "@/lib/format";
import type { CarRef, ProductCard, Suggest, UnderstoodCar } from "@/lib/types";
import { useMyCar } from "@/stores/my-car";

interface Props {
  q: string;
  data: Suggest | null;
  loading: boolean;
  activeIndex: number;
  optionId: (i: number) => string;
  onNavigate: (href: string) => void;
}

function highlight(text: string, q: string): ReactNode {
  const words = q
    .split(/\s+/)
    .map((w) => w.replace(/[^\p{L}\p{N}]/gu, ""))
    .filter((w) => w.length >= 2);
  if (!words.length) return text;
  const re = new RegExp(`(${words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "giu");
  return text.split(re).map((part, i) =>
    i % 2 === 1 ? (
      <mark key={i} className="rounded-[3px] bg-gold-200/70 px-0.5 text-inherit">
        {part}
      </mark>
    ) : (
      part
    ),
  );
}

function isCarRef(car: CarRef | UnderstoodCar | null | undefined): car is CarRef {
  return Boolean(car && "generation_id" in car && car.generation_id);
}

function ProductRow({
  p,
  q,
  index,
  active,
  optionId,
  onNavigate,
  badge,
}: {
  p: ProductCard;
  q: string;
  index: number;
  active: boolean;
  optionId: (i: number) => string;
  onNavigate: (href: string) => void;
  badge?: ReactNode;
}) {
  const t = useTranslations();
  const price = p.sale_price ?? p.price;
  return (
    <button
      type="button"
      id={optionId(index)}
      role="option"
      aria-selected={active}
      onClick={() => onNavigate(`/product/${p.slug}`)}
      className={cn(
        "flex w-full items-center gap-3 rounded-[14px] p-2 text-left transition-colors",
        active ? "bg-platinum-100" : "hover:bg-platinum-50",
        p.exact && "bg-platinum-50 ring-1 ring-platinum-200",
      )}
    >
      <span className="relative h-12 w-16 shrink-0 overflow-hidden rounded-[10px] bg-platinum-100">
        {p.image && <Image src={p.image} alt="" fill sizes="64px" className="object-cover" />}
      </span>
      <span className="min-w-0 flex-1">
        {badge}
        <span className="block truncate text-[13.5px] font-semibold text-ink">{highlight(p.name, q)}</span>
        <span className="block truncate text-[12px] text-platinum-500">
          {[p.manufacturer, p.sku && `${t("common.sku")} ${p.sku}`].filter(Boolean).join(" · ")}
        </span>
      </span>
      <span className="shrink-0 text-right">
        <span className={cn("block font-display text-[14px] font-medium", !price && "text-[12px] text-platinum-500")}>
          {formatPrice(price, t("common.priceOnRequest"))}
        </span>
        <span
          className={cn(
            "text-[11px] font-bold",
            p.stock_status === "in_stock" ? "text-success" : "text-warning",
          )}
        >
          ● {t(`stock.${p.stock_status}`)}
        </span>
      </span>
    </button>
  );
}

function VinCard({ data, onNavigate }: { data: Suggest; onNavigate: (href: string) => void }) {
  const t = useTranslations("search");
  const setCar = useMyCar((s) => s.setCar);
  const vin = data.vin;
  const car = isCarRef(data.car) ? data.car : null;
  const carHref = car ? `/cars/${car.make_slug}/${car.model_slug}/${car.generation_slug}` : null;

  return (
    <div className="flex flex-col gap-3 p-4">
      {car ? (
        <div className="flex flex-col gap-4 rounded-[16px] bg-lux p-4 text-white sm:flex-row sm:items-center">
          <span className="grid size-12 shrink-0 place-items-center rounded-[12px] bg-gold-300/15 text-gold-300">
            <Car className="size-6" />
          </span>
          <div className="min-w-0 flex-1">
            <span className="block text-[12px] text-platinum-300">{t("yourCar")}</span>
            <span className="block font-display text-[16px] font-medium">
              {car.make} {car.label}
            </span>
            <span className="block text-[12px] text-platinum-300">
              {[vin?.year, vin?.body, vin?.engine, vin?.country].filter(Boolean).join(" · ")}
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => {
                setCar(car);
                if (carHref) onNavigate(carHref);
              }}
              className="inline-flex h-10 items-center gap-1.5 rounded-[11px] bg-gold px-4 text-[13px] font-bold text-[#1e1606]"
            >
              {data.total ? t("showParts", { count: data.total }) : t("makeMyCar")}
            </button>
          </div>
        </div>
      ) : (
        <div className="rounded-[16px] bg-platinum-50 p-4">
          <p className="font-semibold">{vin?.make ? `${vin.make} ${vin.model ?? ""} ${vin.year ?? ""}` : t("vinUnknownCar")}</p>
          <p className="mt-1 text-[13px] text-platinum-600">{t("vinNotSureText")}</p>
        </div>
      )}
      {data.categories.length > 0 && car && (
        <div className="flex flex-wrap gap-2">
          {data.categories.map((c) => (
            <Link
              key={c.id}
              href={`${carHref}?category=${c.slug}`}
              onClick={() => setCar(car)}
              className="rounded-[10px] bg-platinum-100 px-3 py-1.5 text-[13px] font-semibold hover:bg-platinum-200"
            >
              {c.name} <span className="font-normal text-platinum-500">{c.count}</span>
            </Link>
          ))}
        </div>
      )}
      <VinCta vin={vin?.vin} onNavigate={onNavigate} />
    </div>
  );
}

function VinCta({ vin, onNavigate }: { vin?: string; onNavigate: (href: string) => void }) {
  const t = useTranslations("search");
  return (
    <div className="flex items-center gap-3 rounded-[14px] border border-dashed border-gold-300/70 px-3 py-2.5 text-[13px] text-platinum-600">
      <MessageSquareText className="size-4 shrink-0 text-gold-700" />
      <span className="min-w-0 flex-1">
        <b className="text-ink">{t("vinNotSure")}</b> {t("vinNotSureText")}
      </span>
      <button
        type="button"
        onClick={() => onNavigate(`/vin${vin ? `?vin=${vin}` : ""}#request`)}
        className="shrink-0 rounded-[9px] bg-ink px-3 py-2 text-[12px] font-bold text-white"
      >
        {t("vinRequest")}
      </button>
    </div>
  );
}

export function SuggestPanel({ q, data, loading, activeIndex, optionId, onNavigate }: Props) {
  const t = useTranslations("search");

  if (loading || !data) {
    return (
      <div className="flex flex-col gap-2 p-4">
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex items-center gap-3">
            <div className="h-12 w-16 animate-pulse rounded-[10px] bg-platinum-100" />
            <div className="flex-1 space-y-2">
              <div className="h-3 w-3/4 animate-pulse rounded bg-platinum-100" />
              <div className="h-3 w-1/3 animate-pulse rounded bg-platinum-100" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (data.kind === "vin") return <VinCard data={data} onNavigate={onNavigate} />;

  const understood = data.understood;
  const exact = data.products.filter((p) => p.exact);
  const rest = data.products.filter((p) => !p.exact);
  const analogs = data.analogs ?? [];
  let index = 0;

  if (!data.products.length && !analogs.length) {
    return (
      <div className="flex flex-col gap-3 p-5">
        <p className="font-semibold">{t("nothing", { q })}</p>
        <p className="text-[13px] text-platinum-600">{t("nothingHint")}</p>
        <VinCta onNavigate={onNavigate} />
      </div>
    );
  }

  return (
    <div className="flex max-h-[min(70vh,620px)] flex-col gap-1 overflow-y-auto p-3">
      {understood && (understood.category || understood.car) && (
        <div className="flex flex-wrap items-center gap-2 px-2 pt-1 pb-2 text-[13px] text-platinum-600">
          <Sparkles className="size-4 text-gold-600" />
          {t("understood")}
          {understood.category && (
            <span className="rounded-[9px] bg-gold-100 px-2.5 py-1 font-semibold text-gold-800">{understood.category.name}</span>
          )}
          {understood.category && understood.car && <span>+</span>}
          {understood.car && (
            <span className="inline-flex items-center gap-1.5 rounded-[9px] bg-ink px-2.5 py-1 font-semibold text-white">
              <Car className="size-3.5" />
              {"full_label" in understood.car && understood.car.full_label
                ? understood.car.full_label
                : `${understood.car.make} ${understood.car.label}`}
            </span>
          )}
          <span>· {data.total}</span>
        </div>
      )}
      {data.relaxed && <p className="px-2 pb-1 text-[12px] font-medium text-warning">{t("relaxed")}</p>}

      {exact.map((p) => (
        <ProductRow
          key={p.id}
          p={p}
          q={q}
          index={index}
          active={activeIndex === index++}
          optionId={optionId}
          onNavigate={onNavigate}
          badge={
            <span className="mb-1 inline-flex items-center gap-1 rounded-md bg-success-soft px-1.5 py-0.5 text-[10.5px] font-extrabold text-success">
              <Check className="size-3" /> {t("exact").toUpperCase()}
            </span>
          }
        />
      ))}
      {analogs.length > 0 && (
        <p className="px-2 pt-2 text-[10.5px] font-bold tracking-[0.18em] text-platinum-400">{t("analogs").toUpperCase()}</p>
      )}
      {analogs.map((p) => (
        <ProductRow key={p.id} p={p} q={q} index={index} active={activeIndex === index++} optionId={optionId} onNavigate={onNavigate} />
      ))}
      {rest.map((p) => (
        <ProductRow key={p.id} p={p} q={q} index={index} active={activeIndex === index++} optionId={optionId} onNavigate={onNavigate} />
      ))}

      <div className="mt-1 flex flex-wrap items-center gap-2 border-t border-platinum-100 px-1 pt-3">
        <button
          type="button"
          id={optionId(index)}
          role="option"
          aria-selected={activeIndex === index}
          onClick={() => onNavigate(`/search?q=${encodeURIComponent(q)}`)}
          className={cn(
            "inline-flex items-center gap-1.5 rounded-[10px] px-3 py-1.5 text-[13px] font-bold",
            activeIndex === index ? "bg-ink text-white" : "bg-platinum-100 text-ink hover:bg-platinum-200",
          )}
        >
          {t("allResults", { count: data.total })}
        </button>
        {data.categories.slice(0, 4).map((c) => (
          <Link
            key={c.id}
            href={`/search?q=${encodeURIComponent(q)}&category=${c.slug}`}
            className="inline-flex items-center gap-1 rounded-[10px] px-2.5 py-1.5 text-[13px] font-medium text-platinum-700 hover:bg-platinum-50"
          >
            {c.name} <span className="text-platinum-400">{c.count}</span>
            <ArrowRight className="size-3 text-platinum-400" />
          </Link>
        ))}
      </div>
    </div>
  );
}
