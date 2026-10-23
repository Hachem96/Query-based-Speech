/**
 * Shared classes for the catalog cards (videos + books) so both grids
 * hover/focus identically. Kept as class strings rather than a component so
 * the cards stay plain <Link>s.
 *
 * Editorial style: a framed thumbnail with the caption set below it on the
 * page itself — no card box. Hover turns the frame gold.
 */
export const cardClass = [
  "group flex flex-col gap-3 rounded-lg text-foreground",
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60",
  "focus-visible:ring-offset-4 focus-visible:ring-offset-background",
].join(" ");

export const thumbClass = [
  "relative aspect-video w-full overflow-hidden rounded-lg border bg-card shadow-[0_1px_2px_rgb(2_42_54/4%)]",
  "transition-colors duration-200 group-hover:border-brand group-focus-visible:border-brand",
].join(" ");

export const thumbImageClass = [
  "size-full object-cover transition-transform duration-300 group-hover:scale-[1.03]",
  "motion-reduce:transition-none motion-reduce:group-hover:scale-100",
].join(" ");

export const cardTitleClass =
  "m-0 text-[15px] leading-snug font-bold text-start transition-colors group-hover:text-primary";
