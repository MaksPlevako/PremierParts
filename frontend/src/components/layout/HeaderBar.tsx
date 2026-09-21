"use client";

import { ChevronDown, Menu, Phone, Search } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { Logo } from "@/components/brand/Logo";
import { MyCarChip } from "@/components/car/MyCarChip";
import { SearchBox } from "@/components/search/SearchBox";
import { Link, usePathname } from "@/i18n/navigation";
import { cn, formatPhoneHref } from "@/lib/format";
import type { CategoryNode, Phone as PhoneT } from "@/lib/types";

import { CartButton } from "./CartButton";
import { MegaMenu } from "./MegaMenu";
import { MobileNav } from "./MobileNav";

export function HeaderBar({ categories, phone }: { categories: CategoryNode[]; phone: PhoneT | null }) {
  const t = useTranslations();
  const pathname = usePathname();
  const isHome = pathname === "/";
  const [scrolled, setScrolled] = useState(false);
  const [megaOpen, setMegaOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [mobileSearch, setMobileSearch] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > (isHome ? 420 : 8));
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, [isHome]);

  // close menus after navigation (derived state reset during render, no effect needed)
  const [lastPath, setLastPath] = useState(pathname);
  if (lastPath !== pathname) {
    setLastPath(pathname);
    setMegaOpen(false);
    setMobileOpen(false);
    setMobileSearch(false);
  }

  const showSearch = !isHome || scrolled;
  const nav = [
    { href: "/cars", label: t("common.cars") },
    { href: "/promotions", label: t("common.promotions"), hot: true },
    { href: "/vin", label: t("common.vin") },
    { href: "/page/dostavka-ta-oplata", label: t("common.delivery") },
    { href: "/contacts", label: t("common.contacts") },
  ];

  return (
    <header className="sticky top-0 z-50">
      <div
        className={cn(
          "glass border-b transition-[border-color,box-shadow] duration-300",
          scrolled ? "border-platinum-200 shadow-[0_10px_30px_-20px_rgba(21,24,28,.35)]" : "border-transparent",
        )}
      >
        <div className="mx-auto flex h-[68px] max-w-[1320px] items-center gap-3 px-4 sm:px-6 lg:gap-6">
          <button
            type="button"
            className="-ml-1 grid size-10 place-items-center rounded-xl hover:bg-platinum-100 lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label={t("header.menu")}
          >
            <Menu className="size-5" />
          </button>

          <Link href="/" className="shrink-0" aria-label="Premier Parts — на головну">
            <Logo />
          </Link>

          <nav className="hidden items-center gap-1 lg:flex" onMouseLeave={() => setMegaOpen(false)}>
            <button
              type="button"
              onMouseEnter={() => setMegaOpen(true)}
              onClick={() => setMegaOpen((v) => !v)}
              aria-expanded={megaOpen}
              className={cn(
                "inline-flex h-10 items-center gap-1.5 rounded-xl px-3.5 text-[14px] font-semibold transition-colors",
                megaOpen ? "bg-ink text-white" : "text-ink hover:bg-platinum-100",
              )}
            >
              {t("common.catalog")}
              <ChevronDown className={cn("size-4 transition-transform", megaOpen && "rotate-180")} />
            </button>
            <AnimatePresence>{megaOpen && <MegaMenu categories={categories} onNavigate={() => setMegaOpen(false)} />}</AnimatePresence>
            {nav.slice(0, showSearch ? 2 : nav.length).map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "inline-flex h-10 items-center rounded-xl px-3 text-[14px] font-medium transition-colors hover:bg-platinum-100",
                  item.hot ? "text-gold-700" : "text-platinum-700",
                  pathname.startsWith(item.href) && "bg-platinum-100 text-ink",
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          <div className="hidden min-w-0 flex-1 md:block">
            <AnimatePresence initial={false}>
              {showSearch && (
                <motion.div
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.25 }}
                >
                  <SearchBox size="header" />
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="ml-auto flex items-center gap-1.5 sm:gap-2 md:ml-0">
            <button
              type="button"
              className="grid size-10 place-items-center rounded-xl hover:bg-platinum-100 md:hidden"
              onClick={() => setMobileSearch((v) => !v)}
              aria-label={t("search.submit")}
            >
              <Search className="size-5" />
            </button>
            <MyCarChip />
            {phone && (
              <a
                href={formatPhoneHref(phone.number)}
                className="hidden size-10 place-items-center rounded-xl hover:bg-platinum-100 sm:grid xl:hidden"
                aria-label={t("header.callUs")}
              >
                <Phone className="size-5" />
              </a>
            )}
            <CartButton />
          </div>
        </div>
        <AnimatePresence>
          {mobileSearch && (
            <motion.div
              className="px-4 pb-3 md:hidden"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
            >
              <SearchBox size="header" autoFocus />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      <MobileNav open={mobileOpen} onClose={() => setMobileOpen(false)} categories={categories} nav={nav} phone={phone} />
    </header>
  );
}
