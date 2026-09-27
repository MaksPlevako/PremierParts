"use client";

import { CarFront, ChevronRight, LogOut, PackageCheck, Save, ShieldCheck, Truck } from "lucide-react";
import { useEffect, useState } from "react";

import { ProductCard } from "@/components/product/ProductCard";
import { GarageCarForm } from "@/components/account/GarageCarForm";
import { Link, useRouter } from "@/i18n/navigation";
import { browserApi, type ApiRequestError } from "@/lib/browser-api";
import { formatPrice } from "@/lib/format";
import type { AccountProfile, OrderSummary, ProductCard as Card, SavedCar } from "@/lib/types";
import { useMyCar } from "@/stores/my-car";

const steps = ["new", "confirmed", "shipped", "completed"];
const labels: Record<string, string> = { new: "Прийнято", confirmed: "Підтверджено", shipped: "Відправлено", completed: "Виконано", canceled: "Скасовано" };

export function AccountDashboard() {
  const router = useRouter();
  const setCar = useMyCar((s) => s.setCar);
  const [profile, setProfile] = useState<AccountProfile | null>(null);
  const [cars, setCars] = useState<SavedCar[]>([]);
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [products, setProducts] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function reload() {
    const [nextCars, nextOrders, recommendations] = await Promise.all([browserApi.garage(), browserApi.myOrders(), browserApi.recommendations()]);
    setCars(nextCars); setOrders(nextOrders); setProducts(recommendations.products);
    const selected = useMyCar.getState().car;
    if (nextCars.length && !nextCars.some((entry) => entry.car.generation_id === selected?.generation_id)) setCar(nextCars[0].car);
    if (!nextCars.length && selected && cars.length) setCar(null);
  }

  useEffect(() => {
    browserApi.profile().then(async (result) => { setProfile(result); await reload(); }).catch((caught: ApiRequestError) => {
      if (caught.status === 404 || caught.status === 401 || caught.status === 403) router.replace("/account/login");
      else setError("Не вдалося завантажити кабінет. Оновіть сторінку.");
    }).finally(() => setLoading(false));
  // Only load on entry. Mutations explicitly refresh the affected sections.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") browserApi.myOrders().then(setOrders).catch(() => undefined);
    }, 60_000);
    return () => window.clearInterval(timer);
  }, []);

  async function saveProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!profile) return;
    setSaving(true); setError("");
    try {
      setProfile(await browserApi.updateProfile({ first_name: profile.first_name, last_name: profile.last_name, phone: profile.phone, city: profile.city, address: profile.address, np_branch: profile.np_branch }));
    } catch { setError("Не вдалося зберегти профіль. Перевірте введені дані."); }
    finally { setSaving(false); }
  }

  async function removeCar(id: number) {
    try { await browserApi.removeCar(id); await reload(); }
    catch { setError("Не вдалося видалити авто."); }
  }

  if (loading) return <div className="mx-auto my-16 h-96 max-w-[1200px] animate-pulse rounded-[28px] bg-platinum-100" />;
  if (!profile) return <div className="mx-auto max-w-[1200px] px-4 py-16 text-center text-red-700">{error}</div>;
  const field = "h-11 w-full rounded-xl border border-platinum-200 bg-white px-3.5 text-sm outline-none focus:border-gold-500";

  return <div className="mx-auto max-w-[1260px] px-4 py-9 sm:px-6 sm:py-14">
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div><p className="text-[11px] font-bold uppercase tracking-[.2em] text-gold-700">Особистий кабінет</p><h1 className="mt-2 font-display text-[32px] sm:text-[42px]">Вітаємо{profile.first_name ? `, ${profile.first_name}` : ""}</h1><p className="mt-1 text-sm text-platinum-500">Авто, покупки й персональні пропозиції в одному місці.</p></div>
      <button onClick={async () => { try { await browserApi.logout(); setCar(null); router.replace("/account/login"); router.refresh(); } catch { setError("Не вдалося вийти. Спробуйте ще раз."); } }} className="inline-flex h-10 items-center gap-2 rounded-xl border border-platinum-200 px-4 text-sm font-semibold hover:bg-platinum-50"><LogOut className="size-4" /> Вийти</button>
    </div>
    {error && <p role="alert" className="mt-6 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
    <nav aria-label="Розділи кабінету" className="mt-8 flex gap-2 overflow-x-auto border-b border-platinum-200 pb-3 text-sm font-semibold">{[["#garage", "Мій автопарк"], ["#orders", "Замовлення"], ["#recommendations", "Для вас"], ["#profile", "Мої дані"]].map(([href, label]) => <a key={href} href={href} className="shrink-0 rounded-xl px-4 py-2 hover:bg-platinum-100">{label}</a>)}</nav>

    <div className="mt-8 grid gap-7 lg:grid-cols-[minmax(0,1fr)_320px]">
      <div className="min-w-0 space-y-7">
        <section id="garage" className="scroll-mt-28 rounded-[24px] bg-white p-5 ring-1 ring-platinum-200 sm:p-7">
          <div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-xl bg-gold-100 text-gold-800"><CarFront className="size-5" /></span><div><h2 className="font-display text-xl">Мій автопарк</h2><p className="text-xs text-platinum-500">Збережені авто доступні після входу з будь-якого пристрою.</p></div></div>
          {cars.length ? <div className="mt-5 grid gap-3 sm:grid-cols-2">{cars.map((entry) => <div key={entry.id} className="rounded-2xl border border-platinum-200 p-4"><p className="font-semibold">{entry.car.full_label}</p>{entry.vin && <p className="mt-1 text-xs text-platinum-500">VIN: {entry.vin}</p>}<div className="mt-4 flex gap-3 text-xs font-bold"><button onClick={() => setCar(entry.car)} className="text-gold-700 hover:underline">Зробити активним</button><button onClick={() => removeCar(entry.id)} className="text-platinum-500 hover:text-red-700">Видалити</button></div></div>)}</div> : <p className="mt-5 rounded-xl bg-platinum-50 p-4 text-sm text-platinum-600">Поки немає збережених автомобілів. Оберіть авто, щоб бачити сумісні деталі.</p>}
          <GarageCarForm onAdded={async (saved) => { setCar(saved.car); await reload(); }} />
        </section>

        <section id="orders" className="scroll-mt-28 rounded-[24px] bg-white p-5 ring-1 ring-platinum-200 sm:p-7"><div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-xl bg-gold-100 text-gold-800"><Truck className="size-5" /></span><div><h2 className="font-display text-xl">Історія та відстеження замовлень</h2><p className="text-xs text-platinum-500">Замовлення, оформлені після входу в акаунт.</p></div></div>
          {orders.length ? <div className="mt-5 space-y-4">{orders.map((order) => <article key={order.number} className="rounded-2xl border border-platinum-200 p-4 sm:p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="font-display text-lg">{order.number}</p><p className="text-xs text-platinum-500">{new Date(order.created_at).toLocaleDateString("uk-UA")} · {order.items.length} позицій</p></div><span className="rounded-full bg-gold-100 px-3 py-1 text-xs font-bold text-gold-800">{labels[order.status] ?? order.status_label}</span></div>{order.status !== "canceled" && <ol className="mt-5 grid grid-cols-4 gap-1">{steps.map((step, index) => <li key={step} className={`border-t-2 pt-2 text-[10px] sm:text-xs ${index <= steps.indexOf(order.status) ? "border-gold-500 text-ink" : "border-platinum-200 text-platinum-400"}`}>{labels[step]}</li>)}</ol>}<div className="mt-4 flex flex-wrap justify-between gap-2 border-t border-platinum-100 pt-4 text-sm"><span className="text-platinum-600">{order.delivery_label}{order.tracking_number ? ` · ТТН ${order.tracking_number}` : ""}</span><strong>{formatPrice(order.total, "—")}</strong></div>{order.tracking_number && (order.delivery_method === "np_branch" || order.delivery_method === "np_courier") && <a href="https://tracking.novaposhta.ua/#/uk/" target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-xs font-bold text-gold-700 hover:underline">Відстежити у Новій пошті ↗</a>}<details className="mt-3 text-sm"><summary className="cursor-pointer font-semibold text-gold-700">Переглянути товари та доставку</summary><ul className="mt-3 space-y-2">{order.items.map((item, index) => <li key={`${item.sku}-${index}`} className="flex justify-between gap-3"><span>{item.name} × {item.qty}</span><span>{formatPrice(item.line_total, "—")}</span></li>)}</ul><p className="mt-3 text-platinum-500">{[order.city, order.np_branch, order.address].filter(Boolean).join(", ")}</p></details></article>)}</div> : <div className="mt-5 rounded-xl bg-platinum-50 p-5 text-sm text-platinum-600">Покупок ще немає. <Link href="/catalog" className="font-semibold text-gold-700">Перейти до каталогу <ChevronRight className="inline size-4" /></Link></div>}
        </section>
        <section id="recommendations" className="scroll-mt-28"><div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-xl bg-gold-100 text-gold-800"><PackageCheck className="size-5" /></span><div><h2 className="font-display text-xl">Рекомендовано для вас</h2><p className="text-xs text-platinum-500">Сумісні деталі для збережених авто з урахуванням покупок.</p></div></div>{products.length ? <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-3">{products.map((product) => <ProductCard key={product.id} product={product} />)}</div> : <p className="mt-5 rounded-2xl bg-platinum-50 p-5 text-sm text-platinum-600">{cars.length ? "Для ваших авто поки немає персональних пропозицій." : "Додайте автомобіль до автопарку, щоб побачити сумісні деталі."}</p>}</section>
      </div>
      <aside id="profile" className="scroll-mt-28 self-start rounded-[24px] bg-white p-5 ring-1 ring-platinum-200 sm:p-6 lg:sticky lg:top-24"><div className="flex items-center gap-2"><ShieldCheck className="size-5 text-gold-700" /><h2 className="font-display text-xl">Мої дані</h2></div><p className="mt-2 text-xs text-platinum-500">Використовуйте ці дані для швидкого оформлення замовлення.</p><form onSubmit={saveProfile} className="mt-5 grid gap-3">{([ ["first_name", "Ім’я"], ["last_name", "Прізвище"], ["phone", "Телефон"], ["city", "Місто"], ["np_branch", "Відділення Нової Пошти"], ["address", "Адреса"] ] as const).map(([key, label]) => <label key={key} className="grid gap-1 text-xs font-semibold">{label}<input className={field} value={profile[key]} onChange={(event) => setProfile({ ...profile, [key]: event.target.value })} /></label>)}<label className="grid gap-1 text-xs font-semibold">Email<input className={`${field} bg-platinum-50 text-platinum-500`} value={profile.email} readOnly /></label><button disabled={saving} className="mt-2 flex h-11 items-center justify-center gap-2 rounded-xl bg-ink text-sm font-bold text-white disabled:opacity-50"><Save className="size-4" /> Зберегти дані</button></form><p className="mt-4 text-xs text-platinum-500">Email підтверджено ✓{profile.providers.length ? ` · Підключено: ${profile.providers.join(", ")}` : ""}</p></aside>
    </div>
  </div>;
}
