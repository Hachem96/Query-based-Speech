import Link from "next/link";
import { PlayIcon, VideoIcon } from "lucide-react";
import { mediaUrl, type Video } from "@/lib/api";
import { cardClass, cardTitleClass, thumbClass, thumbImageClass } from "@/components/MediaCard";
import type { Dictionary } from "@/lib/i18n";

/**
 * `query`: set for library-search results. The link then carries `?q=`, and
 * the video page asks that question itself and seeks to the answer.
 */
export default function VideoCard({ video, t, query }: { video: Video; t: Dictionary; query?: string }) {
  const cover = mediaUrl(video.coverUrl);
  const meta = [video.subject, video.year].filter(Boolean).join(" · ");
  const href = query ? `/videos/${video.id}?${new URLSearchParams({ q: query })}` : `/videos/${video.id}`;

  return (
    <Link href={href} className={cardClass}>
      <div className={thumbClass}>
        {cover ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={cover} alt={t.video.coverAlt(video.name)} loading="lazy" className={thumbImageClass} />
        ) : (
          <div className="grid size-full place-items-center bg-muted text-muted-foreground">
            <VideoIcon className="size-8" aria-hidden="true" />
          </div>
        )}
        {/* Play badge on hover. Media glyphs are never mirrored, even in RTL. */}
        <span
          aria-hidden="true"
          className="absolute inset-0 grid place-items-center bg-ink/0 transition-colors duration-200 group-hover:bg-ink/10"
        >
          <span className="grid size-12 scale-90 place-items-center rounded-full border border-gold bg-ink/80 text-gold opacity-0 transition duration-200 group-hover:scale-100 group-hover:opacity-100 motion-reduce:transition-none">
            <PlayIcon className="size-5 translate-x-px fill-current" />
          </span>
        </span>
      </div>
      <div className="flex flex-col gap-1">
        {/* Titles may be Arabic, Latin, or mixed — dir="auto" picks per title. */}
        <h3 dir="auto" className={cardTitleClass}>
          {video.name}
        </h3>
        <span dir="auto" className="text-[13px] text-muted-foreground tabular-nums text-start">
          {meta || "—"}
        </span>
        {query && (
          <span className="mt-0.5 flex items-center gap-1.5 text-[13px] font-semibold text-primary">
            <PlayIcon className="size-3 fill-current" aria-hidden="true" />
            {t.search.opensAtAnswer}
          </span>
        )}
      </div>
    </Link>
  );
}
