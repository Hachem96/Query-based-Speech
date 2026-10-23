import { Suspense, cache } from "react";
import Link from "next/link";
import { InfoIcon } from "lucide-react";
import ContactLink from "@/components/ContactLink";
import Filters from "@/components/Filters";
import PageHero from "@/components/PageHero";
import VideoCard from "@/components/VideoCard";
import VideoSearch from "@/components/VideoSearch";
import EmptyState from "@/components/EmptyState";
import { CardGridSkeleton, FiltersSkeleton, VideoSearchSkeleton } from "@/components/Skeletons";
import { Button } from "@/components/ui/button";
import { getFilterOptions, listVideos, searchVideos } from "@/lib/api";
import { getContactEmail, mailtoHref } from "@/lib/contact";
import { getT } from "@/lib/i18n-server";

export const dynamic = "force-dynamic";

type SearchParams = Promise<{ subject?: string; year?: string; q?: string }>;

// The result count and the grid share one search request per page render.
const search = cache(searchVideos);

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

async function ResultCount({ q }: { q: string }) {
  const [videos, t] = await Promise.all([search(q), getT()]);
  if (videos.length === 0) return null;
  return <> · {t.search.resultCount(videos.length)}</>;
}

async function SearchResults({ q }: { q: string }) {
  const [videos, t] = await Promise.all([search(q), getT()]);

  if (videos.length === 0) {
    return (
      <EmptyState>
        <p className="m-0">{t.search.noResults}</p>
        <Button variant="outline" asChild>
          <Link href="/">{t.search.clear}</Link>
        </Button>
      </EmptyState>
    );
  }

  // Each result opens its video already seeking to the segment that answers `q`.
  return (
    <div className="grid-cards">
      {videos.map((v) => (
        <VideoCard key={v.id} video={v} t={t} query={q} />
      ))}
    </div>
  );
}

export default async function HomePage({ searchParams }: { searchParams: SearchParams }) {
  const { subject, year, q: rawQ } = await searchParams;
  const q = rawQ?.trim();
  const t = await getT();
  const contactEmail = getContactEmail();

  return (
    <>
      <PageHero align="center" title={t.home.title} lead={t.home.lead}>
        <Suspense fallback={<VideoSearchSkeleton />}>
          <VideoSearch />
        </Suspense>

        <div
          role="note"
          className="mt-5 flex max-w-2xl flex-wrap items-center justify-center gap-x-4 gap-y-2.5 text-[13px] text-muted-foreground"
        >
          <span className="flex gap-2.5 text-start">
            <InfoIcon className="mt-0.5 size-4 shrink-0 text-brand" aria-hidden="true" />
            <p className="m-0">{t.home.aiNote}</p>
          </span>
          {contactEmail && (
            <ContactLink href={mailtoHref(contactEmail, t.contact.feedbackSubject)} className="h-7">
              {t.contact.feedback}
            </ContactLink>
          )}
        </div>
      </PageHero>

      <div className="page-container py-10 sm:py-14">
        {q ? (
          <>
            <p className="mb-6 text-sm text-muted-foreground">
              {t.search.resultsFor} <span dir="auto" className="font-semibold text-foreground">“{q}”</span>
              <span role="status">
                <Suspense key={`q:${q}`} fallback={null}>
                  <ResultCount q={q} />
                </Suspense>
              </span>
            </p>
            <Suspense key={`q:${q}`} fallback={<CardGridSkeleton count={5} />}>
              <SearchResults q={q} />
            </Suspense>
          </>
        ) : (
          <>
            <Suspense fallback={<FiltersSkeleton />}>
              <FiltersSection />
            </Suspense>

            <Suspense key={`${subject ?? ""}|${year ?? ""}`} fallback={<CardGridSkeleton />}>
              <VideoGrid subject={subject} year={year} />
            </Suspense>
          </>
        )}
      </div>
    </>
  );
}
