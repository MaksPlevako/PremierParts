import type { MetadataRoute } from "next";
import { connection } from "next/server";

import { getCategories, getMakes, getPages, getPromotions, getSitemapIndex } from "@/lib/api";
import { siteUrl } from "@/lib/seo";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  await connection(); // The backend is unavailable during next build.
  const base = siteUrl();
  const [categories, makes, pages, promotions, index] = await Promise.all([
    getCategories(),
    getMakes(),
    getPages(),
    getPromotions(),
    getSitemapIndex(),
  ]);
  if (!categories || !makes || !pages || !promotions || !index) {
    throw new Error("Cannot generate a complete sitemap without the catalogue index");
  }
  const entries: MetadataRoute.Sitemap = [
    { url: base, changeFrequency: "daily", priority: 1 },
    { url: `${base}/catalog`, changeFrequency: "daily", priority: 0.9 },
    { url: `${base}/cars`, changeFrequency: "weekly", priority: 0.8 },
    { url: `${base}/promotions`, changeFrequency: "weekly", priority: 0.6 },
    { url: `${base}/vin`, changeFrequency: "monthly", priority: 0.6 },
    { url: `${base}/contacts`, changeFrequency: "monthly", priority: 0.5 },
  ];
  for (const cat of categories) {
    if (cat.product_count > 0) entries.push({ url: `${base}/category/${cat.slug}`, changeFrequency: "daily", priority: 0.8 });
    for (const child of cat.children) {
      if (child.product_count > 0) entries.push({ url: `${base}/category/${child.slug}`, changeFrequency: "daily", priority: 0.8 });
    }
  }
  for (const make of makes) {
    if (make.product_count > 0) entries.push({ url: `${base}/cars/${make.slug}`, priority: 0.6 });
  }
  const models = new Set<string>();
  for (const [make, model, generation] of index.cars) {
    const modelPath = `${base}/cars/${make}/${model}`;
    models.add(modelPath);
    entries.push({ url: `${modelPath}/${generation}`, changeFrequency: "weekly", priority: 0.6 });
  }
  for (const url of models) entries.push({ url, changeFrequency: "weekly", priority: 0.6 });
  for (const page of pages) entries.push({ url: `${base}/page/${page.slug}`, priority: 0.4 });
  for (const promo of promotions) entries.push({ url: `${base}/promotions/${promo.slug}`, priority: 0.6 });
  for (const product of index.products) {
    entries.push({
      url: `${base}/product/${product.slug}`,
      lastModified: product.updated_at,
      changeFrequency: "weekly",
      priority: 0.7,
    });
  }
  return entries;
}
