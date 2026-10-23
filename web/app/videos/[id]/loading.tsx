import { HeroSkeleton, WatchSkeleton } from "@/components/Skeletons";

export default function Loading() {
  return (
    <>
      <HeroSkeleton back />
      <div className="page-container py-10 sm:py-14">
        <WatchSkeleton />
      </div>
    </>
  );
}
