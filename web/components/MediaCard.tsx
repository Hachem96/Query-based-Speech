/**
 * Shared surface class for the catalog cards (videos + books) so both grids
 * hover/focus identically. Kept as a class string rather than a component so
 * the cards stay plain <Link>s.
 */
export const cardClass = [
  "group flex flex-col overflow-hidden rounded-lg border bg-card text-card-foreground",
  "transition-[transform,box-shadow,border-color] duration-200",
  "hover:-translate-y-1 hover:border-input hover:shadow-lg hover:shadow-black/10 dark:hover:shadow-black/50",
  "focus-visible:-translate-y-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/60",
  "motion-reduce:transition-none motion-reduce:hover:translate-y-0",
].join(" ");
