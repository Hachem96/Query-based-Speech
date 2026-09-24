"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
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
            playsInline
            className="aspect-video w-full rounded-lg bg-black shadow-xl shadow-black/15 dark:shadow-black/50"
          />
        ) : (
          <EmptyBox>{t.video.fileMissing}</EmptyBox>
        )}
      </div>

      <div className="flex flex-col gap-4">
        <section
          aria-label={t.video.docsLabel}
          className="flex flex-col gap-2 rounded-lg border bg-card p-3"
        >
          {docs.map(({ label, href, Icon }) =>
            href ? (
              <Button key={label} variant="outline" className="justify-start" asChild>
                <a href={href} target="_blank" rel="noreferrer">
                  <Icon data-icon="inline-start" aria-hidden="true" />
                  {label}
                </a>
              </Button>
            ) : (
              <Button
                key={label}
                variant="outline"
                className="justify-start"
                disabled
                title={t.video.docUnavailable}
              >
                <Icon data-icon="inline-start" aria-hidden="true" />
                {label}
              </Button>
            ),
          )}
        </section>

        <form onSubmit={onAsk} className="flex flex-col gap-3 rounded-lg border bg-card p-4">
          <h3 className="m-0 flex items-center gap-2 text-[15px] font-bold">
            <MessageSquareIcon className="size-4 text-brand" aria-hidden="true" />
            {t.video.askHeading}
          </h3>
          {/* dir="auto": a question typed in English flows LTR, Arabic flows RTL. */}
          <Textarea
            dir="auto"
            placeholder={t.video.askPlaceholder}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label={t.video.askLabel}
            className="min-h-26 bg-background"
          />
          <Button type="submit" disabled={loading || !query.trim()} className="w-full">
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
      </div>
    </div>
  );
}

function EmptyBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid aspect-video place-items-center rounded-lg border bg-card text-muted-foreground">
      <p className="m-0">{children}</p>
    </div>
  );
}
