import { getTranslations } from "next-intl/server";

import { Horseshoe } from "@/components/brand/Logo";
import { SearchBox } from "@/components/search/SearchBox";
import { Link } from "@/i18n/navigation";

export default async function NotFound() {
  const t = await getTranslations();
  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center px-4 py-20 text-center">
      <Horseshoe className="size-24 opacity-80" />
      <p className="mt-6 font-display text-[64px] leading-none font-medium text-gold">404</p>
      <h1 className="mt-4 font-display text-[26px] font-medium">{t("errors.notFound")}</h1>
      <p className="mt-3 text-[15px] text-platinum-600">{t("errors.notFoundText")}</p>
      <div className="mt-8 w-full">
        <SearchBox size="hero" />
      </div>
      <Link href="/" className="mt-6 font-semibold text-gold-700">
        ← {t("common.home")}
      </Link>
    </div>
  );
}
