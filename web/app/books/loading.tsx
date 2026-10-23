import { CardGridSkeleton, HeroSkeleton } from "@/components/Skeletons";

export default function Loading() {
  return (
    <>
      <HeroSkeleton />
      <div className="page-container py-10 sm:py-14">
        <CardGridSkeleton count={6} />
      </div>
    </>
  );
}
