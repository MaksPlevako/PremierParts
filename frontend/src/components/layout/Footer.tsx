import { Mail, MapPin, Phone } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { Logo } from "@/components/brand/Logo";
import { Link } from "@/i18n/navigation";
import { getPages } from "@/lib/api";
import { formatPhoneHref } from "@/lib/format";
import type { CategoryNode, SiteSettings } from "@/lib/types";

export async function Footer({ settings, categories }: { settings: SiteSettings | null; categories: CategoryNode[] }) {
  const t = await getTranslations();
  const pages = (await getPages().catch(() => null)) ?? [];

  return (
    <footer className="mt-24 bg-lux text-platinum-300">
      <div className="mx-auto grid max-w-[1320px] gap-10 px-6 py-14 md:grid-cols-2 lg:grid-cols-[1.4fr_1fr_1fr_1.2fr]">
        <div className="flex flex-col gap-4">
          <Logo tone="white" />
          {settings?.about_short && <p className="max-w-sm text-[13.5px] leading-6 text-platinum-400">{settings.about_short}</p>}
        </div>
        <div>
          <p className="mb-4 text-[11px] font-bold tracking-[0.22em] text-gold-300">{t("footer.catalog").toUpperCase()}</p>
          <ul className="flex flex-col gap-2 text-[14px]">
            {categories.map((c) => (
              <li key={c.id}>
                <Link href={`/category/${c.slug}`} className="hover:text-white">
                  {c.name}
                </Link>
              </li>
            ))}
            <li>
              <Link href="/cars" className="hover:text-white">
                {t("common.cars")}
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="mb-4 text-[11px] font-bold tracking-[0.22em] text-gold-300">{t("footer.info").toUpperCase()}</p>
          <ul className="flex flex-col gap-2 text-[14px]">
            {pages
              .filter((p) => p.show_in_footer && p.slug !== "grafik-roboti")
              .map((p) => (
                <li key={p.slug}>
                  <Link href={`/page/${p.slug}`} className="hover:text-white">
                    {p.title}
                  </Link>
                </li>
              ))}
            <li>
              <Link href="/promotions" className="hover:text-white">
                {t("common.promotions")}
              </Link>
            </li>
            <li>
              <Link href="/vin" className="hover:text-white">
                {t("common.vin")}
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="mb-4 text-[11px] font-bold tracking-[0.22em] text-gold-300">{t("footer.contacts").toUpperCase()}</p>
          <ul className="flex flex-col gap-3 text-[14px]">
            {settings?.phones.map((p) => (
              <li key={p.number}>
                <a href={formatPhoneHref(p.number)} className="inline-flex items-center gap-2 font-semibold text-white hover:text-gold-200">
                  <Phone className="size-4 text-gold-300" />
                  {p.label}
                  {p.viber && <span className="text-[11px] font-medium text-platinum-400">Viber</span>}
                </a>
              </li>
            ))}
            {settings?.email && (
              <li>
                <a href={`mailto:${settings.email}`} className="inline-flex items-center gap-2 hover:text-white">
                  <Mail className="size-4 text-gold-300" />
                  {settings.email}
                </a>
              </li>
            )}
            {settings?.address && (
              <li className="inline-flex items-start gap-2">
                <MapPin className="mt-0.5 size-4 shrink-0 text-gold-300" />
                <span>
                  {settings.address}
                  <br />
                  <span className="text-platinum-400">{settings.work_hours}</span>
                </span>
              </li>
            )}
          </ul>
        </div>
      </div>
      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-[1320px] flex-wrap items-center justify-between gap-3 px-6 py-5 text-[12.5px] text-platinum-400">
          <span>{t("footer.rights", { year: new Date().getFullYear() })}</span>
          {/* Django admin is not a Next.js route */}
          {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
          <a href="/admin/" className="hover:text-gold-200">
            {t("footer.admin")}
          </a>
        </div>
      </div>
    </footer>
  );
}
