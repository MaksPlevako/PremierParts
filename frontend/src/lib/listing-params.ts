import type { ListingQuery } from "./types";

const KEYS = ["q", "manufacturer", "side", "stock", "price_min", "price_max", "sort", "page", "all_cars", "category"] as const;

export type SearchParams = Record<string, string | string[] | undefined>;

/** Keep only the listing parameters we understand, as plain strings. */
export function pickListingParams(sp: SearchParams): Record<string, string | undefined> {
  const out: Record<string, string | undefined> = {};
  for (const key of KEYS) {
    const value = sp[key];
    out[key] = Array.isArray(value) ? value[0] : value;
  }
  return out;
}

export function listingQuery(sp: SearchParams, extra: ListingQuery, car: number | null): ListingQuery {
  const picked = pickListingParams(sp);
  return { ...picked, ...extra, car: car ?? undefined };
}
