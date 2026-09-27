import type { AccountProfile, CarRef, MakeDetail, Make, ModelDetail, OrderSummary, ProductCard, SavedCar, Suggest, VinDecodeResult } from "./types";

function csrfToken(): string {
  return decodeURIComponent(document.cookie.split("; ").find((part) => part.startsWith("csrftoken="))?.split("=")[1] ?? "");
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const unsafe = init?.method && init.method !== "GET";
  if (unsafe && !csrfToken()) await fetch("/api/account/config", { credentials: "same-origin", cache: "no-store" });
  const res = await fetch(`/api${path}`, {
    ...init,
    credentials: "same-origin",
    cache: path.startsWith("/account/") ? "no-store" : init?.cache,
    headers: { "Content-Type": "application/json", Accept: "application/json", ...(unsafe ? { "X-CSRFToken": csrfToken() } : {}), ...(init?.headers ?? {}) },
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error("request failed"), { status: res.status, body });
  return body as T;
}

const post = <T>(path: string, data: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(data) });

export type ApiRequestError = Error & { status: number; body: Record<string, unknown> };

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
  accountConfig: () => request<{ google: boolean; apple: boolean }>("/account/config"),
  register: (data: { email: string; password: string; first_name: string }) => post<{ detail: string }>("/account/register", data),
  verifyEmail: (email: string, code: string) => post<AccountProfile>("/account/verify-email", { email, code }),
  resendEmail: (email: string) => post<{ detail: string }>("/account/resend-email", { email }),
  login: (email: string, password: string) => post<AccountProfile>("/account/login", { email, password }),
  logout: () => post<{ ok: boolean }>("/account/logout", {}),
  requestPasswordReset: (email: string) => post<{ detail: string }>("/account/password/reset", { email }),
  confirmPasswordReset: (email: string, code: string, password: string) => post<AccountProfile>("/account/password/confirm", { email, code, password }),
  profile: () => request<AccountProfile>("/account/profile"),
  updateProfile: (data: Partial<AccountProfile>) => request<AccountProfile>("/account/profile", { method: "PATCH", body: JSON.stringify(data) }),
  garage: () => request<SavedCar[]>("/account/garage"),
  addCar: (data: { generation_id: number; nickname?: string; vin?: string }) => post<SavedCar>("/account/garage", data),
  removeCar: (id: number) => request<void>(`/account/garage/${id}`, { method: "DELETE" }),
  myOrders: () => request<OrderSummary[]>("/account/orders"),
  recommendations: () => request<{ reason: string; products: ProductCard[] }>("/account/recommendations"),
};
