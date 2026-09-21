"use client";

import { ArrowRight, CheckCircle2, Loader2, ScanLine, Send } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { SetMyCarButton } from "@/components/car/SetMyCarButton";
import { isValidPhone, PhoneInput } from "@/components/checkout/PhoneInput";
import { Link } from "@/i18n/navigation";
import { browserApi } from "@/lib/browser-api";
import type { VinDecodeResult } from "@/lib/types";
import { cleanVin, looksLikeVin } from "@/lib/vin";

export function VinTool({ initialVin = "" }: { initialVin?: string }) {
  const t = useTranslations("vin");
  const [vin, setVin] = useState(initialVin.toUpperCase());
  const [result, setResult] = useState<VinDecodeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(() => looksLikeVin(initialVin));

  const decode = async (value = vin) => {
    if (!looksLikeVin(value)) return setError(t("invalid"));
    setError(null);
    setLoading(true);
    try {
      setResult(await browserApi.decodeVin(cleanVin(value)));
    } catch {
      setError(t("invalid"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!looksLikeVin(initialVin)) return;
    browserApi
      .decodeVin(cleanVin(initialVin))
      .then(setResult)
      .catch(() => setError(t("invalid")))
      .finally(() => setLoading(false));
  }, [initialVin, t]);

  const rows: [string, string | number | null][] = result
    ? [
        [t("make"), result.make],
        [t("model"), [result.model, result.series].filter(Boolean).join(" ") || null],
        [t("year"), result.year],
        [t("body"), result.body],
        [t("engine"), result.engine],
        [t("country"), result.country],
      ]
    : [];

  return (
    <div className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
      <div className="flex flex-col gap-6">
        <section className="rounded-[26px] bg-white p-6 ring-1 ring-platinum-200 sm:p-8">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              decode();
            }}
            className="flex flex-col gap-3 sm:flex-row"
          >
            <label className="flex h-14 flex-1 items-center gap-3 rounded-[16px] px-4 ring-1 ring-platinum-200 focus-within:ring-2 focus-within:ring-gold-400">
              <ScanLine className="size-5 text-gold-600" />
              <input
                value={vin}
                onChange={(e) => setVin(e.target.value.toUpperCase())}
                placeholder="WVWZZZ3CZBE123456"
                maxLength={20}
                className="h-full min-w-0 flex-1 bg-transparent font-mono text-[17px] tracking-[0.12em] outline-none"
                aria-label="VIN"
              />
              <span className="font-mono text-[12px] text-platinum-400">{cleanVin(vin).length}/17</span>
            </label>
            <button type="submit" disabled={loading} className="inline-flex h-14 items-center justify-center gap-2 rounded-[16px] bg-ink px-7 font-semibold text-white">
              {loading && <Loader2 className="size-4 animate-spin" />}
              Розпізнати
            </button>
          </form>
          {error && <p className="mt-3 text-[13px] font-medium text-danger">{error}</p>}
          <p className="mt-4 text-[13px] text-platinum-500">
            <b className="text-platinum-700">{t("where")}</b> {t("whereText")}
          </p>
        </section>

        {result && (
          <section className="rounded-[26px] bg-white p-6 ring-1 ring-platinum-200 sm:p-8">
            <div className="mb-4 flex items-center justify-between gap-3">
              <h2 className="font-display text-[19px] font-medium">{t("result")}</h2>
              <span className="rounded-full bg-platinum-100 px-2.5 py-1 font-mono text-[12px]">{result.vin}</span>
            </div>
            <dl className="grid gap-x-8 sm:grid-cols-2">
              {rows
                .filter(([, v]) => v)
                .map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-4 border-b border-platinum-100 py-2.5 text-[14px]">
                    <dt className="text-platinum-500">{k}</dt>
                    <dd className="text-right font-semibold">{v}</dd>
                  </div>
                ))}
            </dl>
            {result.warnings.length > 0 && <p className="mt-3 text-[12.5px] text-warning">{result.warnings[0]}</p>}
            <h3 className="mt-6 mb-3 font-semibold">{t("matches")}</h3>
            {result.matches.length ? (
              <ul className="flex flex-col gap-2">
                {result.matches.map((m) => (
                  <li key={m.generation_id} className="flex flex-wrap items-center gap-3 rounded-[16px] bg-platinum-50 p-4 ring-1 ring-platinum-200">
                    <span className="min-w-0 flex-1 font-semibold">{m.full_label}</span>
                    <Link
                      href={`/cars/${m.make_slug}/${m.model_slug}/${m.generation_slug}`}
                      className="inline-flex items-center gap-1 text-[13px] font-semibold text-gold-700"
                    >
                      Деталі <ArrowRight className="size-3.5" />
                    </Link>
                    <SetMyCarButton car={m} className="h-10 px-4 text-[13px]" />
                  </li>
                ))}
              </ul>
            ) : (
              <p className="rounded-[14px] bg-platinum-50 p-4 text-[14px] text-platinum-600">{t("noMatches")}</p>
            )}
          </section>
        )}
      </div>
      <VinRequestForm vin={vin} />
    </div>
  );
}

function VinRequestForm({ vin }: { vin: string }) {
  const t = useTranslations();
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("+380");
  const [part, setPart] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "done">("idle");
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    if (!looksLikeVin(vin)) return setError(t("vin.invalid"));
    if (!isValidPhone(phone)) return setError(t("checkout.phoneInvalid"));
    setError(null);
    setState("sending");
    try {
      await browserApi.vinRequest({ vin: cleanVin(vin), name, phone, part_query: part });
      setState("done");
    } catch {
      setError(t("checkout.error"));
      setState("idle");
    }
  };

  return (
    <section id="request" className="h-fit scroll-mt-28 rounded-[26px] bg-lux p-6 text-white sm:p-8 lg:sticky lg:top-[92px]">
      <p className="text-[11px] font-bold tracking-[0.24em] text-gold-300">ЗАПИТ МЕНЕДЖЕРУ</p>
      <h2 className="mt-2 font-display text-[22px] font-medium">{t("vin.requestTitle")}</h2>
      <p className="mt-2 text-[14px] text-platinum-300">{t("vin.requestText")}</p>
      {state === "done" ? (
        <div className="mt-6 flex items-start gap-3 rounded-[16px] bg-white/10 p-4">
          <CheckCircle2 className="size-5 shrink-0 text-gold-300" />
          <p className="text-[14px] font-semibold">{t("vin.sent")}</p>
        </div>
      ) : (
        <form
          className="mt-6 flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <input
            value={part}
            onChange={(e) => setPart(e.target.value)}
            placeholder={t("vin.partPlaceholder")}
            className="h-12 rounded-[12px] bg-white/10 px-4 text-white ring-1 ring-white/15 outline-none placeholder:text-platinum-400 focus:ring-2 focus:ring-gold-400"
          />
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={t("checkout.name")}
            className="h-12 rounded-[12px] bg-white/10 px-4 text-white ring-1 ring-white/15 outline-none placeholder:text-platinum-400 focus:ring-2 focus:ring-gold-400"
          />
          <div className="[&_input]:w-full [&_input]:bg-white/10 [&_input]:text-white [&_input]:ring-white/15">
            <PhoneInput value={phone} onChange={setPhone} />
          </div>
          {error && <p className="text-[13px] text-red-300">{error}</p>}
          <button type="submit" disabled={state === "sending"} className="mt-1 inline-flex h-12 items-center justify-center gap-2 rounded-[14px] bg-gold font-bold text-[#1e1606]">
            {state === "sending" ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            {t("vin.send")}
          </button>
        </form>
      )}
    </section>
  );
}
