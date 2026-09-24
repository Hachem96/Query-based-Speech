"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import ThemeToggle from "./ThemeToggle";
import LanguageToggle from "./LanguageToggle";
import { useT } from "./locale-provider";

const TABS = [
  {
    href: "/",
    key: "videos",
    isActive: (p: string) => p === "/" || p.startsWith("/videos"),
  },
  {
    href: "/books",
    key: "books",
    isActive: (p: string) => p.startsWith("/books"),
  },
] as const;

export default function SiteHeader() {
  const pathname = usePathname() || "/";
  const t = useT();

  return (
    <header className="sticky top-0 z-20 border-b bg-background/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-5 py-3">
        <Link
          href="/"
          className="flex items-center gap-2.5 rounded-sm focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none"
          aria-label={t.header.homeLabel}
        >
          <span
            aria-hidden="true"
            className="grid size-8 place-items-center rounded-md bg-brand text-lg font-bold leading-none text-brand-foreground"
          >
            س
          </span>
          <span className="flex flex-col leading-tight">
            <span lang="ar" className="text-base font-bold">إسأل سيد</span>
            {/* Latin brand name: force LTR so the bidi algorithm never flips it. */}
            <span
              dir="ltr"
              lang="en"
              className="text-[11px] font-medium tracking-[0.14em] text-muted-foreground uppercase"
            >
              Es2al Sayed
            </span>
          </span>
        </Link>

        <nav
          aria-label={t.header.navLabel}
          className="order-3 -mb-3 flex w-full gap-1 sm:order-none sm:mb-0 sm:me-auto sm:w-auto"
        >
          {TABS.map((tab) => {
            const active = tab.isActive(pathname);
            return (
              <Link
                key={tab.href}
                href={tab.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative rounded-sm px-3 py-2 text-sm font-semibold text-muted-foreground transition-colors",
                  "hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none",
                  "after:absolute after:inset-x-1 after:-bottom-px after:h-0.5 after:rounded-full after:bg-brand after:opacity-0 after:transition-opacity",
                  active && "text-foreground after:opacity-100",
                )}
              >
                {t.header[tab.key]}
              </Link>
            );
          })}
        </nav>

        <div className="ms-auto flex items-center gap-2 sm:ms-0">
          <LanguageToggle />
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
