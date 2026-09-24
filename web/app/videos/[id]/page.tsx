import { Suspense } from "react";
import { notFound } from "next/navigation";
import BackLink from "@/components/BackLink";
import VideoWatch from "@/components/VideoWatch";
import { WatchSkeleton } from "@/components/Skeletons";
import { getVideo } from "@/lib/api";
import { getT } from "@/lib/i18n-server";

export const dynamic = "force-dynamic";

export default async function VideoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const t = await getT();

  let video;
  try {
    video = await getVideo(id);
  } catch (err) {
    // A missing id is a 404; anything else (e.g. backend down) is a real
    // error and should surface through error.tsx.
    if (err instanceof Error && / 404\b/.test(err.message)) notFound();
    throw err;
  }

  const meta = [video.subject, video.year].filter(Boolean).join(" · ");

  return (
    <>
      <BackLink href="/">{t.video.back}</BackLink>
      <h1 dir="auto" className="mb-1 text-2xl font-bold tracking-tight text-start sm:text-3xl">
        {video.name}
      </h1>
      <p dir="auto" className="mb-5 text-sm text-muted-foreground tabular-nums text-start">
        {meta || "—"}
      </p>
      <Suspense fallback={<WatchSkeleton />}>
        <VideoWatch video={video} />
      </Suspense>
    </>
  );
}
