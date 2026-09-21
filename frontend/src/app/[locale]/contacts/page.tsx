import { Clock, Mail, MapPin, Phone } from "lucide-react";
import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { getSettingsSafe } from "@/lib/api";
import { formatPhoneHref } from "@/lib/format";
import { JsonLd, storeJsonLd } from "@/lib/seo";

export const metadata: Metadata = { title: "Контакти", alternates: { canonical: "/contacts" } };

export default async function ContactsPage({ params }: PageProps<"/[locale]/contacts">) {
  const { locale } = await params;
  setRequestLocale(locale);
  const [s, t] = await Promise.all([getSettingsSafe(), getTranslations("contacts")]);

  const cards = [
    {
      icon: Phone,
      title: t("phones"),
      body: (
        <div className="flex flex-col gap-1">
          {s?.phones.map((p) => (
            <a key={p.number} href={formatPhoneHref(p.number)} className="font-display text-[18px] font-medium hover:text-gold-800">
              {p.label} {p.viber && <span className="text-[12px] font-sans text-[#7360f2]">Viber</span>}
            </a>
          ))}
        </div>
      ),
    },
    { icon: Mail, title: t("email"), body: <a href={`mailto:${s?.email}`} className="font-semibold hover:text-gold-800">{s?.email}</a> },
    { icon: MapPin, title: t("address"), body: <p className="font-semibold">{s?.address}</p> },
    { icon: Clock, title: t("hours"), body: <p className="font-semibold">{s?.work_hours}</p> },
  ];

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <JsonLd data={storeJsonLd(s)} />
      <Breadcrumbs items={[{ name: t("title") }]} />
      <h1 className="mt-4 font-display text-[30px] font-medium sm:text-[38px]">{t("title")}</h1>
      <p className="mt-2 text-[15px] text-platinum-600">{t("subtitle")}</p>
      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_1.4fr]">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
          {cards.map(({ icon: Icon, title, body }) => (
            <div key={title} className="flex gap-4 rounded-[22px] bg-white p-5 ring-1 ring-platinum-200">
              <span className="grid size-11 shrink-0 place-items-center rounded-[13px] bg-ink text-gold-300">
                <Icon className="size-5" />
              </span>
              <div>
                <p className="mb-1 text-[12px] font-bold tracking-[0.16em] text-platinum-400 uppercase">{title}</p>
                {body}
              </div>
            </div>
          ))}
          {s?.pickup_note && (
            <p className="rounded-[18px] bg-gold-50 p-4 text-[13.5px] text-platinum-700 ring-1 ring-gold-200">
              <b className="text-ink">{t("pickup")}:</b> {s.pickup_note}.
            </p>
          )}
        </div>
        <div className="min-h-[420px] overflow-hidden rounded-[26px] ring-1 ring-platinum-200">
          {s?.map_embed_url ? (
            <iframe title="Карта" src={s.map_embed_url} className="h-full min-h-[420px] w-full grayscale-[35%]" loading="lazy" referrerPolicy="no-referrer-when-downgrade" />
          ) : (
            <div className="grid h-full place-items-center bg-platinum-50 text-platinum-400">Карта</div>
          )}
        </div>
      </div>
    </div>
  );
}
