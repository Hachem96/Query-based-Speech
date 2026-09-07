import Link from "next/link";
import { VideoIcon } from "lucide-react";
import { mediaUrl, type Video } from "@/lib/api";
import { cardClass } from "@/components/MediaCard";

export default function VideoCard({ video }: { video: Video }) {
  const cover = mediaUrl(video.coverUrl);
  const meta = [video.subject, video.year].filter(Boolean).join(" · ");

  return (
    <Link href={`/videos/${video.id}`} className={cardClass}>
      {cover ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img
          src={cover}
          alt={`غلاف فيديو: ${video.name}`}
          loading="lazy"
          className="aspect-video w-full border-b object-cover"
        />
      ) : (
        <div className="grid aspect-video w-full place-items-center border-b bg-muted text-muted-foreground">
          <VideoIcon className="size-8" aria-hidden="true" />
        </div>
      )}
      <div className="flex flex-1 flex-col gap-1.5 px-4 pt-3.5 pb-4">
        {/* Titles may be Arabic, Latin, or mixed — dir="auto" picks per title. */}
        <h3 dir="auto" className="m-0 text-[15px] leading-snug font-semibold text-start">
          {video.name}
        </h3>
        <span dir="auto" className="text-[13px] text-muted-foreground tabular-nums text-start">
          {meta || "—"}
        </span>
      </div>
    </Link>
  );
}
