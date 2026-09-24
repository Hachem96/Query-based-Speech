import { cookies } from "next/headers";
import { DEFAULT_LOCALE, LOCALE_COOKIE, getDictionary, isLocale, type Locale } from "./i18n";

/** The visitor's chosen locale, from the `lang` cookie set by LanguageToggle. */
export async function getLocale(): Promise<Locale> {
  const value = (await cookies()).get(LOCALE_COOKIE)?.value;
  return isLocale(value) ? value : DEFAULT_LOCALE;
}

export async function getT() {
  return getDictionary(await getLocale());
}
