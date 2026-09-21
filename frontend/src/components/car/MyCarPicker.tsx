"use client";

import { ArrowLeft, Car, ChevronRight, Loader2, ScanLine, Search } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";

import { toast } from "@/components/ui/Toaster";
import { Dialog } from "@/components/ui/Dialog";
import { useRouter } from "@/i18n/navigation";
import { browserApi } from "@/lib/browser-api";
import { cn } from "@/lib/format";
import type { CarModelItem, CarRef, GenerationItem, Make, MakeDetail, VinDecodeResult } from "@/lib/types";
import { cleanVin, looksLikeVin } from "@/lib/vin";
import { useMyCar } from "@/stores/my-car";

let makesCache: Make[] | null = null;

function toCarRef(make: MakeDetail, model: CarModelItem, gen: GenerationItem): CarRef {
  return {
    generation_id: gen.id,
    make: make.name,
    make_slug: make.slug,
    model: model.name,
    model_slug: model.slug,
    generation_slug: gen.slug,
    label: gen.label,
    full_label: `${make.name} ${gen.label}`,
    years_label: gen.years_label,
    market: model.market,
  };
}

export function MyCarPicker() {
  const t = useTranslations("car");
  const router = useRouter();
  const { pickerOpen, closePicker, setCar } = useMyCar();
  const [tab, setTab] = useState<"model" | "vin">("model");
  const [makes, setMakes] = useState<Make[] | null>(makesCache);
  const [make, setMake] = useState<MakeDetail | null>(null);
  const [model, setModel] = useState<CarModelItem | null>(null);
  const [filter, setFilter] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!pickerOpen || makes) return;
    browserApi.makes().then((data) => {
      makesCache = data;
      setMakes(data);
    });
  }, [pickerOpen, makes]);

  const reset = () => {
    setMake(null);
    setModel(null);
    setFilter("");
  };
  const close = () => {
    closePicker();
    reset();
  };

  const choose = (car: CarRef) => {
    setCar(car);
    reset();
    toast({ title: t("saved", { car: car.full_label }), text: t("chooseCarHint") });
    router.refresh();
  };

  const openMake = async (slug: string) => {
    setBusy(true);
    setFilter("");
    try {
      setMake(await browserApi.make(slug));
    } finally {
      setBusy(false);
    }
  };

  const pickModel = (m: CarModelItem) => {
    if (m.generations.length === 1 && make) return choose(toCarRef(make, m, m.generations[0]));
    setModel(m);
  };

  const step = model ? 3 : make ? 2 : 1;
  const title = step === 1 ? t("make") : step === 2 ? `${make!.name} · ${t("model")}` : `${make!.name} ${model!.name} · ${t("years")}`;

  return (
    <Dialog open={pickerOpen} onClose={close} title={t("pickerTitle")} description={t("pickerSubtitle")} className="sm:max-w-2xl">
      <div className="flex flex-col gap-4 p-5 sm:p-6">
        <div className="grid grid-cols-2 gap-1 rounded-[14px] bg-platinum-100 p-1 text-[13px] font-semibold">
          {(["model", "vin"] as const).map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setTab(key)}
              className={cn(
                "inline-flex h-10 items-center justify-center gap-2 rounded-[11px] transition",
                tab === key ? "bg-white text-ink shadow-soft" : "text-platinum-600 hover:text-ink",
              )}
            >
              {key === "vin" ? <ScanLine className="size-4" /> : <Car className="size-4" />}
              {key === "vin" ? t("byVin") : t("byModel")}
            </button>
          ))}
        </div>

        {tab === "vin" ? (
          <VinPick onPick={choose} />
        ) : (
          <>
            <div className="flex items-center gap-2">
              {step > 1 && (
                <button
                  type="button"
                  onClick={() => (model ? setModel(null) : setMake(null))}
                  className="grid size-9 place-items-center rounded-[10px] ring-1 ring-platinum-200 hover:bg-platinum-50"
                  aria-label="Назад"
                >
                  <ArrowLeft className="size-4" />
                </button>
              )}
              <p className="flex-1 font-display text-[15px] font-medium">{title}</p>
              <span className="text-[12px] font-semibold text-platinum-400">{step}/3</span>
            </div>
            {step < 3 && (
              <label className="flex h-11 items-center gap-2 rounded-[12px] px-3 ring-1 ring-platinum-200 focus-within:ring-2 focus-within:ring-gold-400">
                <Search className="size-4 text-platinum-400" />
                <input
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                  placeholder={step === 1 ? t("searchMake") : t("searchModel")}
                  className="h-full flex-1 bg-transparent text-[14px] outline-none"
                />
              </label>
            )}
            <AnimatePresence mode="wait">
              <motion.div
                key={step}
                initial={{ opacity: 0, x: 16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -16 }}
                transition={{ duration: 0.18 }}
                className="min-h-[300px]"
              >
                {busy || (step === 1 && !makes) ? (
                  <div className="grid h-[300px] place-items-center">
                    <Loader2 className="size-6 animate-spin text-gold-600" />
                  </div>
                ) : step === 1 ? (
                  <MakeStep makes={makes ?? []} filter={filter} onPick={openMake} />
                ) : step === 2 ? (
                  <ModelStep make={make!} filter={filter} onPick={pickModel} />
                ) : (
                  <div className="grid gap-2 sm:grid-cols-2">
                    {model!.generations.map((g) => (
                      <button
                        key={g.id}
                        type="button"
                        onClick={() => choose(toCarRef(make!, model!, g))}
                        className="flex items-center justify-between rounded-[14px] p-4 text-left ring-1 ring-platinum-200 transition hover:bg-platinum-50 hover:ring-gold-400"
                      >
                        <span>
                          <span className="block font-display text-[16px] font-medium">{g.years_label || t("noYears")}</span>
                          <span className="text-[12px] text-platinum-500">{g.product_count} деталей</span>
                        </span>
                        <ChevronRight className="size-4 text-platinum-400" />
                      </button>
                    ))}
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </>
        )}
      </div>
    </Dialog>
  );
}

