import { Suspense } from "react";
import Link from "next/link";
import { BookOpenIcon } from "lucide-react";
import EmptyState from "@/components/EmptyState";
import PageHero from "@/components/PageHero";
import { CardGridSkeleton } from "@/components/Skeletons";
import { cardClass, cardTitleClass, thumbClass, thumbImageClass } from "@/components/MediaCard";
import { listBooks, mediaUrl } from "@/lib/api";
import { getT } from "@/lib/i18n-server";

export const dynamic = "force-dynamic";

async function BookGrid() {
  const [books, t] = await Promise.all([listBooks(), getT()]);

  if (books.length === 0) {
    return (
      <EmptyState>
        <p className="m-0">{t.books.noBooks}</p>
      </EmptyState>
    );
  }

  return (
    <div className="grid-cards">
      {books.map((book) => {
        const cover = mediaUrl(book.coverUrl);
        const title = book.title ?? t.books.untitled;
        const meta = [book.author, book.year].filter(Boolean).join(" · ");
        return (
          <Link key={book.id} href={`/books/${book.id}`} className={cardClass}>
            <div className={thumbClass}>
              {cover ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={cover} alt={t.books.coverAlt(title)} loading="lazy" className={thumbImageClass} />
              ) : (
                <div className="grid size-full place-items-center bg-muted text-muted-foreground">
                  <BookOpenIcon className="size-8" aria-hidden="true" />
                </div>
              )}
            </div>
            <div className="flex flex-col gap-1">
              <h3 dir="auto" className={cardTitleClass}>
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

export default async function BooksPage() {
  const t = await getT();
  return (
    <>
      <PageHero title={t.books.title} />
      <div className="page-container py-10 sm:py-14">
        <Suspense fallback={<CardGridSkeleton count={6} />}>
          <BookGrid />
        </Suspense>
      </div>
    </>
  );
}
