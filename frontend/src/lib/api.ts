import "server-only";

import type {
  CarDetail,
  CarRef,
  CategoryNode,
  HomeData,
  ListingQuery,
  ListingResult,
  Make,
  MakeDetail,
  ModelDetail,
  OrderSummary,
  Page,
  ProductDetail,
  Promotion,
  SiteSettings,
} from "./types";

const BASE = `${process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000"}/api`;

export class ApiError extends Error {
  constructor(
    public status: number,
    public path: string,
  ) {
    super(`API ${status} for ${path}`);
  }
}

type Options = { tags?: string[]; revalidate?: number | false; noStore?: boolean };

async function apiGet<T>(path: string, { tags = [], revalidate = 300, noStore = false }: Options = {}): Promise<T | null> {
  const init: RequestInit = noStore
    ? { cache: "no-store" }
    : { next: { tags: ["all", ...tags], revalidate } };
  const res = await fetch(`${BASE}${path}`, { ...init, headers: { Accept: "application/json" } });
  if (res.status === 404) return null;
  if (!res.ok) throw new ApiError(res.status, path);
  return (await res.json()) as T;
}

function qs(params: ListingQuery): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  }
  const s = search.toString();
  return s ? `?${s}` : "";
}

export const getHome = () => apiGet<HomeData>("/home", { tags: ["home", "banners", "products", "promotions"] });
export const getSettings = () => apiGet<SiteSettings>("/settings", { tags: ["settings"], revalidate: 3600 });
export const getCategories = () => apiGet<CategoryNode[]>("/categories", { tags: ["categories"], revalidate: 3600 });
export const getCategory = (slug: string) =>
  apiGet<CategoryNode>(`/categories/${encodeURIComponent(slug)}`, { tags: ["categories", `category:${slug}`] });
export const getProduct = (slug: string) =>
  apiGet<ProductDetail>(`/products/${encodeURIComponent(slug)}`, { tags: ["products", `product:${slug}`] });
export const getMakes = () => apiGet<Make[]>("/makes", { tags: ["makes"], revalidate: 3600 });
export const getMake = (slug: string) => apiGet<MakeDetail>(`/makes/${encodeURIComponent(slug)}`, { tags: ["makes"] });
export const getModel = (make: string, model: string) =>
  apiGet<ModelDetail>(`/cars/${encodeURIComponent(make)}/${encodeURIComponent(model)}`, { tags: ["makes"] });
export const getCar = (make: string, model: string, gen: string) =>
  apiGet<CarDetail>(`/cars/${encodeURIComponent(make)}/${encodeURIComponent(model)}/${encodeURIComponent(gen)}`, {
    tags: ["makes", "products"],
  });
export const getGeneration = (id: number) => apiGet<CarRef>(`/generations/${id}`, { tags: ["makes"], revalidate: 3600 });
export const listProducts = (params: ListingQuery) =>
  apiGet<ListingResult>(`/products${qs(params)}`, { tags: ["products", "promotions"], revalidate: 120 });
export const searchProducts = (params: ListingQuery) =>
  apiGet<ListingResult>(`/search${qs(params)}`, { tags: ["products"], revalidate: 60 });
export const getPromotions = () => apiGet<Promotion[]>("/promotions", { tags: ["promotions"] });
export const getPromotion = (slug: string) =>
  apiGet<Promotion>(`/promotions/${encodeURIComponent(slug)}`, { tags: ["promotions", `promotion:${slug}`] });
export const getPages = () => apiGet<Page[]>("/pages", { tags: ["pages"], revalidate: 3600 });
export const getPage = (slug: string) => apiGet<Page>(`/pages/${encodeURIComponent(slug)}`, { tags: ["pages", `page:${slug}`] });
export const getBanners = (placement: string) =>
  apiGet<import("./types").Banner[]>(`/banners?placement=${placement}`, { tags: ["banners"] });
export const getOrder = (number: string, token: string) =>
  apiGet<OrderSummary>(`/orders/${encodeURIComponent(number)}?token=${encodeURIComponent(token)}`, { noStore: true });

/** Settings are needed by every page (header/footer); never let an API hiccup break rendering. */
export async function getSettingsSafe(): Promise<SiteSettings | null> {
  try {
    return await getSettings();
  } catch {
    return null;
  }
}
