import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { setRequestLocale } from "next-intl/server";

import { Breadcrumbs } from "@/components/catalog/Breadcrumbs";
import { getPage, getPages } from "@/lib/api";
import { Link } from "@/i18n/navigation";
import { cn } from "@/lib/format";
import { seoMetadata, seoSummary } from "@/lib/seo";

export async function generateMetadata({ params }: PageProps<"/[locale]/page/[slug]">): Promise<Metadata> {
  const { slug } = await params;
  const page = await getPage(slug);
  if (!page) return {};
  return seoMetadata(
    page.seo_title || page.title,
    page.seo_description || seoSummary(page.body || page.title),
    `/page/${page.slug}`,
  );
}

export default async function StaticPage({ params }: PageProps<"/[locale]/page/[slug]">) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const [page, pages] = await Promise.all([getPage(slug), getPages()]);
  if (!page) notFound();

  return (
    <div className="mx-auto max-w-[1320px] px-4 pt-6 sm:px-6">
      <Breadcrumbs items={[{ name: page.title }]} />
      <div className="mt-6 grid gap-8 lg:grid-cols-[260px_1fr]">
        <nav className="hidden flex-col gap-1 lg:flex">
          {(pages ?? []).map((p) => (
            <Link
              key={p.slug}
              href={`/page/${p.slug}`}
              className={cn(
                "rounded-[12px] px-4 py-2.5 text-[14px] font-medium",
                p.slug === slug ? "bg-ink text-white" : "text-platinum-700 hover:bg-platinum-50",
              )}
            >
              {p.title}
            </Link>
          ))}
        </nav>
        <article className="rounded-[26px] bg-white p-6 ring-1 ring-platinum-200 sm:p-10">
          <h1 className="font-display text-[28px] font-medium sm:text-[34px]">{page.title}</h1>
          {/* Body is edited by managers in the admin WYSIWYG and sanitised on import */}
          <div className="prose-lux mt-6" dangerouslySetInnerHTML={{ __html: page.body ?? "" }} />
        </article>
      </div>
    </div>
  );
}
