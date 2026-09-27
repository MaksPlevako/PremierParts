"use client";

import { Banknote, Building2, Car, CreditCard, Loader2, MapPin, Package, Truck } from "lucide-react";
import Image from "next/image";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";
import { z } from "zod";

import { Link, useRouter } from "@/i18n/navigation";
import { browserApi } from "@/lib/browser-api";
import { cn, finalPrice, formatPrice } from "@/lib/format";
import { cartTotals, useCart } from "@/stores/cart";
import { useHydrated } from "@/lib/use-hydrated";
import { useMyCar } from "@/stores/my-car";

import { NpField } from "./NpField";
import { isValidPhone, PhoneInput } from "./PhoneInput";

type Delivery = "np_branch" | "np_courier" | "pickup" | "taxi";
type Payment = "iban" | "card_pickup" | "cash_pickup";

const DELIVERY: { key: Delivery; icon: typeof Truck }[] = [
  { key: "np_branch", icon: Package },
  { key: "np_courier", icon: Truck },
  { key: "pickup", icon: MapPin },
  { key: "taxi", icon: Car },
];

export function CheckoutForm() {
  const t = useTranslations();
  const router = useRouter();
  const { lines, clear } = useCart();
  const car = useMyCar((s) => s.car);
  const mounted = useHydrated();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("+380");
  const [email, setEmail] = useState("");
  const [delivery, setDelivery] = useState<Delivery>("np_branch");
  const [city, setCity] = useState("");
  const [branch, setBranch] = useState("");
  const [address, setAddress] = useState("");
  const [payment, setPayment] = useState<Payment>("iban");
  const [comment, setComment] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [sending, setSending] = useState(false);
  const [serverError, setServerError] = useState(false);

  useEffect(() => {
    browserApi.profile().then((profile) => {
      setName((value) => value || [profile.first_name, profile.last_name].filter(Boolean).join(" "));
      setPhone((value) => value === "+380" ? profile.phone || value : value);
      setEmail((value) => value || profile.email);
      setCity((value) => value || profile.city);
      setBranch((value) => value || profile.np_branch);
      setAddress((value) => value || profile.address);
    }).catch(() => undefined);
  }, []);

  const schema = useMemo(
    () =>
      z
        .object({
          customer_name: z.string().trim().min(2, t("checkout.required")),
          phone: z.string().refine(isValidPhone, t("checkout.phoneInvalid")),
          email: z.union([z.literal(""), z.email(t("checkout.required"))]),
          city: z.string(),
          np_branch: z.string(),
          address: z.string(),
        })
        .superRefine((v, ctx) => {
          if ((delivery === "np_branch" || delivery === "np_courier") && !v.city.trim())
            ctx.addIssue({ code: "custom", path: ["city"], message: t("checkout.required") });
          if (delivery === "np_branch" && !v.np_branch.trim())
            ctx.addIssue({ code: "custom", path: ["np_branch"], message: t("checkout.required") });
          if ((delivery === "np_courier" || delivery === "taxi") && !v.address.trim())
            ctx.addIssue({ code: "custom", path: ["address"], message: t("checkout.required") });
        }),
    [delivery, t],
  );

  if (!mounted) return <div className="h-96 animate-pulse rounded-[24px] bg-platinum-50" />;
  if (!lines.length) {
    return (
      <div className="rounded-[24px] bg-platinum-50 p-10 text-center ring-1 ring-platinum-200">
        <p className="font-display text-[20px] font-medium">{t("cart.empty")}</p>
        <Link href="/catalog" className="mt-4 inline-block font-semibold text-gold-700">
          {t("cart.toCatalog")} →
        </Link>
      </div>
    );
  }

  const totals = cartTotals(lines);

  const submit = async () => {
    const parsed = schema.safeParse({ customer_name: name, phone, email, city, np_branch: branch, address });
    if (!parsed.success) {
      const next: Record<string, string> = {};
      for (const issue of parsed.error.issues) next[String(issue.path[0])] = issue.message;
      setErrors(next);
      document.querySelector(`[data-field="${Object.keys(next)[0]}"]`)?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    setErrors({});
    setSending(true);
    setServerError(false);
    try {
      const res = await browserApi.createOrder({
        customer_name: name,
        phone,
        email,
        delivery_method: delivery,
        city: delivery === "pickup" || delivery === "taxi" ? "Київ" : city,
        np_branch: delivery === "np_branch" ? branch : "",
        address: delivery === "np_courier" || delivery === "taxi" ? address : "",
        payment_method: payment,
        comment,
        car_generation_id: car?.generation_id ?? null,
        items: lines.map((l) => ({ product_id: l.product.id, qty: l.qty })),
      });
      clear();
      router.push(`/checkout/success/${res.number}?token=${res.access_token}`);
    } catch (e) {
      const body = (e as { body?: Record<string, string[]> }).body ?? {};
      const next: Record<string, string> = {};
      for (const [k, v] of Object.entries(body)) if (Array.isArray(v)) next[k] = v[0];
      setErrors(next);
      setServerError(true);
      setSending(false);
    }
  };

  const field = "h-12 w-full rounded-[12px] px-4 ring-1 outline-none focus:ring-2 focus:ring-gold-400";
  const err = (k: string) => (errors[k] ? <p className="mt-1 text-[12.5px] text-danger">{errors[k]}</p> : null);
  const card = (active: boolean) =>
    cn(
      "flex items-start gap-3 rounded-[16px] p-4 text-left ring-1 transition",
      active ? "bg-platinum-50 ring-2 ring-gold-500" : "ring-platinum-200 hover:ring-gold-300",
    );
  const payments: { key: Payment; icon: typeof CreditCard; hint?: string }[] =
    delivery === "pickup"
      ? [
          { key: "iban", icon: Building2, hint: t("checkout.iban_hint") },
          { key: "card_pickup", icon: CreditCard },
          { key: "cash_pickup", icon: Banknote },
        ]
      : [{ key: "iban", icon: Building2, hint: t("checkout.iban_hint") }];

  return (
    <form
      className="grid gap-6 lg:grid-cols-[1fr_400px]"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
      noValidate
    >
      <div className="flex flex-col gap-6">
        <section className="rounded-[24px] bg-white p-6 ring-1 ring-platinum-200">
          <h2 className="mb-4 font-display text-[18px] font-medium">1. {t("checkout.contact")}</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-1.5 text-[13px] font-semibold" data-field="customer_name">
              {t("checkout.name")}
              <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" className={cn(field, errors.customer_name ? "ring-danger" : "ring-platinum-200")} />
              {err("customer_name")}
            </label>
            <label className="flex flex-col gap-1.5 text-[13px] font-semibold" data-field="phone">
              {t("checkout.phone")}
              <PhoneInput value={phone} onChange={setPhone} invalid={Boolean(errors.phone)} />
              {err("phone")}
            </label>
            <label className="flex flex-col gap-1.5 text-[13px] font-semibold sm:col-span-2" data-field="email">
              {t("checkout.email")}
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" className={cn(field, "ring-platinum-200")} />
              {err("email")}
            </label>
          </div>
        </section>

        <section className="rounded-[24px] bg-white p-6 ring-1 ring-platinum-200">
          <h2 className="mb-4 font-display text-[18px] font-medium">2. {t("checkout.delivery")}</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {DELIVERY.map(({ key, icon: Icon }) => (
              <button
                key={key}
                type="button"
                onClick={() => {
                  setDelivery(key);
                  if (key !== "pickup") setPayment("iban");
                }}
                className={card(delivery === key)}
              >
                <Icon className={cn("mt-0.5 size-5 shrink-0", delivery === key ? "text-gold-700" : "text-platinum-400")} />
                <span>
                  <span className="block text-[14px] font-semibold">{t(`checkout.${key}`)}</span>
                  <span className="text-[12.5px] text-platinum-500">{t(`checkout.${key}_hint`)}</span>
                </span>
              </button>
            ))}
          </div>
          <div className="mt-5 grid gap-4">
            {(delivery === "np_branch" || delivery === "np_courier") && (
              <NpField
                city={city}
                onCity={setCity}
                branch={branch}
                onBranch={setBranch}
                withBranch={delivery === "np_branch"}
                errors={errors}
                fieldClass={field}
              />
            )}
            {(delivery === "np_courier" || delivery === "taxi") && (
              <label className="flex flex-col gap-1.5 text-[13px] font-semibold" data-field="address">
                {t("checkout.address")}
                <input value={address} onChange={(e) => setAddress(e.target.value)} autoComplete="street-address" className={cn(field, errors.address ? "ring-danger" : "ring-platinum-200")} />
                {err("address")}
              </label>
            )}
            {delivery === "pickup" && (
              <p className="rounded-[14px] bg-platinum-50 p-4 text-[13.5px] text-platinum-700">
                <b className="text-ink">Київ, вул. Вікентія Беретті, 6Б</b> · Пн–Пт 10:00–18:00, за попереднім узгодженням. Завдаток 300 грн входить у вартість товару.
              </p>
            )}
          </div>
        </section>

        <section className="rounded-[24px] bg-white p-6 ring-1 ring-platinum-200">
          <h2 className="mb-4 font-display text-[18px] font-medium">3. {t("checkout.payment")}</h2>
          <div className="grid gap-3 sm:grid-cols-3">
            {payments.map(({ key, icon: Icon, hint }) => (
              <button key={key} type="button" onClick={() => setPayment(key)} className={card(payment === key)}>
                <Icon className={cn("mt-0.5 size-5 shrink-0", payment === key ? "text-gold-700" : "text-platinum-400")} />
                <span>
                  <span className="block text-[14px] font-semibold">{t(`checkout.${key}`)}</span>
                  {hint && <span className="text-[12.5px] text-platinum-500">{hint}</span>}
                </span>
              </button>
            ))}
          </div>
          <label className="mt-5 flex flex-col gap-1.5 text-[13px] font-semibold">
            {t("checkout.comment")}
            <textarea value={comment} onChange={(e) => setComment(e.target.value)} rows={3} className="rounded-[12px] px-4 py-3 ring-1 ring-platinum-200 outline-none focus:ring-2 focus:ring-gold-400" />
          </label>
        </section>
      </div>

      <aside className="h-fit rounded-[24px] bg-white p-6 ring-1 ring-platinum-200 lg:sticky lg:top-[92px]">
        <p className="font-display text-[18px] font-medium">{t("checkout.summary")}</p>
        <ul className="mt-4 flex max-h-72 flex-col gap-3 overflow-y-auto pr-1">
          {lines.map(({ product, qty }) => (
            <li key={product.id} className="flex gap-3">
              <span className="relative size-14 shrink-0 overflow-hidden rounded-[10px] bg-platinum-100">
                {product.image && <Image src={product.image} alt="" fill sizes="56px" className="object-cover" />}
              </span>
              <span className="min-w-0 flex-1">
                <span className="line-clamp-2 text-[13px] font-semibold">{product.name}</span>
                <span className="text-[12px] text-platinum-500">
                  {qty} × {formatPrice(finalPrice(product), t("common.priceOnRequest"))}
                </span>
              </span>
            </li>
          ))}
        </ul>
        {car && (
          <p className="mt-4 rounded-[12px] bg-platinum-50 px-3 py-2 text-[12.5px] text-platinum-600">
            {t("checkout.car")}: <b className="text-ink">{car.full_label}</b>
          </p>
        )}
        <dl className="mt-4 flex flex-col gap-2 border-t border-platinum-100 pt-4 text-[14px]">
          {totals.discount > 0 && (
            <div className="flex justify-between text-success">
              <dt>{t("cart.discount")}</dt>
              <dd className="font-semibold">−{formatPrice(totals.discount)}</dd>
            </div>
          )}
          <div className="flex items-baseline justify-between">
            <dt className="font-semibold">{t("cart.total")}</dt>
            <dd className="font-display text-[26px] font-medium">{formatPrice(totals.total, "—")}</dd>
          </div>
        </dl>
        {serverError && <p className="mt-3 text-[13px] text-danger">{t("checkout.error")}</p>}
        <button
          type="submit"
          disabled={sending}
          className="mt-5 inline-flex h-13 w-full items-center justify-center gap-2 rounded-[14px] bg-gold font-bold text-[#1e1606] shadow-gold disabled:opacity-70"
        >
          {sending && <Loader2 className="size-4 animate-spin" />}
          {sending ? t("checkout.submitting") : t("checkout.submit")}
        </button>
        <p className="mt-3 text-center text-[11.5px] text-platinum-400">{t("checkout.agree")}</p>
      </aside>
    </form>
  );
}
