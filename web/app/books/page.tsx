import { Suspense } from "react";
import Link from "next/link";
import { BookOpenIcon } from "lucide-react";
import EmptyState from "@/components/EmptyState";
import { CardGridSkeleton } from "@/components/Skeletons";
import { cardClass } from "@/components/MediaCard";
import { listBooks, mediaUrl } from "@/lib/api";

export const dynamic = "force-dynamic";

async function BookGrid() {
  const books = await listBooks();

  if (books.length === 0) {
    return (
      <EmptyState>
        <p className="m-0">لم تُضَف أي كتب إلى المكتبة بعد.</p>
      </EmptyState>
    );
  }

  return (
    <div className="grid-cards">
      {books.map((book) => {
        const cover = mediaUrl(book.coverUrl);
        const title = book.title ?? "بدون عنوان";
        const meta = [book.author, book.year].filter(Boolean).join(" · ");
        return (
          <Link key={book.id} href={`/books/${book.id}`} className={cardClass}>
            {cover ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={cover}
                alt={`غلاف كتاب: ${title}`}
                loading="lazy"
                className="aspect-video w-full border-b object-cover"
              />
            ) : (
              <div className="grid aspect-video w-full place-items-center border-b bg-muted text-muted-foreground">
                <BookOpenIcon className="size-8" aria-hidden="true" />
              </div>
            )}
            <div className="flex flex-1 flex-col gap-1.5 px-4 pt-3.5 pb-4">
              <h3 dir="auto" className="m-0 text-[15px] leading-snug font-semibold text-start">
                {title}
              </h3>
              <span dir="auto" className="text-[13px] text-muted-foreground tabular-nums text-start">
                {meta || "—"}
              </span>
            </div>
          </Link>
        );
      })}
    </div>
  );
}

export default function BooksPage() {
  return (
    <>
      <h1 className="mb-5 text-2xl font-bold tracking-tight sm:text-3xl">مكتبة الكتب</h1>
      <Suspense fallback={<CardGridSkeleton count={6} />}>
        <BookGrid />
      </Suspense>
    </>
  );
}
