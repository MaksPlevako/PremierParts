import { CheckCircle2 } from "lucide-react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";

import { Link } from "@/i18n/navigation";
import { getOrder, getSettingsSafe } from "@/lib/api";
import { formatPrice } from "@/lib/format";

export const metadata: Metadata = { title: "Замовлення прийнято", robots: { index: false } };

export default async function SuccessPage({ params, searchParams }: PageProps<"/[locale]/checkout/success/[number]">) {
  const { locale, number } = await params;
  setRequestLocale(locale);
  const { token } = await searchParams;
  const [order, settings, t] = await Promise.all([
    typeof token === "string" ? getOrder(number, token) : null,
    getSettingsSafe(),
    getTranslations(),
  ]);
  if (!order) notFound();

  return (
    <div className="mx-auto max-w-[920px] px-4 pt-10 sm:px-6">
      <div className="flex flex-col items-center gap-4 rounded-[28px] bg-lux px-6 py-12 text-center text-white">
        <span className="grid size-16 place-items-center rounded-full bg-gold text-[#1e1606] shadow-gold">
          <CheckCircle2 className="size-8" />
        </span>
        <h1 className="font-display text-[26px] font-medium sm:text-[32px]">{t("checkout.success", { number: order.number })}</h1>
        <p className="max-w-lg text-[15px] text-platinum-300">{t("checkout.successText")}</p>
      </div>

      <div className="mt-6 grid gap-6 md:grid-cols-[1.3fr_1fr]">
        <section className="rounded-[24px] bg-white p-6 ring-1 ring-platinum-200">
          <h2 className="mb-4 font-display text-[18px] font-medium">{t("checkout.summary")}</h2>
          <ul className="divide-y divide-platinum-100">
            {order.items.map((item) => (
              <li key={`${item.sku}-${item.name}`} className="flex justify-between gap-4 py-3 text-[14px]">
                <span className="min-w-0">
                  {item.slug ? (
                    <Link href={`/product/${item.slug}`} className="font-semibold hover:text-gold-800">
                      {item.name}
                    </Link>
                  ) : (
                    <span className="font-semibold">{item.name}</span>
                  )}
                  <span className="block text-[12px] text-platinum-500">
                    {item.sku} · {item.qty} шт.
                  </span>
                </span>
                <span className="shrink-0 font-display">{formatPrice(item.line_total, t("common.priceOnRequest"))}</span>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex items-baseline justify-between border-t border-platinum-100 pt-4">
            <span className="font-semibold">{t("cart.total")}</span>
            <span className="font-display text-[24px] font-medium">{formatPrice(order.total, "—")}</span>
          </div>
          <dl className="mt-5 grid gap-2 rounded-[16px] bg-platinum-50 p-4 text-[13.5px]">
            <div className="flex justify-between gap-4">
              <dt className="text-platinum-500">{t("checkout.delivery")}</dt>
              <dd className="text-right font-semibold">
                {order.delivery_label}
                {order.city && `, ${order.city}`}
                {order.np_branch && `, ${order.np_branch}`}
              </dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-platinum-500">{t("checkout.payment")}</dt>
              <dd className="text-right font-semibold">{order.payment_label}</dd>
            </div>
            {order.car && (
              <div className="flex justify-between gap-4">
                <dt className="text-platinum-500">{t("checkout.car")}</dt>
                <dd className="text-right font-semibold">{order.car.full_label}</dd>
              </div>
            )}
          </dl>
        </section>

        <div className="flex flex-col gap-6">
          <section className="rounded-[24px] bg-white p-6 ring-1 ring-platinum-200">
            <h2 className="mb-4 font-display text-[18px] font-medium">{t("checkout.next")}</h2>
            <ol className="flex flex-col gap-4">
              {[t("checkout.step1"), t("checkout.step2"), t("checkout.step3")].map((step, i) => (
                <li key={step} className="flex gap-3 text-[14px]">
                  <span className="grid size-7 shrink-0 place-items-center rounded-full bg-ink font-display text-[12px] text-gold-300">{i + 1}</span>
                  {step}
                </li>
              ))}
            </ol>
          </section>
          {order.payment_method === "iban" && settings?.iban_details && (
            <section className="rounded-[24px] bg-gold-50 p-6 ring-1 ring-gold-200">
              <h2 className="mb-3 font-display text-[16px] font-medium">{t("checkout.payDetails")}</h2>
              <pre className="font-sans text-[13.5px] leading-6 whitespace-pre-wrap text-platinum-700">
                {settings.iban_details.replace("{номер}", order.number)}
              </pre>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
