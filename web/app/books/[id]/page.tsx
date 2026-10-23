import { notFound } from "next/navigation";
import BackLink from "@/components/BackLink";
import EmptyState from "@/components/EmptyState";
import PageHero from "@/components/PageHero";
import { getBook, mediaUrl } from "@/lib/api";
import { getT } from "@/lib/i18n-server";

export const dynamic = "force-dynamic";

export default async function BookPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const t = await getT();

  let book;
  try {
    book = await getBook(id);
  } catch (err) {
    // A missing id is a 404; anything else (e.g. backend down) is a real
    // error and should surface through error.tsx.
    if (err instanceof Error && / 404\b/.test(err.message)) notFound();
    throw err;
  }

  const pdf = mediaUrl(book.pdfUrl);
  const title = book.title ?? t.books.untitled;
  const meta = [book.author, book.year].filter(Boolean).join(" · ");

  return (
    <>
      <PageHero
        before={<BackLink href="/books">{t.books.back}</BackLink>}
        eyebrow={meta || undefined}
        title={title}
        titleDir="auto"
      />
      <div className="page-container py-10 sm:py-14">
        {pdf ? (
          <iframe src={pdf} title={title} className="h-[80vh] w-full rounded-lg border bg-card" />
        ) : (
          <EmptyState>
            <p className="m-0">{t.books.pdfMissing}</p>
          </EmptyState>
        )}
      </div>
    </>
  );
}
