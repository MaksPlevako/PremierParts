"use client";

import { ChevronRight, Phone } from "lucide-react";
import { useTranslations } from "next-intl";

import { Logo } from "@/components/brand/Logo";
import { CategoryIcon } from "@/components/catalog/CategoryIcon";
import { Dialog } from "@/components/ui/Dialog";
import { Link } from "@/i18n/navigation";
import { formatPhoneHref } from "@/lib/format";
import type { CategoryNode, Phone as PhoneT } from "@/lib/types";

interface Props {
  open: boolean;
  onClose: () => void;
  categories: CategoryNode[];
  nav: { href: string; label: string; hot?: boolean }[];
  phone: PhoneT | null;
}

export function MobileNav({ open, onClose, categories, nav, phone }: Props) {
  const t = useTranslations();
  return (
    <Dialog open={open} onClose={onClose} variant="side" title={<Logo />}>
      <div className="flex flex-col gap-6 p-5">
        <section>
          <p className="mb-2 text-[11px] font-bold tracking-[0.2em] text-platinum-400">{t("common.catalog").toUpperCase()}</p>
          <ul className="flex flex-col">
            {categories.map((c) => (
              <li key={c.id}>
                <Link
                  href={`/category/${c.slug}`}
                  onClick={onClose}
                  className="flex items-center gap-3 rounded-xl px-2 py-2.5 font-semibold hover:bg-platinum-50"
                >
                  <span className="grid size-9 place-items-center rounded-[10px] bg-ink text-gold-300">
                    <CategoryIcon name={c.icon} className="size-5" />
                  </span>
                  <span className="flex-1">{c.name}</span>
                  <ChevronRight className="size-4 text-platinum-400" />
                </Link>
              </li>
            ))}
          </ul>
        </section>
        <section className="flex flex-col">
          {nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              className={`rounded-xl px-2 py-2.5 text-[15px] font-medium hover:bg-platinum-50 ${item.hot ? "text-gold-700" : ""}`}
            >
              {item.label}
            </Link>
          ))}
        </section>
        {phone && (
          <a
            href={formatPhoneHref(phone.number)}
            className="flex items-center justify-center gap-2 rounded-2xl bg-ink py-3.5 font-semibold text-white"
          >
            <Phone className="size-4 text-gold-300" />
            {phone.label}
          </a>
        )}
      </div>
    </Dialog>
  );
}
