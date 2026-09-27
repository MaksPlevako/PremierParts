import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("next/server", () => ({ connection: vi.fn(async () => {}) }));
vi.mock("@/lib/seo", () => ({ siteUrl: () => "https://parts.example" }));
vi.mock("@/lib/api", () => ({
  getCategories: vi.fn(),
  getMakes: vi.fn(),
  getPages: vi.fn(),
  getPromotions: vi.fn(),
  getSitemapIndex: vi.fn(),
}));

import sitemap from "@/app/sitemap";
import { getCategories, getMakes, getPages, getPromotions, getSitemapIndex } from "@/lib/api";

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getCategories).mockResolvedValue([]);
  vi.mocked(getMakes).mockResolvedValue([]);
  vi.mocked(getPages).mockResolvedValue([]);
  vi.mocked(getPromotions).mockResolvedValue([]);
  vi.mocked(getSitemapIndex).mockResolvedValue({ products: [], cars: [] });
});

describe("sitemap", () => {
  it("includes products past the old 6000-item limit and every public car route", async () => {
    vi.mocked(getCategories).mockResolvedValue([
      { id: 1, slug: "optika", name: "Оптика", icon: "light", image: null, product_count: 1, children: [
        { id: 2, slug: "empty", name: "Порожня", icon: "light", image: null, product_count: 0, children: [] },
      ] },
    ]);
    vi.mocked(getMakes).mockResolvedValue([
      { id: 1, name: "Ford", slug: "ford", logo: null, is_popular: true, product_count: 10 },
    ]);
    vi.mocked(getSitemapIndex).mockResolvedValue({
      products: Array.from({ length: 6001 }, (_, i) => ({ slug: `part-${i}`, updated_at: "2026-09-27T10:00:00Z" })),
      cars: [["ford", "focus", "2010-2014"], ["ford", "focus", "2015-2018"]],
    });

    const entries = await sitemap();
    const urls = entries.map((entry) => entry.url);

    expect(urls.filter((url) => url.includes("/product/"))).toHaveLength(6001);
    expect(urls).toContain("https://parts.example/product/part-6000");
    expect(urls).toContain("https://parts.example/category/optika");
    expect(urls).not.toContain("https://parts.example/category/empty");
    expect(urls).toContain("https://parts.example/cars/ford/focus");
    expect(urls).toContain("https://parts.example/cars/ford/focus/2010-2014");
    expect(urls).toContain("https://parts.example/cars/ford/focus/2015-2018");
    expect(urls).toContain("https://parts.example/promotions");
    expect(new Set(urls).size).toBe(urls.length);
    expect(entries.find((entry) => entry.url.endsWith("/product/part-6000"))?.lastModified).toBe("2026-09-27T10:00:00Z");
  });

  it("fails visibly instead of publishing a partial sitemap when the catalogue API fails", async () => {
    vi.mocked(getSitemapIndex).mockRejectedValueOnce(new Error("catalogue unavailable"));

    await expect(sitemap()).rejects.toThrow("catalogue unavailable");
  });
});
