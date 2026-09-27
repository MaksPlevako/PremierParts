"use client";

import { Plus } from "lucide-react";
import { useEffect, useRef, useState, type FormEvent } from "react";

import { browserApi } from "@/lib/browser-api";
import type { Make, MakeDetail, SavedCar } from "@/lib/types";

const field = "h-11 w-full rounded-xl border border-platinum-200 bg-white px-3.5 text-sm outline-none focus:border-gold-500 disabled:bg-platinum-100 disabled:text-platinum-400";

export function GarageCarForm({ onAdded }: { onAdded: (car: SavedCar) => Promise<void> }) {
  const [makes, setMakes] = useState<Make[]>([]);
  const [loadingMakes, setLoadingMakes] = useState(true);
  const [makeSlug, setMakeSlug] = useState("");
  const [makeDetail, setMakeDetail] = useState<MakeDetail | null>(null);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelId, setModelId] = useState("");
  const [generationId, setGenerationId] = useState("");
  const [vin, setVin] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const makeRequest = useRef(0);

  useEffect(() => {
    let active = true;
    browserApi.makes().then((data) => {
      if (active) setMakes(data);
    }).catch(() => {
      if (active) setError("Не вдалося завантажити каталог авто. Оновіть сторінку.");
    }).finally(() => {
      if (active) setLoadingMakes(false);
    });
    return () => { active = false; };
  }, []);

  async function chooseMake(slug: string) {
    const request = ++makeRequest.current;
    setMakeSlug(slug);
    setMakeDetail(null);
    setModelId("");
    setGenerationId("");
    setError("");
    if (!slug) { setLoadingModels(false); return; }
    setLoadingModels(true);
    try {
      const detail = await browserApi.make(slug);
      if (makeRequest.current === request) setMakeDetail(detail);
    } catch {
      if (makeRequest.current === request) setError("Не вдалося завантажити моделі. Спробуйте обрати марку ще раз.");
    } finally {
      if (makeRequest.current === request) setLoadingModels(false);
    }
  }

  const models = makeDetail?.families.flatMap((family) => family.models).filter((model) => model.generations.length > 0) ?? [];
  const model = models.find((entry) => String(entry.id) === modelId);
  const generation = model?.generations.find((entry) => String(entry.id) === generationId);
  const vinValid = !vin || /^[A-HJ-NPR-Z0-9]{17}$/.test(vin);

  async function addCar(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!generation || !vinValid) return;
    setSaving(true);
    setError("");
    try {
      const saved = await browserApi.addCar({ generation_id: generation.id, vin });
      setVin("");
      setMakeSlug("");
      setMakeDetail(null);
      setModelId("");
      setGenerationId("");
      await onAdded(saved);
    } catch {
      setError("Не вдалося зберегти авто. Перевірте дані та спробуйте ще раз.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={addCar} className="mt-5 rounded-2xl bg-platinum-50 p-4">
      <p className="text-sm font-semibold">Додати авто з каталогу</p>
      <p className="mt-1 text-xs text-platinum-500">Оберіть марку, модель і покоління вашого авто.</p>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <label className="grid gap-1.5 text-xs font-semibold">
          Марка
          <select aria-label="Марка авто" className={field} value={makeSlug} onChange={(event) => void chooseMake(event.target.value)} disabled={loadingMakes || saving} required>
            <option value="">{loadingMakes ? "Завантаження марок…" : "Оберіть марку"}</option>
            {makes.map((make) => <option key={make.id} value={make.slug}>{make.name}</option>)}
          </select>
        </label>
        <label className="grid gap-1.5 text-xs font-semibold">
          Модель
          <select aria-label="Модель авто" className={field} value={modelId} onChange={(event) => { setModelId(event.target.value); setGenerationId(""); }} disabled={!makeDetail || loadingModels || saving} required>
            <option value="">{loadingModels ? "Завантаження моделей…" : "Оберіть модель"}</option>
            {models.map((entry) => <option key={entry.id} value={entry.id}>{entry.name}{entry.market ? ` · ${entry.market}` : ""}</option>)}
          </select>
        </label>
        <label className="grid gap-1.5 text-xs font-semibold">
          Покоління та роки
          <select aria-label="Покоління авто" className={field} value={generationId} onChange={(event) => setGenerationId(event.target.value)} disabled={!model || saving} required>
            <option value="">Оберіть покоління</option>
            {model?.generations.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
          </select>
        </label>
      </div>
      {generation && <p className="mt-3 text-xs font-semibold text-gold-800">Обрано: {makeDetail?.name} {generation.label}</p>}
      <div className="mt-4 grid gap-2 sm:grid-cols-[minmax(0,1fr)_auto]">
        <input aria-label="VIN авто" className={field} placeholder="VIN (необов’язково)" value={vin} onChange={(event) => setVin(event.target.value.toUpperCase().trim())} maxLength={17} disabled={saving} />
        <button type="submit" disabled={!generation || !vinValid || saving} className="flex h-11 items-center justify-center gap-2 rounded-xl bg-ink px-4 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"><Plus className="size-4" /> {saving ? "Зберігаємо…" : "Додати авто"}</button>
      </div>
      {!vinValid && <p className="mt-2 text-xs text-red-700">VIN має містити 17 символів без I, O та Q.</p>}
      {error && <p role="alert" className="mt-3 text-xs font-semibold text-red-700">{error}</p>}
    </form>
  );
}
