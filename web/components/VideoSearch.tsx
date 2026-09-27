"use client";

import { useEffect, useId, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { SearchIcon, XIcon } from "lucide-react";
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

  return (
    <form role="search" onSubmit={submit} className="mb-6 flex max-w-xl gap-2">
      <label htmlFor={inputId} className="sr-only">
        {t.search.label}
      </label>
      <div className="relative flex-1">
        <SearchIcon
          className="pointer-events-none absolute start-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden="true"
        />
        <input
          id={inputId}
          type="search"
          dir="auto"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={t.search.placeholder}
          maxLength={200}
          className="h-9 w-full rounded-md border bg-card ps-9 pe-9 text-sm shadow-xs outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 [&::-webkit-search-cancel-button]:hidden"
        />
        {value && (
          <button
            type="button"
            onClick={clear}
            aria-label={t.search.clear}
            className="absolute end-2 top-1/2 -translate-y-1/2 rounded-sm p-1 text-muted-foreground hover:text-foreground"
          >
            <XIcon className="size-4" aria-hidden="true" />
          </button>
        )}
      </div>
      <Button type="submit">{t.search.submit}</Button>
    </form>
  );
}
