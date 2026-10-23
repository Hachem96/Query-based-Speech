import Link from "next/link";
import EmptyState from "@/components/EmptyState";
import { Button } from "@/components/ui/button";
import { getT } from "@/lib/i18n-server";

export default async function NotFound() {
  const t = await getT();
  return (
    <div className="page-container py-12 sm:py-16">
      <EmptyState>
        <p className="m-0 text-foreground">{t.errors.notFound}</p>
        <Button variant="outline" asChild>
          <Link href="/">{t.errors.backToVideos}</Link>
        </Button>
      </EmptyState>
    </div>
  );
}
