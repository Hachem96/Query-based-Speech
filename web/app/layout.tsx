import type { Metadata } from "next";
import { Geist, IBM_Plex_Sans_Arabic } from "next/font/google";
import { DirectionProvider } from "@/components/ui/direction";
import { TooltipProvider } from "@/components/ui/tooltip";
import { ThemeProvider } from "@/components/theme-provider";
import SiteHeader from "@/components/SiteHeader";
import { cn } from "@/lib/utils";
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

export const metadata: Metadata = {
  title: "إسأل سيد · Es2al Sayed",
  description:
    "اسأل سؤالاً عن محاضرة عربية وانتقل مباشرةً إلى اللحظة التي تُجيب عنه.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="ar"
      dir="rtl"
      className={cn("font-sans", geist.variable, arabic.variable)}
      suppressHydrationWarning
    >
      <body className="flex min-h-dvh flex-col">
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <DirectionProvider dir="rtl">
            <TooltipProvider delayDuration={300}>
              <a
                href="#main"
                className="fixed top-2 start-2 z-50 -translate-y-[160%] rounded-md bg-brand px-3.5 py-2 text-sm font-semibold text-brand-foreground transition-transform focus-visible:translate-y-0 focus-visible:outline-none"
              >
                تخطَّ إلى المحتوى
              </a>
              <SiteHeader />
              <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-5 pt-8 pb-12">
                {children}
              </main>
              <footer className="border-t text-xs text-muted-foreground">
                <div className="mx-auto w-full max-w-6xl px-5 py-6">
                  <p className="m-0">إسأل سيد — منصة تعلّم تفاعلية للمحاضرات العربية.</p>
                </div>
              </footer>
            </TooltipProvider>
          </DirectionProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
