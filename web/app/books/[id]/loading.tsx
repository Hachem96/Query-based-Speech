import { Skeleton } from "@/components/ui/skeleton";
import { HeroSkeleton } from "@/components/Skeletons";

export default function Loading() {
  return (
    <>
      <HeroSkeleton back />
      <div className="page-container py-10 sm:py-14" aria-hidden="true">
        <Skeleton className="h-[80vh] w-full rounded-lg" />
      </div>
    </>
  );
}
