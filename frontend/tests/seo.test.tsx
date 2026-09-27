import { afterEach, describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";

import { JsonLd, listingSeo, productJsonLd, seoMetadata, seoSummary, siteUrl } from "@/lib/seo";
import type { ProductDetail } from "@/lib/types";

const originalSiteUrl = process.env.SITE_URL;

afterEach(() => {
  if (originalSiteUrl === undefined) delete process.env.SITE_URL;
  else process.env.SITE_URL = originalSiteUrl;
});

const product = (overrides: Partial<ProductDetail> = {}): ProductDetail => ({
  slug: "front-lamp",
  name: "Передня фара",
  sku: "FP-1",
  manufacturer: "TYC",
  price: 2500,
  sale_price: null,
  stock_status: "in_stock",
  description: "Фара для Volkswagen",
  images: [{ url: "/media/lamp.jpg", alt: "Фара" }],
  part_numbers: [{ number: "OEM-1", kind: "oem" }],
  ...overrides,
} as ProductDetail);

describe("public SEO metadata", () => {
  it("uses the runtime public origin and gives pages their own social metadata", () => {
    process.env.SITE_URL = "https://parts.example/";

    expect(siteUrl()).toBe("https://parts.example");
    expect(seoMetadata("Оптика", "Фари та ліхтарі", "/category/optika")).toMatchObject({
      alternates: { canonical: "/category/optika" },
      openGraph: { title: "Оптика", description: "Фари та ліхтарі", url: "/category/optika" },
      twitter: { title: "Оптика", description: "Фари та ліхтарі" },
    });
  });

  it("indexes each pagination page but keeps filtered and invalid URLs out", () => {
    expect(listingSeo("/category/optika", { page: "2" })).toMatchObject({
      alternates: { canonical: "/category/optika?page=2" },
    });
    expect(listingSeo("/category/optika", { page: "2" }).robots).toBeUndefined();
    expect(listingSeo("/category/optika", { page: "2", sort: "new" })).toMatchObject({
      alternates: { canonical: "/category/optika" },
      robots: { index: false, follow: true },
    });
    expect(listingSeo("/category/optika", { page: "invalid" }).robots).toMatchObject({ index: false });
    expect(listingSeo("/category/optika", { page: ["2", "3"] }).robots).toMatchObject({ index: false });
  });

  it("turns CMS HTML into a short plain-text description", () => {
    expect(seoSummary("<p>Доставка <strong>по Україні</strong>&nbsp; щодня</p>")).toBe("Доставка по Україні щодня");
  });
});

describe("product structured data", () => {
  it.each([
    ["in_stock", "InStock"],
    ["on_order", "PreOrder"],
    ["out_of_stock", "OutOfStock"],
  ] as const)("reports %s availability correctly", (stockStatus, availability) => {
    process.env.SITE_URL = "https://parts.example";
    const json = productJsonLd(product({ stock_status: stockStatus, sale_price: 2000 }));

    expect(json.offers).toMatchObject({
      url: "https://parts.example/product/front-lamp",
      price: 2000,
      priceCurrency: "UAH",
      availability: `https://schema.org/${availability}`,
    });
    expect(json.image).toEqual(["https://parts.example/media/lamp.jpg"]);
  });

  it("does not advertise an unknown price as a purchasable offer", () => {
    expect(productJsonLd(product({ price: 0 })).offers).toBeUndefined();
  });

  it("escapes product text before placing JSON-LD in a script tag", () => {
    const html = renderToStaticMarkup(<JsonLd data={{ name: "</script><script>alert(1)</script>" }} />);

    expect(html).not.toContain("</script><script>");
    expect(html).toContain("\\u003c/script>");
  });
});
