import { cn } from "@/lib/utils";

/** The gold "س" monogram; decorative — callers supply the accessible name. */
export default function BrandMark({ className }: { className?: string }) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "grid size-9 place-items-center rounded-sm border border-gold/70 font-heading text-xl leading-none font-bold text-gold",
        className,
      )}
    >
      س
    </span>
  );
}
