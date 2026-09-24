"use client";

import { useEffect } from "react";
import EmptyState from "@/components/EmptyState";
import { Button } from "@/components/ui/button";
import { useT } from "@/components/locale-provider";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const t = useT();
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <EmptyState role="alert">
      <p className="m-0 text-foreground">{t.errors.loadFailed}</p>
      <p className="m-0 max-w-[48ch] text-sm">
        {t.errors.loadFailedHint}
      </p>
      <Button type="button" onClick={reset}>
        {t.errors.retry}
      </Button>
    </EmptyState>
  );
}
