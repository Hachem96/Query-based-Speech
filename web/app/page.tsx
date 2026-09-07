import { Suspense } from "react";
import Link from "next/link";
import { TriangleAlertIcon } from "lucide-react";
import Filters from "@/components/Filters";
import VideoCard from "@/components/VideoCard";
import EmptyState from "@/components/EmptyState";
import { CardGridSkeleton, FiltersSkeleton } from "@/components/Skeletons";
import { Button } from "@/components/ui/button";
import { getFilterOptions, listVideos } from "@/lib/api";

export const dynamic = "force-dynamic";

type SearchParams = Promise<{ subject?: string; year?: string }>;

async function FiltersSection() {
  const options = await getFilterOptions();
  if (options.subjects.length === 0 && options.years.length === 0) return null;
  return <Filters options={options} />;
}

async function VideoGrid({ subject, year }: { subject?: string; year?: string }) {
  const videos = await listVideos({ subject, year });

  if (videos.length === 0) {
    if (subject || year) {
      return (
        <EmptyState>
          <p className="m-0">لا توجد فيديوهات تطابق هذه المرشِّحات.</p>
          <Button variant="outline" asChild>
            <Link href="/">مسح المرشِّحات</Link>
          </Button>
        </EmptyState>
      );
    }
    return (
      <EmptyState>
        <p className="m-0">لم تُضَف أي فيديوهات إلى المكتبة بعد.</p>
      </EmptyState>
    );
  }

  return (
    <div className="grid-cards">
      {videos.map((v) => (
        <VideoCard key={v.id} video={v} />
      ))}
    </div>
  );
}

export default async function HomePage({ searchParams }: { searchParams: SearchParams }) {
  const { subject, year } = await searchParams;

  return (
    <>
      <h1 className="mb-2 text-2xl font-bold tracking-tight sm:text-3xl">مكتبة الفيديوهات</h1>
      <p className="mb-6 max-w-[62ch] text-muted-foreground">
        اختر محاضرة، اطرح سؤالاً بالعربية، وسينقلك المشغّل مباشرةً إلى المقطع الذي يُجيب عنه.
      </p>

      <div
        role="note"
        className="mb-6 flex gap-3 rounded-md border-s-[3px] border-brand bg-brand-muted px-4 py-3 text-[13px]"
      >
        <TriangleAlertIcon className="mt-0.5 size-4 shrink-0 text-brand" aria-hidden="true" />
        <div className="flex flex-col gap-1">
          <p className="m-0">
            النص المكتوب مُولَّد بالذكاء الاصطناعي وقد يحتوي على أخطاء. نرحّب بملاحظاتكم.
          </p>
          {/* English copy is LTR content inside an RTL page: set both dir and lang. */}
          <p dir="ltr" lang="en" className="m-0 text-start text-muted-foreground">
            The transcription is AI-generated and may contain errors. We welcome your feedback.
          </p>
        </div>
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
