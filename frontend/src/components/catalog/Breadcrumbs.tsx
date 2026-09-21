import { ChevronRight } from "lucide-react";

import { Link } from "@/i18n/navigation";
import { breadcrumbJsonLd, JsonLd } from "@/lib/seo";

export function Breadcrumbs({ items }: { items: { name: string; href?: string }[] }) {
  const all = [{ name: "Головна", href: "/" }, ...items];
  return (
    <nav aria-label="Навігація" className="text-[12.5px] text-platinum-500">
      <JsonLd data={breadcrumbJsonLd(all.filter((i) => i.href) as { name: string; href: string }[])} />
      <ol className="flex flex-wrap items-center gap-1">
        {all.map((item, i) => (
          <li key={`${item.name}-${i}`} className="inline-flex items-center gap-1">
            {i > 0 && <ChevronRight className="size-3.5 text-platinum-300" />}
            {item.href && i < all.length - 1 ? (
              <Link href={item.href} className="hover:text-ink">
                {item.name}
              </Link>
            ) : (
              <span className="font-medium text-platinum-700">{item.name}</span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
