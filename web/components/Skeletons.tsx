/**
 * Shared skeleton placeholders. Server components — safe to render from
 * `loading.tsx` files and Suspense fallbacks. Shapes mirror the real layouts
 * so nothing shifts when content arrives.
 */
import { Skeleton } from "@/components/ui/skeleton";

export function SkeletonCard() {
  return (
    <div className="flex flex-col overflow-hidden rounded-lg border bg-card">
      <Skeleton className="aspect-video w-full rounded-none" />
      <div className="flex flex-col gap-2 px-4 pt-3.5 pb-4">
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

export function PageTitleSkeleton({ lead = false }: { lead?: boolean }) {
  return (
    <div aria-hidden="true">
      <Skeleton className="mb-5 h-8 w-2/5" />
      {lead && <Skeleton className="mb-7 h-4 w-3/5" />}
    </div>
  );
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
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-2 rounded-lg border bg-card p-4">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
        <div className="flex flex-col gap-3 rounded-lg border bg-card p-4">
          <Skeleton className="h-4 w-2/5" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-8 w-1/2" />
        </div>
      </div>
    </div>
  );
}
