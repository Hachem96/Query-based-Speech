import { notFound } from "next/navigation";
import BackLink from "@/components/BackLink";
import EmptyState from "@/components/EmptyState";
import { getBook, mediaUrl } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function BookPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

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
  const title = book.title ?? "بدون عنوان";

  return (
    <>
      <BackLink href="/books">العودة إلى الكتب</BackLink>
      <h1 dir="auto" className="mb-5 text-2xl font-bold tracking-tight text-start sm:text-3xl">
        {title}
      </h1>
      {pdf ? (
        <iframe src={pdf} title={title} className="h-[80vh] w-full rounded-lg border bg-card" />
      ) : (
        <EmptyState>
          <p className="m-0">ملف PDF لهذا الكتاب غير متوفر.</p>
        </EmptyState>
      )}
    </>
  );
}
