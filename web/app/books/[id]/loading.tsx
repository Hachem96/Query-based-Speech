import { Skeleton } from "@/components/ui/skeleton";

export default function Loading() {
  return (
    <div aria-hidden="true">
      <Skeleton className="mb-4 h-7 w-36" />
      <Skeleton className="mb-5 h-8 w-2/5" />
      <Skeleton className="h-[80vh] w-full rounded-lg" />
    </div>
  );
}
