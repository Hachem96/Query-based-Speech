import { cn } from "@/lib/utils";

export default function EmptyState({
  children,
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-3.5 rounded-lg border bg-card px-6 pt-12 pb-13 text-center text-muted-foreground",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
