import { Skeleton } from "@/components/ui/skeleton";
import { WatchSkeleton } from "@/components/Skeletons";

export default function Loading() {
  return (
    <div aria-hidden="true">
      <Skeleton className="mb-4 h-7 w-40" />
      <Skeleton className="mb-2 h-8 w-1/2" />
      <Skeleton className="mb-5 h-4 w-1/4" />
      <WatchSkeleton />
    </div>
  );
}
