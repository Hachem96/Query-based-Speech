import Link from "next/link";
import { ArrowLeftIcon } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * "Back" must point toward the start of the reading direction: left in LTR,
 * right in RTL. The icon is drawn for LTR and mirrored under `dir="rtl"`.
 */
export default function BackLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Button variant="outline" size="sm" className="mb-4" asChild>
      <Link href={href}>
        <ArrowLeftIcon data-icon="inline-start" className="rtl:-scale-x-100" aria-hidden="true" />
        {children}
      </Link>
    </Button>
  );
}
