import type { MetadataRoute } from "next";
import { connection } from "next/server";

import { siteUrl } from "@/lib/seo";

export default async function robots(): Promise<MetadataRoute.Robots> {
  await connection(); // Use the public origin configured at runtime, not the build machine's URL.
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/admin/", "/api/", "/checkout/success/"] }],
    sitemap: `${siteUrl()}/sitemap.xml`,
  };
}
