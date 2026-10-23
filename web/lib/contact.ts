/**
 * Contact address behind the "Contact us" and transcription-feedback links,
 * from the CONTACT_EMAIL env var. Server-only: it is read per request (every
 * page is dynamic), so it can be set or changed without rebuilding the image.
 * Unset → the contact links are not rendered at all.
 */
export function getContactEmail(): string | null {
  return process.env.CONTACT_EMAIL?.trim() || null;
}

/** Percent-encodes the subject (URLSearchParams' `+` for spaces shows up literally in mail clients). */
export function mailtoHref(email: string, subject?: string): string {
  return subject ? `mailto:${email}?subject=${encodeURIComponent(subject)}` : `mailto:${email}`;
}
