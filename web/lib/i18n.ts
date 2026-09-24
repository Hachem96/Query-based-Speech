/**
 * UI strings for both locales. Shared by server and client components, so it
 * must not import anything server-only (see `lib/i18n-server.ts` for that).
 *
 * Only static UI copy lives here — catalog data (video names, subjects, book
 * titles) comes from the DB as-is and keeps `dir="auto"` wherever it renders.
 */

export const LOCALES = ["ar", "en"] as const;
export type Locale = (typeof LOCALES)[number];
export const DEFAULT_LOCALE: Locale = "ar";
export const LOCALE_COOKIE = "lang";

export function isLocale(value: unknown): value is Locale {
  return LOCALES.includes(value as Locale);
}

export const dirOf = (locale: Locale) => (locale === "ar" ? "rtl" : "ltr");

const ar = {
  meta: {
    title: "إسأل سيد · Es2al Sayed",
    description: "اسأل سؤالاً عن محاضرة عربية وانتقل مباشرةً إلى اللحظة التي تُجيب عنه.",
  },
  layout: {
    skipToContent: "تخطَّ إلى المحتوى",
    footer: "إسأل سيد — منصة تعلّم تفاعلية للمحاضرات العربية.",
  },
  header: {
    homeLabel: "إسأل سيد — الصفحة الرئيسية",
    navLabel: "التنقل الرئيسي",
    videos: "الفيديوهات",
    books: "الكتب",
  },
  theme: {
    groupLabel: "سمة العرض",
    light: "فاتح",
    dark: "داكن",
  },
  language: {
    // Label names the language you switch *to*, written in that language.
    switchTo: "English",
    switchToLabel: "Switch to English",
  },
  home: {
    title: "مكتبة الفيديوهات",
    lead: "اختر محاضرة، اطرح سؤالاً بالعربية، وسينقلك المشغّل مباشرةً إلى المقطع الذي يُجيب عنه.",
    aiNote: "النص المكتوب مُولَّد بالذكاء الاصطناعي وقد يحتوي على أخطاء. نرحّب بملاحظاتكم.",
    noMatches: "لا توجد فيديوهات تطابق هذه المرشِّحات.",
    clearFilters: "مسح المرشِّحات",
    noVideos: "لم تُضَف أي فيديوهات إلى المكتبة بعد.",
  },
  filters: {
    subject: "المادة",
    allSubjects: "كل المواد",
    year: "السنة",
    allYears: "كل السنوات",
  },
  books: {
    title: "مكتبة الكتب",
    noBooks: "لم تُضَف أي كتب إلى المكتبة بعد.",
    untitled: "بدون عنوان",
    coverAlt: (title: string) => `غلاف كتاب: ${title}`,
    back: "العودة إلى الكتب",
    pdfMissing: "ملف PDF لهذا الكتاب غير متوفر.",
  },
  video: {
    coverAlt: (name: string) => `غلاف فيديو: ${name}`,
    back: "العودة إلى الفيديوهات",
    fileMissing: "ملف هذا الفيديو غير متوفر.",
    docsLabel: "مستندات الفيديو",
    transcript: "النص الكامل",
    summary: "الملخّص",
    translation: "الترجمة",
    docUnavailable: "غير متوفر لهذا الفيديو",
    askHeading: "اسأل سؤالاً",
    askPlaceholder: "اكتب سؤالك عن هذا الفيديو...",
    askLabel: "سؤالك عن الفيديو",
    searching: "جارٍ البحث…",
    search: "ابحث عن الإجابة",
    jumpTo: "انتقل إلى",
    segment: "المقطع",
    seconds: (n: number) => `${n} ثانية`,
    connectionError: "تعذّر الاتصال بالخادم. حاول مرة أخرى.",
  },
  errors: {
    loadFailed: "تعذّر تحميل هذه الصفحة.",
    loadFailedHint: "قد يكون الخادم غير متاح. تأكّد من أن واجهة الـ API قيد التشغيل ويمكن الوصول إليها.",
    retry: "إعادة المحاولة",
    notFound: "تعذّر العثور على هذه الصفحة.",
    backToVideos: "العودة إلى الفيديوهات",
  },
};

export type Dictionary = typeof ar;

const en: Dictionary = {
  meta: {
    title: "Es2al Sayed · إسأل سيد",
    description: "Ask a question about an Arabic lecture and jump straight to the moment that answers it.",
  },
  layout: {
    skipToContent: "Skip to content",
    footer: "Es2al Sayed — an interactive learning platform for Arabic lectures.",
  },
  header: {
    homeLabel: "Es2al Sayed — Home",
    navLabel: "Main navigation",
    videos: "Videos",
    books: "Books",
  },
  theme: {
    groupLabel: "Color theme",
    light: "Light",
    dark: "Dark",
  },
  language: {
    switchTo: "العربية",
    switchToLabel: "التبديل إلى العربية",
  },
  home: {
    title: "Video library",
    lead: "Pick a lecture, ask a question in Arabic, and the player jumps straight to the segment that answers it.",
    aiNote: "The transcription is AI-generated and may contain errors. We welcome your feedback.",
    noMatches: "No videos match these filters.",
    clearFilters: "Clear filters",
    noVideos: "No videos have been added to the library yet.",
  },
  filters: {
    subject: "Subject",
    allSubjects: "All subjects",
    year: "Year",
    allYears: "All years",
  },
  books: {
    title: "Book library",
    noBooks: "No books have been added to the library yet.",
    untitled: "Untitled",
    coverAlt: (title: string) => `Book cover: ${title}`,
    back: "Back to books",
    pdfMissing: "The PDF for this book is not available.",
  },
  video: {
    coverAlt: (name: string) => `Video cover: ${name}`,
    back: "Back to videos",
    fileMissing: "This video file is not available.",
    docsLabel: "Video documents",
    transcript: "Full transcript",
    summary: "Summary",
    translation: "Translation",
    docUnavailable: "Not available for this video",
    askHeading: "Ask a question",
    askPlaceholder: "Type your question about this video...",
    askLabel: "Your question about the video",
    searching: "Searching…",
    search: "Find the answer",
    jumpTo: "Jump to",
    segment: "Segment",
    seconds: (n: number) => `${n} ${n === 1 ? "second" : "seconds"}`,
    connectionError: "Couldn't reach the server. Please try again.",
  },
  errors: {
    loadFailed: "This page couldn't be loaded.",
    loadFailedHint: "The server may be unavailable. Make sure the API is running and reachable.",
    retry: "Try again",
    notFound: "This page couldn't be found.",
    backToVideos: "Back to videos",
  },
};

const DICTIONARIES: Record<Locale, Dictionary> = { ar, en };

export const getDictionary = (locale: Locale): Dictionary => DICTIONARIES[locale];
