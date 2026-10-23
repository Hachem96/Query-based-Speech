import type { Metadata } from "next";
import { Cairo, Changa } from "next/font/google";
import { DirectionProvider } from "@/components/ui/direction";
import { TooltipProvider } from "@/components/ui/tooltip";
import { LocaleProvider } from "@/components/locale-provider";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import { cn } from "@/lib/utils";
import { getContactEmail, mailtoHref } from "@/lib/contact";
import { dirOf, getDictionary } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";
import "./globals.css";

// Cairo is the body face for both scripts; Changa (a condensed Kufi) sets the
// h1/h2 display titles. See --font-sans / --font-heading in globals.css.
const cairo = Cairo({
  subsets: ["arabic", "latin"],
  variable: "--font-cairo",
  display: "swap",
});

const changa = Changa({
  subsets: ["arabic", "latin"],
  variable: "--font-changa",
  display: "swap",
});

export async function generateMetadata(): Promise<Metadata> {
  const t = getDictionary(await getLocale());
  return { title: t.meta.title, description: t.meta.description, other: { google: "notranslate" } };
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Locale comes from a cookie so the server renders the right lang/dir —
  // no flash of the wrong direction on first paint.
  const locale = await getLocale();
  const dir = dirOf(locale);
  const t = getDictionary(locale);
  const contactEmail = getContactEmail();

  return (
    <html
      lang={locale}
      dir={dir}
      // Browser auto-translate rewrites text nodes React owns, which crashes
      // reconciliation ("removeChild ... not a child"). The site has its own
      // Arabic/English toggle instead.
      translate="no"
      className={cn("font-sans", cairo.variable, changa.variable)}
    >
      {/* Single theme: cream pages between dark bands. There is no theme
          switch; `.dark` is only applied to individual bands. */}
      <body className="flex min-h-dvh flex-col">
        <LocaleProvider locale={locale}>
          <DirectionProvider dir={dir}>
            <TooltipProvider delayDuration={300}>
              <a
                href="#main"
                className="fixed top-2 start-2 z-50 -translate-y-[160%] rounded-md bg-brand px-3.5 py-2 text-sm font-semibold text-brand-foreground transition-transform focus-visible:translate-y-0 focus-visible:outline-none"
              >
                {t.layout.skipToContent}
              </a>
              <SiteHeader contactHref={contactEmail && mailtoHref(contactEmail)} />
              {/* Full width: each page wraps its own content in `page-container`
                  so its hero band can run edge to edge. */}
              <main id="main" className="flex w-full flex-1 flex-col">
                {children}
              </main>
              <SiteFooter />
            </TooltipProvider>
          </DirectionProvider>
        </LocaleProvider>
      </body>
    </html>
  );
}
