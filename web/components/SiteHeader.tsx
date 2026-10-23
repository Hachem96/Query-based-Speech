"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import BrandMark from "./BrandMark";
import ContactLink from "./ContactLink";
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

/** `contactHref` comes from the server layout (CONTACT_EMAIL); null hides the button. */
export default function SiteHeader({ contactHref }: { contactHref: string | null }) {
  const pathname = usePathname() || "/";
  const t = useT();

  // `dark` scopes the dark tokens to the header, so it is a dark band that
  // runs straight into the page hero below it.
  return (
    <header className="dark sticky top-0 z-20 border-b bg-ink text-foreground">
      <div className="page-container flex flex-wrap items-center gap-x-8 gap-y-3 py-3">
        <Link
          href="/"
          className="flex items-center gap-3 rounded-sm focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none"
          aria-label={t.header.homeLabel}
        >
          <BrandMark />
          <span className="flex flex-col leading-tight">
            <span lang="ar" className="font-heading text-base font-bold">إسأل سيد</span>
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
                  "after:absolute after:inset-x-3 after:-bottom-px after:h-px after:bg-brand after:opacity-0 after:transition-opacity",
                  active && "text-foreground after:opacity-100",
                )}
              >
                {t.header[tab.key]}
              </Link>
            );
          })}
        </nav>

        <div className="ms-auto flex items-center gap-2 sm:ms-0">
          {contactHref && <ContactLink href={contactHref}>{t.contact.button}</ContactLink>}
          <LanguageToggle />
        </div>
      </div>
    </header>
  );
}
