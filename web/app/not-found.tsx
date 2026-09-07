import Link from "next/link";
import EmptyState from "@/components/EmptyState";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <EmptyState>
      <p className="m-0 text-foreground">تعذّر العثور على هذه الصفحة.</p>
      <Button variant="outline" asChild>
        <Link href="/">العودة إلى الفيديوهات</Link>
      </Button>
    </EmptyState>
  );
}
