import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const backend = process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  images: {
    localPatterns: [{ pathname: "/media/**", search: "" }, { pathname: "/brand/**", search: "" }],
    formats: ["image/avif", "image/webp"],
    qualities: [70, 80],
    // media is served by our own Django container on the private Docker network
    dangerouslyAllowLocalIP: true,
  },
  async rewrites() {
    // In Docker nginx routes /api and /media to Django; these rewrites make `next dev` work the same way
    // and let the image optimizer read uploads. App routes such as /api/revalidate still win.
    return [
      { source: "/media/:path*", destination: `${backend}/media/:path*` },
      { source: "/api/:path*", destination: `${backend}/api/:path*` },
    ];
  },
};

export default createNextIntlPlugin("./src/i18n/request.ts")(nextConfig);
