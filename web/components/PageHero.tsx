import { cn } from "@/lib/utils";

/**
 * Full-bleed dark band that opens every page: optional eyebrow, display title,
 * short gold rule, optional lead, then any extra content (search, back link).
 * `dark` scopes the dark tokens to the band (the page itself stays cream).
 */
export default function PageHero({
  eyebrow,
  title,
  titleDir,
  lead,
  align = "start",
  before,
  children,
}: {
  eyebrow?: React.ReactNode;
  title: React.ReactNode;
  /** "auto" for catalog titles that may be Arabic, Latin, or mixed. */
  titleDir?: "auto";
  lead?: React.ReactNode;
  align?: "start" | "center";
  /** Rendered above the eyebrow (e.g. a back link). */
  before?: React.ReactNode;
  children?: React.ReactNode;
}) {
  const center = align === "center";

  return (
    <section className="dark band-pattern bg-ink text-foreground">
      <div
        className={cn(
          "page-container flex flex-col py-12 sm:py-16",
          center ? "items-center text-center" : "items-start text-start",
        )}
      >
        {before}
        {eyebrow && <p dir="auto" className="eyebrow m-0 mb-3">{eyebrow}</p>}
        <h1
          dir={titleDir}
          className={cn(
            "m-0 text-3xl leading-tight font-bold sm:text-5xl",
            center ? "max-w-[22ch]" : "max-w-[32ch] text-start",
          )}
        >
          {title}
        </h1>
        <span aria-hidden="true" className="mt-5 block h-px w-16 bg-brand" />
        {lead && (
          <p className="m-0 mt-5 max-w-[62ch] text-base text-muted-foreground sm:text-lg">{lead}</p>
        )}
        {children}
      </div>
    </section>
  );
}
