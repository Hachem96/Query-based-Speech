import { Suspense } from "react";
import Link from "next/link";
import { TriangleAlertIcon } from "lucide-react";
import Filters from "@/components/Filters";
import VideoCard from "@/components/VideoCard";
import EmptyState from "@/components/EmptyState";
import { CardGridSkeleton, FiltersSkeleton } from "@/components/Skeletons";
import { Button } from "@/components/ui/button";
import { getFilterOptions, listVideos } from "@/lib/api";
import { getT } from "@/lib/i18n-server";

export const dynamic = "force-dynamic";

type SearchParams = Promise<{ subject?: string; year?: string }>;

async function FiltersSection() {
  const options = await getFilterOptions();
  if (options.subjects.length === 0 && options.years.length === 0) return null;
  return <Filters options={options} />;
}

async function VideoGrid({ subject, year }: { subject?: string; year?: string }) {
  const [videos, t] = await Promise.all([listVideos({ subject, year }), getT()]);

  if (videos.length === 0) {
    if (subject || year) {
      return (
        <EmptyState>
          <p className="m-0">{t.home.noMatches}</p>
          <Button variant="outline" asChild>
            <Link href="/">{t.home.clearFilters}</Link>
          </Button>
        </EmptyState>
      );
    }
    return (
      <EmptyState>
        <p className="m-0">{t.home.noVideos}</p>
      </EmptyState>
    );
  }

  return (
    <div className="grid-cards">
      {videos.map((v) => (
        <VideoCard key={v.id} video={v} t={t} />
      ))}
    </div>
  );
}

export default async function HomePage({ searchParams }: { searchParams: SearchParams }) {
  const { subject, year } = await searchParams;
  const t = await getT();

  return (
    <>
      <h1 className="mb-2 text-2xl font-bold tracking-tight sm:text-3xl">{t.home.title}</h1>
      <p className="mb-6 max-w-[62ch] text-muted-foreground">
        {t.home.lead}
      </p>

      <div
        role="note"
        className="mb-6 flex gap-3 rounded-md border-s-[3px] border-brand bg-brand-muted px-4 py-3 text-[13px]"
      >
        <TriangleAlertIcon className="mt-0.5 size-4 shrink-0 text-brand" aria-hidden="true" />
        <p className="m-0">{t.home.aiNote}</p>
      </div>

      <Suspense fallback={<FiltersSkeleton />}>
        <FiltersSection />
      </Suspense>

      <Suspense key={`${subject ?? ""}|${year ?? ""}`} fallback={<CardGridSkeleton />}>
        <VideoGrid subject={subject} year={year} />
      </Suspense>
    </>
  );
}
