import { MegaphoneIcon } from "lucide-react";
import { getT } from "@/lib/i18n-server";

/**
 * Site-wide notice strip between the header and each page's hero. A slightly
 * darker band (`bg-night`) than the two ink bands around it, so it reads as
 * its own line without breaking the dark run at the top of the page.
 */
export default async function AnnouncementBar() {
  const t = await getT();

  return (
    <div role="note" className="dark border-b bg-night text-foreground">
      <p className="page-container m-0 flex items-center justify-center gap-2 py-2 text-center text-[13px] text-muted-foreground">
        {/* The megaphone points forward, so mirror it in RTL. */}
        <MegaphoneIcon className="size-4 shrink-0 text-brand rtl:-scale-x-100" aria-hidden="true" />
        <span>{t.layout.announcement}</span>
      </p>
    </div>
  );
}
