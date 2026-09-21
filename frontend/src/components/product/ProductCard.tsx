import Image from "next/image";
import { useTranslations } from "next-intl";

import { FitBadge } from "@/components/car/FitBadge";
import { Link } from "@/i18n/navigation";
import { cn, formatPrice } from "@/lib/format";
import type { ProductCard as Card } from "@/lib/types";

import { AddToCartButton } from "./AddToCartButton";

export function ProductCard({ product, priority = false }: { product: Card; priority?: boolean }) {
  const t = useTranslations();
  const price = product.sale_price ?? product.price;
  const href = `/product/${product.slug}`;

  return (
    <article className="group relative flex flex-col rounded-[20px] bg-white p-2 ring-1 ring-platinum-200 transition-[box-shadow,transform] duration-300 ease-[var(--ease-lux)] hover:-translate-y-0.5 hover:shadow-[0_22px_50px_-28px_rgba(21,24,28,.45)] hover:ring-platinum-300">
      <Link href={href} className="relative block aspect-[4/3] overflow-hidden rounded-[14px] bg-platinum-100">
        {product.image ? (
          <Image
            src={product.image}
            alt={product.name}
            fill
            sizes="(min-width: 1280px) 290px, (min-width: 768px) 30vw, 50vw"
            preload={priority}
            className="object-cover transition-transform duration-700 ease-[var(--ease-lux)] group-hover:scale-[1.04]"
          />
        ) : (
          <span className="grid h-full place-items-center text-[12px] text-platinum-400">Premier Parts</span>
        )}
        <span className="absolute top-2 left-2 flex flex-col items-start gap-1">
          {product.discount_percent ? (
            <span className="rounded-full bg-ink px-2 py-0.5 text-[11px] font-bold text-gold-200">−{product.discount_percent}%</span>
          ) : null}
          <span
            className={cn(
              "rounded-full bg-white/92 px-2 py-0.5 text-[10.5px] font-bold backdrop-blur",
              product.stock_status === "in_stock" ? "text-success" : "text-warning",
            )}
          >
            ● {t(`stock.${product.stock_status}`)}
          </span>
        </span>
      </Link>
      <div className="flex flex-1 flex-col px-1.5 pt-3 pb-1">
        <div className="mb-1 flex h-4 items-center gap-2">
          <FitBadge generationIds={product.generation_ids} />
        </div>
        <Link href={href} className="line-clamp-2 min-h-[40px] text-[13.5px] leading-5 font-semibold text-ink hover:text-gold-800">
          {product.name}
        </Link>
        <p className="mt-1.5 truncate text-[12px] text-platinum-500">
          {[product.manufacturer, product.sku].filter(Boolean).join(" · ")}
        </p>
        <div className="mt-auto flex items-end justify-between gap-2 pt-3">
          <div className="min-w-0">
            {product.old_price && price ? (
              <span className="block text-[12px] text-platinum-400 line-through">{formatPrice(product.old_price)}</span>
            ) : null}
            <span className={cn("block font-display font-medium", price ? "text-[17px]" : "text-[12.5px] text-platinum-600")}>
              {formatPrice(price, t("common.priceOnRequest"))}
            </span>
          </div>
          <AddToCartButton product={product} compact />
        </div>
      </div>
    </article>
  );
}

export function ProductGrid({ products, className }: { products: Card[]; className?: string }) {
  return (
    <div className={cn("grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 xl:grid-cols-4", className)}>
      {products.map((p, i) => (
        <ProductCard key={p.id} product={p} priority={i < 4} />
      ))}
    </div>
  );
}
