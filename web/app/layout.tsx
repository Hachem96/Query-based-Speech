import type { Metadata } from "next";
import { Geist, IBM_Plex_Sans_Arabic } from "next/font/google";
import { DirectionProvider } from "@/components/ui/direction";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import { LocaleProvider } from "@/components/locale-provider";
import SiteHeader from "@/components/SiteHeader";
import { cn } from "@/lib/utils";
import { dirOf, getDictionary } from "@/lib/i18n";
import { getLocale } from "@/lib/i18n-server";
import "./globals.css";

// Geist carries Latin glyphs; anything it lacks (all Arabic) falls through to
// IBM Plex Sans Arabic. Order matters — see --font-sans in globals.css.
const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist",
  display: "swap",
});

const arabic = IBM_Plex_Sans_Arabic({
  subsets: ["arabic"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ibm-plex-arabic",
  display: "swap",
});

export async function generateMetadata(): Promise<Metadata> {
  const t = getDictionary(await getLocale());
  return { title: t.meta.title, description: t.meta.description };
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  // Locale comes from a cookie so the server renders the right lang/dir —
  // no flash of the wrong direction on first paint.
  const locale = await getLocale();
  const dir = dirOf(locale);
  const t = getDictionary(locale);

  return (
    <html
      lang={locale}
      dir={dir}
      className={cn("font-sans", geist.variable, arabic.variable)}
      suppressHydrationWarning
    >
      <body className="flex min-h-dvh flex-col">
        {/* New storageKey: visitors who stored "system" under the old key would
            otherwise get a literal `system` class (= light tokens) now that
            enableSystem is off. */}
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          storageKey="theme-v2"
          disableTransitionOnChange
        >
          <LocaleProvider locale={locale}>
            <DirectionProvider dir={dir}>
              <TooltipProvider delayDuration={300}>
                <a
                  href="#main"
                  className="fixed top-2 start-2 z-50 -translate-y-[160%] rounded-md bg-brand px-3.5 py-2 text-sm font-semibold text-brand-foreground transition-transform focus-visible:translate-y-0 focus-visible:outline-none"
                >
                  {t.layout.skipToContent}
                </a>
                <SiteHeader />
                <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-5 pt-8 pb-12">
                  {children}
                </main>
                <footer className="border-t text-xs text-muted-foreground">
                  <div className="mx-auto w-full max-w-6xl px-5 py-6">
                    <p className="m-0">{t.layout.footer}</p>
                  </div>
                </footer>
              </TooltipProvider>
            </DirectionProvider>
          </LocaleProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
