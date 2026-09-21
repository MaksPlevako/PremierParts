import type { ProductDetail, SiteSettings } from "./types";

export function siteUrl(): string {
  return (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:8080").replace(/\/$/, "");
}

export function absoluteUrl(path: string): string {
  return path.startsWith("http") ? path : `${siteUrl()}${path.startsWith("/") ? "" : "/"}${path}`;
}

export function storeJsonLd(settings: SiteSettings | null) {
  return {
    "@context": "https://schema.org",
    "@type": "AutoPartsStore",
    name: "Premier Parts",
    url: siteUrl(),
    logo: absoluteUrl("/icon.svg"),
    email: settings?.email,
    telephone: settings?.phones?.[0]?.number,
    address: {
      "@type": "PostalAddress",
      streetAddress: "вул. Вікентія Беретті, 6Б",
      addressLocality: "Київ",
      addressCountry: "UA",
    },
    openingHoursSpecification: {
      "@type": "OpeningHoursSpecification",
      dayOfWeek: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
      opens: "10:00",
      closes: "18:00",
    },
    potentialAction: {
      "@type": "SearchAction",
      target: `${siteUrl()}/search?q={query}`,
      "query-input": "required name=query",
    },
  };
}

export function productJsonLd(p: ProductDetail) {
  const price = p.sale_price ?? p.price;
  return {
    "@context": "https://schema.org",
    "@type": "Product",
    name: p.name,
    sku: p.sku,
    mpn: p.part_numbers.find((n) => n.kind === "oem")?.number ?? p.sku,
    brand: p.manufacturer ? { "@type": "Brand", name: p.manufacturer } : undefined,
    image: p.images.map((i) => absoluteUrl(i.url)),
    description: p.description || p.name,
    itemCondition: "https://schema.org/NewCondition",
    offers: {
      "@type": "Offer",
      url: absoluteUrl(`/product/${p.slug}`),
      priceCurrency: "UAH",
      price: price || undefined,
      availability:
        p.stock_status === "in_stock" ? "https://schema.org/InStock" : "https://schema.org/PreOrder",
    },
  };
}

export function breadcrumbJsonLd(items: { name: string; href: string }[]) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, i) => ({
      "@type": "ListItem",
      position: i + 1,
      name: item.name,
      item: absoluteUrl(item.href),
    })),
  };
}

export function JsonLd({ data }: { data: unknown }) {
  return (
    <script
      type="application/ld+json"
      // JSON-LD must be raw JSON; escape "<" so a product name can never close the script tag
      dangerouslySetInnerHTML={{ __html: JSON.stringify(data).replace(/</g, "\\u003c") }}
    />
  );
}
