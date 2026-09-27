import type { Metadata } from "next";

import type { ProductDetail, SiteSettings } from "./types";

export function siteUrl(): string {
  return (process.env.SITE_URL ?? process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:8080").replace(/\/$/, "");
}

export function absoluteUrl(path: string): string {
  return path.startsWith("http") ? path : `${siteUrl()}${path.startsWith("/") ? "" : "/"}${path}`;
}

export function seoMetadata(title: string, description: string, path: string, image?: string): Metadata {
  const imageUrl = image || "/brand/logo_black_row.png";
  return {
    title,
    description,
    alternates: { canonical: path },
    openGraph: {
      type: "website",
      url: path,
      title,
      description,
      images: [{ url: imageUrl, alt: title }],
    },
    twitter: { card: "summary_large_image", title, description, images: [imageUrl] },
  };
}

export function listingSeo(path: string, searchParams: Record<string, string | string[] | undefined>): Metadata {
  const pageValue = searchParams.page;
  const page = pageValue === undefined ? 1 : typeof pageValue === "string" ? Number(pageValue) : NaN;
  const hasFilters = Object.keys(searchParams).some((key) => key !== "page");
  const validPage = Number.isSafeInteger(page) && page >= 1;
  return {
    alternates: { canonical: !hasFilters && validPage && page > 1 ? `${path}?page=${page}` : path },
    robots: hasFilters || !validPage ? { index: false, follow: true } : undefined,
  };
}

export function seoSummary(value: string, maxLength = 155): string {
  const clean = value.replace(/<[^>]*>/g, " ").replace(/&(?:nbsp|[a-z]+|#\d+);/gi, " ").replace(/\s+/g, " ").trim();
  return clean.length > maxLength ? `${clean.slice(0, maxLength).trimEnd()}…` : clean;
}

export function storeJsonLd(settings: SiteSettings | null) {
  return {
    "@context": "https://schema.org",
    "@type": "AutoPartsStore",
    name: "Premier Parts",
    url: siteUrl(),
    logo: absoluteUrl("/brand/logo_black_main.png"),
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
    offers: price > 0 ? {
      "@type": "Offer",
      url: absoluteUrl(`/product/${p.slug}`),
      priceCurrency: "UAH",
      price,
      availability:
        p.stock_status === "in_stock"
          ? "https://schema.org/InStock"
          : p.stock_status === "on_order"
            ? "https://schema.org/PreOrder"
            : "https://schema.org/OutOfStock",
    } : undefined,
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
