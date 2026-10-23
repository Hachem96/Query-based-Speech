import { CardGridSkeleton, FiltersSkeleton, HeroSkeleton } from "@/components/Skeletons";

export default function Loading() {
  return (
    <>
      <HeroSkeleton align="center" lead search />
      <div className="page-container py-10 sm:py-14">
        <FiltersSkeleton />
        <CardGridSkeleton />
      </div>
    </>
  );
}
