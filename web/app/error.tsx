"use client";

import { useEffect } from "react";
import EmptyState from "@/components/EmptyState";
import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <EmptyState role="alert">
      <p className="m-0 text-foreground">تعذّر تحميل هذه الصفحة.</p>
      <p className="m-0 max-w-[48ch] text-sm">
        قد يكون الخادم غير متاح. تأكّد من أن واجهة الـ API قيد التشغيل ويمكن الوصول إليها.
      </p>
      <Button type="button" onClick={reset}>
        إعادة المحاولة
      </Button>
    </EmptyState>
  );
}
