import { MailIcon } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Gold outlined `mailto:` button. Only for the dark bands — gold text fails
 * contrast on the cream page. No hooks, so server and client components can
 * both render it.
 */
export default function ContactLink({
  href,
  children,
  className,
}: {
  href: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <a
      href={href}
      className={cn(
        "inline-flex h-8 shrink-0 items-center gap-1.5 rounded-md border border-brand/60 px-2.5 text-xs font-semibold text-brand transition-colors",
        "hover:bg-brand/10 focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none",
        className,
      )}
    >
      <MailIcon className="size-3.5" aria-hidden="true" />
      {children}
    </a>
  );
}
