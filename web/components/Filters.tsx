"use client";

import { useId } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import type { FilterOptions } from "@/lib/api";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useT } from "@/components/locale-provider";

// Radix Select forbids `""` as an item value, so "no filter" is a sentinel.
const ALL = "__all__";

export default function Filters({ options }: { options: FilterOptions }) {
  const t = useT();
  const router = useRouter();
  const params = useSearchParams();
  const subjectId = useId();
  const yearId = useId();

  function update(key: "subject" | "year", value: string) {
    const next = new URLSearchParams(params.toString());
    if (value && value !== ALL) next.set(key, value);
    else next.delete(key);
    router.push(next.toString() ? `/?${next}` : "/");
  }

  return (
    <div className="mb-7 flex flex-wrap gap-4">
      {options.subjects.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor={subjectId}
            className="text-xs font-semibold tracking-wide text-muted-foreground"
          >
            {t.filters.subject}
          </label>
          <Select
            value={params.get("subject") ?? ALL}
            onValueChange={(v) => update("subject", v)}
          >
            <SelectTrigger id={subjectId} className="min-w-48 bg-card">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>{t.filters.allSubjects}</SelectItem>
              {options.subjects.map((s) => (
                <SelectItem key={s} value={s}>
                  {/* Subject names may be Latin script — let each decide its own direction. */}
                  <span dir="auto">{s}</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {options.years.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <label
            htmlFor={yearId}
            className="text-xs font-semibold tracking-wide text-muted-foreground"
          >
            {t.filters.year}
          </label>
          <Select
            value={params.get("year") ?? ALL}
            onValueChange={(v) => update("year", v)}
          >
            <SelectTrigger id={yearId} className="min-w-36 bg-card tabular-nums">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>{t.filters.allYears}</SelectItem>
              {options.years.map((y) => (
                <SelectItem key={y} value={String(y)} className="tabular-nums">
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}
    </div>
  );
}
