"use client";

import { Check, Copy } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import type { ProductDetail } from "@/lib/types";

const KIND: Record<string, string> = { sku: "Артикул", oem: "OEM", cross: "Крос" };

export function PartNumbers({ numbers }: { numbers: ProductDetail["part_numbers"] }) {
  const t = useTranslations("product");
  const [copied, setCopied] = useState<string | null>(null);
  if (!numbers.length) return null;
  return (
    <div className="flex flex-wrap gap-2">
      {numbers.map((n) => (
        <button
          key={`${n.kind}-${n.number}`}
          type="button"
          onClick={() => {
            navigator.clipboard?.writeText(n.number);
            setCopied(n.number);
            setTimeout(() => setCopied(null), 1500);
          }}
          className="group inline-flex items-center gap-2 rounded-[11px] bg-platinum-50 px-3 py-2 ring-1 ring-platinum-200 transition hover:ring-gold-400"
          title={t("copy")}
        >
          <span className="text-[10.5px] font-bold tracking-wider text-platinum-400 uppercase">{KIND[n.kind]}</span>
          <span className="font-mono text-[13.5px] font-semibold tracking-wide text-ink">{n.number}</span>
          {copied === n.number ? <Check className="size-3.5 text-success" /> : <Copy className="size-3.5 text-platinum-400 group-hover:text-gold-600" />}
        </button>
      ))}
    </div>
  );
}
