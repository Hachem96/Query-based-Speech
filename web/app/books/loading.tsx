import { CardGridSkeleton, PageTitleSkeleton } from "@/components/Skeletons";

export default function Loading() {
  return (
    <>
      <PageTitleSkeleton />
      <CardGridSkeleton count={6} />
    </>
  );
}
