import type { MetadataRoute } from "next";
import { connection } from "next/server";

import { getCategories, getMakes, getPages, getPromotions, listProducts } from "@/lib/api";
import { siteUrl } from "@/lib/seo";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  await connection(); // built at request time: the backend is not reachable during `next build`
  const base = siteUrl();
  const [categories, makes, pages, promotions] = await Promise.all([
    getCategories().catch(() => null),
    getMakes().catch(() => null),
    getPages().catch(() => null),
    getPromotions().catch(() => null),
  ]);
  const entries: MetadataRoute.Sitemap = [
    { url: base, changeFrequency: "daily", priority: 1 },
    { url: `${base}/catalog`, changeFrequency: "daily", priority: 0.9 },
    { url: `${base}/cars`, changeFrequency: "weekly", priority: 0.8 },
    { url: `${base}/vin`, changeFrequency: "monthly", priority: 0.6 },
    { url: `${base}/contacts`, changeFrequency: "monthly", priority: 0.5 },
  ];
  for (const cat of categories ?? []) {
    entries.push({ url: `${base}/category/${cat.slug}`, changeFrequency: "daily", priority: 0.8 });
    for (const child of cat.children) entries.push({ url: `${base}/category/${child.slug}`, changeFrequency: "daily", priority: 0.8 });
  }
  for (const make of makes ?? []) if (make.product_count) entries.push({ url: `${base}/cars/${make.slug}`, priority: 0.6 });
  for (const page of pages ?? []) entries.push({ url: `${base}/page/${page.slug}`, priority: 0.4 });
  for (const promo of promotions ?? []) entries.push({ url: `${base}/promotions/${promo.slug}`, priority: 0.6 });

  // Products: walk the listing API (60 per page) — fine for the demo catalogue size
  for (let page = 1; page <= 100; page++) {
    const res = await listProducts({ page, page_size: 60, sort: "new" }).catch(() => null);
    if (!res) break;
    for (const p of res.results) entries.push({ url: `${base}/product/${p.slug}`, changeFrequency: "weekly", priority: 0.7 });
    if (page >= res.pages) break;
  }
  return entries;
}
