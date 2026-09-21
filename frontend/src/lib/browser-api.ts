import type { CarRef, MakeDetail, Make, ModelDetail, OrderSummary, ProductCard, Suggest, VinDecodeResult } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", Accept: "application/json", ...(init?.headers ?? {}) },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error("request failed"), { status: res.status, body });
  return body as T;
}

const post = <T>(path: string, data: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(data) });

export const browserApi = {
  suggest: (q: string, car?: number | null, signal?: AbortSignal) =>
    request<Suggest>(`/search/suggest?q=${encodeURIComponent(q)}${car ? `&car=${car}` : ""}`, { signal }),
  decodeVin: (vin: string) => post<VinDecodeResult>("/vin/decode", { vin }),
  vinRequest: (data: { vin: string; name?: string; phone: string; part_query?: string; comment?: string }) =>
    post<{ id: number }>("/vin/requests", data),
  createOrder: (data: unknown) => post<{ number: string; access_token: string; total: number }>("/orders", data),
  quickOrder: (data: { phone: string; name?: string; product_id: number; note?: string; car_generation_id?: number | null }) =>
    post<{ number: string; access_token: string; total: number }>("/orders/quick", data),
  validateCart: (items: { product_id: number; qty: number }[]) =>
    post<{ items: { product_id: number; qty: number; available: boolean; card: ProductCard | null }[]; total: number }>(
      "/cart/validate",
      { items },
    ),
  makes: () => request<Make[]>("/makes"),
  make: (slug: string) => request<MakeDetail>(`/makes/${slug}`),
  model: (make: string, model: string) => request<ModelDetail>(`/cars/${make}/${model}`),
  generation: (id: number) => request<CarRef>(`/generations/${id}`),
  npCities: (q: string) => request<{ enabled: boolean; results: { ref: string; name: string }[] }>(`/np/cities?q=${encodeURIComponent(q)}`),
  npWarehouses: (cityRef: string, q = "") =>
    request<{ enabled: boolean; results: { ref: string; name: string }[] }>(
      `/np/warehouses?city_ref=${encodeURIComponent(cityRef)}&q=${encodeURIComponent(q)}`,
    ),
  order: (number: string, token: string) => request<OrderSummary>(`/orders/${number}?token=${token}`),
};
