/**
 * Shared skeleton placeholders. Server components — safe to render from
 * `loading.tsx` files and Suspense fallbacks. Shapes mirror the real layouts
 * so nothing shifts when content arrives.
 */
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function SkeletonCard() {
  return (
    <div className="flex flex-col gap-3">
      <Skeleton className="aspect-video w-full rounded-lg" />
      <div className="flex flex-col gap-2">
        <Skeleton className="h-4 w-4/5" />
        <Skeleton className="h-3 w-2/5" />
      </div>
    </div>
  );
}

export function CardGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid-cards" aria-hidden="true" aria-busy="true">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}

/** Placeholder for <PageHero>: same dark band, padding and rhythm. */
export function HeroSkeleton({
  align = "start",
  back = false,
  lead = false,
  search = false,
}: {
  align?: "start" | "center";
  back?: boolean;
  lead?: boolean;
  search?: boolean;
}) {
  return (
    <div aria-hidden="true" className="dark band-pattern bg-ink">
      <div
        className={cn(
          "page-container flex flex-col py-12 sm:py-16",
          align === "center" ? "items-center" : "items-start",
        )}
      >
        {back && <Skeleton className="mb-6 h-7 w-36" />}
        <Skeleton className="h-10 w-3/5 max-w-md sm:h-14" />
        <span className="mt-5 block h-px w-16 bg-brand" />
        {lead && <Skeleton className="mt-5 h-5 w-4/5 max-w-xl" />}
        {search && <VideoSearchSkeleton />}
      </div>
    </div>
  );
}

export function VideoSearchSkeleton() {
  return <Skeleton aria-hidden="true" className="mt-8 h-[54px] w-full max-w-2xl rounded-lg" />;
}

export function FiltersSkeleton() {
  return (
    <div className="mb-7 flex flex-wrap gap-4" aria-hidden="true">
      <Skeleton className="h-[58px] w-48" />
      <Skeleton className="h-[58px] w-36" />
    </div>
  );
}

export function WatchSkeleton() {
  return (
    <div className="watch-grid" aria-hidden="true" aria-busy="true">
      <Skeleton className="aspect-video w-full rounded-lg" />
      <div className="flex flex-col gap-5">
        <div className="dark flex flex-col gap-4 rounded-lg border bg-ink p-5">
          <Skeleton className="h-6 w-2/5" />
          <span className="block h-px w-12 bg-brand" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
        <div className="flex flex-col gap-3 rounded-lg border bg-card p-4">
          <Skeleton className="h-4 w-2/5" />
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-6 w-full" />
        </div>
      </div>
    </div>
  );
}
