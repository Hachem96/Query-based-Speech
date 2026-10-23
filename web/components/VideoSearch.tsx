"use client";

import { useEffect, useId, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ArrowRightIcon, SearchIcon, XIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useT } from "@/components/locale-provider";

export default function VideoSearch() {
  const t = useT();
  const router = useRouter();
  const params = useSearchParams();
  const inputId = useId();
  const current = params.get("q") ?? "";
  const [value, setValue] = useState(current);

  // Keep the field in sync with back/forward navigation.
  useEffect(() => setValue(current), [current]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const q = value.trim();
    // A search replaces the subject/year filters rather than combining with them.
    router.push(q ? `/?${new URLSearchParams({ q })}` : "/");
  }

  function clear() {
    setValue("");
    router.push("/");
  }

  // Lives in the dark home hero: one bordered field with the gold (primary)
  // submit button inside it; the field shows focus for the input within.
  return (
    <form role="search" onSubmit={submit} className="mt-8 w-full max-w-2xl">
      <label htmlFor={inputId} className="sr-only">
        {t.search.label}
      </label>
      <div className="flex items-center gap-2 rounded-lg border border-input bg-night/60 p-1.5 ps-3.5 transition-[border-color,box-shadow] focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/30">
        <SearchIcon className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
        <input
          id={inputId}
          type="search"
          dir="auto"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={t.search.placeholder}
          maxLength={200}
          className="h-10 min-w-0 flex-1 bg-transparent text-base outline-none placeholder:text-muted-foreground [&::-webkit-search-cancel-button]:hidden"
        />
        {value && (
          <button
            type="button"
            onClick={clear}
            aria-label={t.search.clear}
            className="shrink-0 rounded-sm p-1 text-muted-foreground hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none"
          >
            <XIcon className="size-4" aria-hidden="true" />
          </button>
        )}
        <Button type="submit" className="h-10 px-4 font-semibold">
          {t.search.submit}
          {/* Drawn for LTR; mirrored so it points forward in RTL too. */}
          <ArrowRightIcon data-icon="inline-end" className="rtl:-scale-x-100" aria-hidden="true" />
        </Button>
      </div>
    </form>
  );
}
