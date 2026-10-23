"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  ArrowRightIcon,
  FileTextIcon,
  LanguagesIcon,
  ListIcon,
  MessageSquareIcon,
  PlayIcon,
  SearchIcon,
} from "lucide-react";
import { mediaUrl, runInference, type InferenceResult, type Video } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { useT } from "@/components/locale-provider";

function fmt(seconds: number): string {
  if (!Number.isFinite(seconds)) return "00:00";
  const s = Math.max(0, Math.floor(seconds));
  return `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;
}

/** Timestamps/ranges are LTR data even inside RTL prose. */
function Time({ children }: { children: React.ReactNode }) {
  return (
    <span dir="ltr" className="inline-block tabular-nums">
      {children}
    </span>
  );
}

export default function VideoWatch({ video }: { video: Video }) {
  const t = useT();
  const videoRef = useRef<HTMLVideoElement>(null);
  const searchParams = useSearchParams();
  const docsHeadingId = useId();
  const src = mediaUrl(video.videoUrl);

  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InferenceResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Deep link: /videos/1?t=125 starts playback at 125s.
  useEffect(() => {
    const t = Number(searchParams.get("t"));
    if (!t || !videoRef.current) return;
    const el = videoRef.current;
    const seek = () => {
      el.currentTime = t;
    };
    if (el.readyState >= 1) seek();
    else el.addEventListener("loadedmetadata", seek, { once: true });
  }, [searchParams]);

  function seekTo(seconds: number) {
    const el = videoRef.current;
    if (!el) return;
    el.currentTime = seconds;
    void el.play().catch(() => {});
  }

  async function onAsk(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runInference(video.name, query.trim());
      setResult(res);
      seekTo(res.startTimeStamp);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : t.video.connectionError,
      );
    } finally {
      setLoading(false);
    }
  }

  const docs = [
    { label: t.video.transcript, href: mediaUrl(video.transcriptionUrl), Icon: FileTextIcon },
    { label: t.video.summary, href: mediaUrl(video.summaryUrl), Icon: ListIcon },
    { label: t.video.translation, href: mediaUrl(video.translationUrl), Icon: LanguagesIcon },
  ];

  return (
    <div className="watch-grid">
      <div>
        {src ? (
          <video
            ref={videoRef}
            src={src}
            controls
            controlsList="nodownload"
            onContextMenu={(e) => e.preventDefault()}
            playsInline
            className="aspect-video w-full rounded-lg border bg-black"
          />
        ) : (
          <EmptyBox>{t.video.fileMissing}</EmptyBox>
        )}
      </div>

      <div className="flex flex-col gap-5">
        {/* The ask panel is a dark band, echoing the home hero; inside it
            `primary` resolves to gold. */}
        <form
          onSubmit={onAsk}
          className="dark band-pattern flex flex-col gap-4 rounded-lg border bg-ink p-5 text-foreground"
        >
          <div>
            <h2 className="m-0 flex items-center gap-2.5 text-xl font-bold">
              <MessageSquareIcon className="size-5 text-brand" aria-hidden="true" />
              {t.video.askHeading}
            </h2>
            <span aria-hidden="true" className="mt-3 block h-px w-12 bg-brand" />
          </div>
          {/* dir="auto": a question typed in English flows LTR, Arabic flows RTL. */}
          <Textarea
            dir="auto"
            placeholder={t.video.askPlaceholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label={t.video.askLabel}
            className="min-h-26 bg-night/60 dark:bg-night/60"
          />
          <Button type="submit" disabled={loading || !query.trim()} className="h-10 w-full font-semibold">
            <SearchIcon data-icon="inline-start" aria-hidden="true" />
            {loading ? t.video.searching : t.video.search}
          </Button>

          <div aria-live="polite" className="flex flex-col gap-2.5 empty:hidden">
            {error && (
              <p role="alert" className="m-0 text-sm font-semibold text-destructive">
                {error}
              </p>
            )}

            {loading && (
              <div className="flex flex-col gap-2.5 rounded-md bg-brand-muted p-3" aria-busy="true">
                <Skeleton className="h-8 w-1/2" />
                <Skeleton className="h-3 w-3/4" />
              </div>
            )}

            {!loading && result && (
              <div className="flex flex-col items-start gap-2.5 rounded-md border-s-[3px] border-brand bg-brand-muted p-3 text-sm">
                <Button type="button" size="sm" onClick={() => seekTo(result.startTimeStamp)}>
                  <PlayIcon data-icon="inline-start" aria-hidden="true" />
                  {t.video.jumpTo} <Time>{fmt(result.startTimeStamp)}</Time>
                </Button>
                <p className="m-0 text-muted-foreground">
                  {t.video.segment}{" "}
                  <Time>
                    {fmt(result.startTimeStamp)} → {fmt(result.endTimeStamp)}
                  </Time>{" "}
                  ({t.video.seconds(Math.round(result.duration))})
                </p>
              </div>
            )}
          </div>
        </form>

        <section aria-labelledby={docsHeadingId} className="rounded-lg border bg-card">
          <h2 id={docsHeadingId} className="eyebrow m-0 border-b px-4 py-3 font-sans">
            {t.video.docsLabel}
          </h2>
          <ul className="m-0 list-none divide-y p-0">
            {docs.map(({ label, href, Icon }) => (
              <li key={label}>
                {href ? (
                  <a
                    href={href}
                    target="_blank"
                    rel="noreferrer"
                    className="group/doc flex items-center gap-3 px-4 py-3 text-sm font-semibold transition-colors hover:bg-muted/60 hover:text-primary focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none focus-visible:ring-inset"
                  >
                    <Icon className="size-4 text-muted-foreground group-hover/doc:text-primary" aria-hidden="true" />
                    <span className="flex-1">{label}</span>
                    {/* Drawn for LTR; mirrored (and nudged) toward the reading direction. */}
                    <ArrowRightIcon
                      className="size-4 text-muted-foreground transition-transform group-hover/doc:translate-x-0.5 rtl:-scale-x-100 rtl:group-hover/doc:-translate-x-0.5"
                      aria-hidden="true"
                    />
                  </a>
                ) : (
                  <div className="flex items-center gap-3 px-4 py-3 text-sm text-muted-foreground">
                    <Icon className="size-4 opacity-60" aria-hidden="true" />
                    <span className="flex-1 opacity-60">{label}</span>
                    <span className="text-xs">{t.video.docUnavailable}</span>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}

function EmptyBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid aspect-video place-items-center rounded-lg border bg-muted text-muted-foreground">
      <p className="m-0">{children}</p>
    </div>
  );
}
