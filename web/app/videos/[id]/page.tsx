import { Suspense } from "react";
import { notFound } from "next/navigation";
import BackLink from "@/components/BackLink";
import PageHero from "@/components/PageHero";
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
      <PageHero
        before={<BackLink href="/">{t.video.back}</BackLink>}
        eyebrow={meta ? <span className="tabular-nums">{meta}</span> : undefined}
        title={video.name}
        titleDir="auto"
      />
      <div className="page-container py-10 sm:py-14">
        <Suspense fallback={<WatchSkeleton />}>
          <VideoWatch video={video} />
        </Suspense>
      </div>
    </>
  );
}