function MakeStep({ makes, filter, onPick }: { makes: Make[]; filter: string; onPick: (slug: string) => void }) {
  const t = useTranslations("car");
  const f = filter.trim().toLowerCase();
  const list = f ? makes.filter((m) => m.name.toLowerCase().includes(f)) : makes;
  const popular = f ? [] : makes.filter((m) => m.is_popular);
  const sorted = [...list].sort((a, b) => a.name.localeCompare(b.name));
  return (
    <div className="flex flex-col gap-4">
      {popular.length > 0 && (
        <div>
          <p className="mb-2 text-[11px] font-bold tracking-[0.18em] text-platinum-400">{t("popular").toUpperCase()}</p>
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
            {popular.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => onPick(m.slug)}
                className="rounded-[12px] bg-platinum-50 px-2 py-3 text-[13px] font-semibold ring-1 ring-platinum-200 transition hover:bg-white hover:ring-gold-400"
              >
                {m.name}
              </button>
            ))}
          </div>
        </div>
      )}
      <div>
        {!f && <p className="mb-2 text-[11px] font-bold tracking-[0.18em] text-platinum-400">{t("allMakes").toUpperCase()}</p>}
        <div className="grid grid-cols-2 gap-x-3 sm:grid-cols-3">
          {sorted.map((m) => (
            <button
              key={m.id}
              type="button"
              onClick={() => onPick(m.slug)}
              className="flex items-center justify-between rounded-[10px] px-2.5 py-2 text-left text-[14px] hover:bg-platinum-50"
            >
              <span className="font-medium">{m.name}</span>
              <span className="text-[11px] text-platinum-400">{m.product_count || ""}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function ModelStep({ make, filter, onPick }: { make: MakeDetail; filter: string; onPick: (m: CarModelItem) => void }) {
  const f = filter.trim().toLowerCase();
  const families = useMemo(
    () =>
      make.families
        .map((fam) => ({ ...fam, models: fam.models.filter((m) => !f || m.name.toLowerCase().includes(f)) }))
        .filter((fam) => fam.models.length),
    [make, f],
  );
  return (
    <div className="flex max-h-[46vh] flex-col gap-4 overflow-y-auto pr-1">
      {families.map((fam) => (
        <div key={fam.family}>
          <p className="mb-1.5 font-display text-[13px] font-medium text-platinum-500">{fam.family}</p>
          <div className="grid gap-1.5 sm:grid-cols-2">
            {fam.models.map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => onPick(m)}
                className="flex items-center justify-between rounded-[12px] px-3 py-2.5 text-left ring-1 ring-platinum-200 transition hover:bg-platinum-50 hover:ring-gold-400"
              >
                <span className="min-w-0">
                  <span className="block truncate text-[14px] font-semibold">{m.name}</span>
                  <span className="text-[11.5px] text-platinum-500">
                    {m.generations.map((g) => g.years_label).filter(Boolean).join(", ") || "—"}
                  </span>
                </span>
                <span className="ml-2 shrink-0 text-[11px] font-semibold text-gold-700">{m.product_count || ""}</span>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function VinPick({ onPick }: { onPick: (car: CarRef) => void }) {
  const t = useTranslations();
  const [vin, setVin] = useState("");
  const [result, setResult] = useState<VinDecodeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const decode = async () => {
    if (!looksLikeVin(vin)) return setError(t("vin.invalid"));
    setError(null);
    setLoading(true);
    try {
      setResult(await browserApi.decodeVin(cleanVin(vin)));
    } catch {
      setError(t("vin.invalid"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[300px] flex-col gap-4">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          decode();
        }}
        className="flex gap-2"
      >
        <input
          value={vin}
          onChange={(e) => setVin(e.target.value.toUpperCase())}
          placeholder={t("car.vinPlaceholder")}
          maxLength={20}
          className="h-12 min-w-0 flex-1 rounded-[12px] px-4 font-mono text-[15px] tracking-wider uppercase ring-1 ring-platinum-200 outline-none focus:ring-2 focus:ring-gold-400"
        />
        <button type="submit" className="h-12 rounded-[12px] bg-ink px-5 font-semibold text-white" disabled={loading}>
          {loading ? <Loader2 className="size-4 animate-spin" /> : t("car.decode")}
        </button>
      </form>
      {error && <p className="text-[13px] font-medium text-danger">{error}</p>}
      {result && (
        <div className="flex flex-col gap-2">
          <p className="text-[13px] text-platinum-600">
            <b className="text-ink">
              {[result.make, result.model, result.year].filter(Boolean).join(" ") || "—"}
            </b>
            {result.body && ` · ${result.body}`}
            {result.engine && ` · ${result.engine}`}
          </p>
          {result.matches.length ? (
            <>
              <p className="text-[13px] font-semibold">{t("car.chooseVariant")}</p>
              {result.matches.map((m) => (
                <button
                  key={m.generation_id}
                  type="button"
                  onClick={() => onPick(m)}
                  className="flex items-center justify-between rounded-[14px] p-4 text-left ring-1 ring-platinum-200 hover:bg-platinum-50 hover:ring-gold-400"
                >
                  <span className="font-semibold">{m.full_label}</span>
                  <ChevronRight className="size-4 text-platinum-400" />
                </button>
              ))}
            </>
          ) : (
            <p className="rounded-[12px] bg-platinum-50 p-4 text-[13px] text-platinum-600">{t("vin.noMatches")}</p>
          )}
        </div>
      )}
    </div>
  );
}
