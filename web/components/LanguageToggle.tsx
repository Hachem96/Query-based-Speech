"use client";

import { useTransition } from "react";
import { useRouter } from "next/navigation";
import { LanguagesIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { LOCALE_COOKIE, type Locale } from "@/lib/i18n";
import { useLocale, useT } from "@/components/locale-provider";

/**
 * Flips between Arabic and English. The choice lives in a cookie so the server
 * renders `<html lang dir>` correctly; `router.refresh()` re-renders the server
 * tree (layout included) in the new locale without a full reload.
 */
export default function LanguageToggle() {
  const locale = useLocale();
  const t = useT();
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const next: Locale = locale === "ar" ? "en" : "ar";

  function toggle() {
    document.cookie = `${LOCALE_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
    startTransition(() => router.refresh());
  }

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={pending}
      aria-label={t.language.switchToLabel}
      lang={next}
      className={cn(
        "inline-flex h-8 items-center gap-1.5 rounded-md border border-input bg-card px-2.5 text-xs font-semibold text-muted-foreground transition-colors",
        "hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none disabled:opacity-60",
      )}
    >
      <LanguagesIcon className="size-3.5" aria-hidden="true" />
      {t.language.switchTo}
    </button>
  );
}
