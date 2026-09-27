import { expect, test } from "@playwright/test";

test("sitemap exposes every active product and car page without duplicate URLs", async ({ request }) => {
  const [indexResponse, sitemapResponse, robotsResponse] = await Promise.all([
    request.get("/api/seo/sitemap-index"),
    request.get("/sitemap.xml"),
    request.get("/robots.txt"),
  ]);
  expect(indexResponse.ok()).toBeTruthy();
  expect(sitemapResponse.ok()).toBeTruthy();
  expect(robotsResponse.ok()).toBeTruthy();

  const index = await indexResponse.json() as {
    products: { slug: string }[];
    cars: [string, string, string][];
  };
  const xml = await sitemapResponse.text();
  const urls = [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1]);
  const urlSet = new Set(urls);
  const origin = new URL(sitemapResponse.url()).origin;

  expect(urls.length).toBeLessThanOrEqual(50_000);
  expect(urlSet.size).toBe(urls.length);
  expect(urlSet.has(`${origin}/promotions`)).toBeTruthy();
  for (const product of index.products) expect(urlSet.has(`${origin}/product/${product.slug}`)).toBeTruthy();
  for (const [make, model, generation] of index.cars) {
    expect(urlSet.has(`${origin}/cars/${make}/${model}`)).toBeTruthy();
    expect(urlSet.has(`${origin}/cars/${make}/${model}/${generation}`)).toBeTruthy();
  }

  const robots = await robotsResponse.text();
  expect(robots).toContain(`Sitemap: ${origin}/sitemap.xml`);
  expect(robots).toContain("Disallow: /admin/");
  expect(robots).not.toContain("Disallow: /search");
});

test("every public page family serves a page-specific canonical and description", async ({ page, request, isMobile }) => {
  test.skip(isMobile, "server metadata is identical across viewports");
  test.setTimeout(120_000);

  const [categoriesResponse, makesResponse, pagesResponse, promotionsResponse, indexResponse] = await Promise.all([
    request.get("/api/categories"),
    request.get("/api/makes"),
    request.get("/api/pages"),
    request.get("/api/promotions"),
    request.get("/api/seo/sitemap-index"),
  ]);
  const categories = await categoriesResponse.json() as { slug: string; product_count: number }[];
  const makes = await makesResponse.json() as { slug: string; product_count: number }[];
  const pages = await pagesResponse.json() as { slug: string }[];
  const promotions = await promotionsResponse.json() as { slug: string }[];
  const index = await indexResponse.json() as { products: { slug: string }[]; cars: [string, string, string][] };
  const [make, model, generation] = index.cars[0];
  const paths = [
    "/", "/catalog", "/cars", "/vin", "/contacts", "/promotions",
    `/category/${categories.find((category) => category.product_count > 0)!.slug}`,
    `/cars/${makes.find((item) => item.product_count > 0)!.slug}`,
    `/cars/${make}/${model}`,
    `/cars/${make}/${model}/${generation}`,
    `/product/${index.products[0].slug}`,
  ];
  if (pages.length) paths.push(`/page/${pages[0].slug}`);
  if (promotions.length) paths.push(`/promotions/${promotions[0].slug}`);

  await page.goto("/", { waitUntil: "domcontentloaded" });
  const origin = new URL(page.url()).origin;
  for (const path of paths) {
    const response = await request.get(path);
    expect(response.status(), path).toBe(200);
    const metadata = await page.evaluate((html) => {
      const document = new DOMParser().parseFromString(html, "text/html");
      return {
        canonical: document.querySelector('link[rel="canonical"]')?.getAttribute("href"),
        description: document.querySelector('meta[name="description"]')?.getAttribute("content"),
        ogTitle: document.querySelector('meta[property="og:title"]')?.getAttribute("content"),
        robots: document.querySelector('meta[name="robots"]')?.getAttribute("content"),
      };
    }, await response.text());

    expect(metadata.canonical, path).toBe(path === "/" ? origin : `${origin}${path}`);
    expect(metadata.description?.length, path).toBeGreaterThan(15);
    expect(metadata.ogTitle?.length, path).toBeGreaterThan(3);
    expect(metadata.robots?.includes("noindex") ?? false, path).toBe(false);
  }
});

test("product metadata and structured data match the public product API", async ({ page, request }) => {
  const index = await (await request.get("/api/seo/sitemap-index")).json() as { products: { slug: string }[] };
  const slug = index.products[0].slug;
  const product = await (await request.get(`/api/products/${slug}`)).json() as {
    name: string; price: number; sale_price: number | null; stock_status: string;
  };
  const origin = new URL(test.info().project.use.baseURL ?? "http://localhost:3000").origin;

  await page.goto(`/product/${slug}`, { waitUntil: "domcontentloaded" });
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", `${origin}/product/${slug}`);
  await expect(page.locator('meta[name="description"]')).toHaveAttribute("content", /.+/);
  await expect(page.locator('meta[property="og:title"]')).toHaveAttribute("content", /.+/);
  const jsonLd = await page.locator('script[type="application/ld+json"]').allTextContents();
  const productSchema = jsonLd.map((value) => JSON.parse(value) as Record<string, unknown>).find((value) => value["@type"] === "Product");
  expect(productSchema?.name).toBe(product.name);
  if ((product.sale_price ?? product.price) > 0) {
    expect(productSchema?.offers).toMatchObject({
      price: product.sale_price ?? product.price,
      availability: `https://schema.org/${{
        in_stock: "InStock", on_order: "PreOrder", out_of_stock: "OutOfStock",
      }[product.stock_status as "in_stock" | "on_order" | "out_of_stock"]}`,
    });
  } else {
    expect(productSchema?.offers).toBeUndefined();
  }
});

test("pagination keeps its canonical while filtered and search pages stay out of the index", async ({ page }) => {
  const origin = new URL(test.info().project.use.baseURL ?? "http://localhost:3000").origin;

  await page.goto("/category/optika?page=2", { waitUntil: "domcontentloaded" });
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", `${origin}/category/optika?page=2`);
  await expect(page.locator('meta[name="robots"]')).toHaveCount(0);

  await page.goto("/category/optika?sort=new", { waitUntil: "domcontentloaded" });
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute("href", `${origin}/category/optika`);
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);

  await page.goto("/search?q=fara", { waitUntil: "domcontentloaded" });
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);
});

test("car picker loads on demand and can be reopened", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: "Обрати авто" }).click();
  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("heading", { name: "Оберіть ваше авто" })).toBeVisible();
  await page.getByRole("button", { name: "Закрити" }).click();
  await expect(dialog).toBeHidden();
  await page.getByRole("button", { name: "Обрати авто" }).click();
  await expect(dialog).toBeVisible();
});
