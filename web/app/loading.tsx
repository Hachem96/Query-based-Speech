import { CardGridSkeleton, FiltersSkeleton, PageTitleSkeleton } from "@/components/Skeletons";

export default function Loading() {
  return (
    <>
      <PageTitleSkeleton lead />
      <FiltersSkeleton />
      <CardGridSkeleton />
    </>
  );
}
