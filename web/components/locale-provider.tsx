"use client";

import { createContext, useContext } from "react";
import { getDictionary, type Dictionary, type Locale } from "@/lib/i18n";

const LocaleContext = createContext<Locale>("ar");

/** Hands the server-resolved locale to client components. */
export function LocaleProvider({ locale, children }: { locale: Locale; children: React.ReactNode }) {
  return <LocaleContext.Provider value={locale}>{children}</LocaleContext.Provider>;
}

export const useLocale = () => useContext(LocaleContext);

export function useT(): Dictionary {
  return getDictionary(useLocale());
}
