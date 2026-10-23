import Link from "next/link";
import BrandMark from "@/components/BrandMark";
import { getT } from "@/lib/i18n-server";

export default async function SiteFooter() {
  const t = await getT();

  return (
    <footer className="dark band-pattern border-t bg-night text-foreground">
      <div className="page-container flex flex-col gap-8 py-12 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <BrandMark />
            <span className="flex flex-col leading-tight">
              <span lang="ar" className="font-heading text-lg font-bold">إسأل سيد</span>
              <span
                dir="ltr"
                lang="en"
                className="text-[11px] font-medium tracking-[0.14em] text-muted-foreground uppercase"
              >
                Es2al Sayed
              </span>
            </span>
          </div>
          <span aria-hidden="true" className="block h-px w-16 bg-brand" />
          <p className="m-0 max-w-[48ch] text-sm text-muted-foreground">{t.layout.footer}</p>
        </div>

        <div className="flex flex-col gap-6 sm:items-end">
          <nav aria-label={t.layout.footerNavLabel} className="flex gap-6 text-sm font-semibold">
            <Link href="/" className="text-muted-foreground transition-colors hover:text-brand">
              {t.header.videos}
            </Link>
            <Link href="/books" className="text-muted-foreground transition-colors hover:text-brand">
              {t.header.books}
            </Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
