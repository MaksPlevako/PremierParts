import type { MetadataRoute } from "next";

import { siteUrl } from "@/lib/seo";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/cart", "/checkout", "/search", "/admin/", "/api/"] }],
    sitemap: `${siteUrl()}/sitemap.xml`,
  };
}
