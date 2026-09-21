"use client";

import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";

import { browserApi } from "@/lib/browser-api";
import { cn } from "@/lib/format";

interface Props {
  city: string;
  onCity: (v: string) => void;
  branch: string;
  onBranch: (v: string) => void;
  withBranch: boolean;
  errors: Record<string, string>;
  fieldClass: string;
}

type Option = { ref: string; name: string };

/** City + branch inputs with Nova Poshta autocomplete when the API key is configured; plain inputs otherwise. */
export function NpField({ city, onCity, branch, onBranch, withBranch, errors, fieldClass }: Props) {
  const t = useTranslations("checkout");
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [cities, setCities] = useState<Option[]>([]);
  const [cityRef, setCityRef] = useState<string | null>(null);
  const [branches, setBranches] = useState<Option[]>([]);
  const [open, setOpen] = useState<"city" | "branch" | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    browserApi
      .npCities("Київ")
      .then((r) => setEnabled(r.enabled))
      .catch(() => setEnabled(false));
  }, []);

  useEffect(() => {
    if (!enabled || city.length < 2 || cityRef) return;
    clearTimeout(timer.current);
    timer.current = setTimeout(() => browserApi.npCities(city).then((r) => setCities(r.results)), 200);
  }, [city, enabled, cityRef]);

  useEffect(() => {
    if (!enabled || !cityRef || !withBranch) return;
    browserApi.npWarehouses(cityRef, branch).then((r) => setBranches(r.results));
  }, [cityRef, branch, enabled, withBranch]);

  const list = (items: Option[], pick: (o: Option) => void) =>
    items.length > 0 && (
      <ul className="absolute inset-x-0 top-full z-20 mt-1 max-h-60 overflow-y-auto rounded-[14px] bg-white p-1.5 shadow-float">
        {items.map((o) => (
          <li key={o.ref}>
            <button type="button" onMouseDown={() => pick(o)} className="w-full rounded-[10px] px-3 py-2 text-left text-[13.5px] font-normal hover:bg-platinum-50">
              {o.name}
            </button>
          </li>
        ))}
      </ul>
    );

  return (
    <div className={cn("grid gap-4", withBranch && "sm:grid-cols-2")}>
      <label className="relative flex flex-col gap-1.5 text-[13px] font-semibold" data-field="city">
        {t("city")}
        <input
          value={city}
          onChange={(e) => {
            onCity(e.target.value);
            setCityRef(null);
            onBranch("");
          }}
          onFocus={() => setOpen("city")}
          onBlur={() => setTimeout(() => setOpen(null), 150)}
          autoComplete="address-level2"
          className={cn(fieldClass, errors.city ? "ring-danger" : "ring-platinum-200")}
        />
        {open === "city" && enabled && !cityRef && list(cities, (o) => {
          onCity(o.name);
          setCityRef(o.ref);
          setOpen(null);
        })}
        {errors.city && <p className="text-[12.5px] font-normal text-danger">{errors.city}</p>}
      </label>
      {withBranch && (
        <label className="relative flex flex-col gap-1.5 text-[13px] font-semibold" data-field="np_branch">
          {t("branch")}
          <input
            value={branch}
            onChange={(e) => onBranch(e.target.value)}
            onFocus={() => setOpen("branch")}
            onBlur={() => setTimeout(() => setOpen(null), 150)}
            placeholder={enabled && !cityRef ? "Спершу оберіть місто" : "Напр.: Відділення №12"}
            className={cn(fieldClass, errors.np_branch ? "ring-danger" : "ring-platinum-200")}
          />
          {open === "branch" && enabled && cityRef && list(branches, (o) => {
            onBranch(o.name);
            setOpen(null);
          })}
          {errors.np_branch && <p className="text-[12.5px] font-normal text-danger">{errors.np_branch}</p>}
        </label>
      )}
    </div>
  );
}
