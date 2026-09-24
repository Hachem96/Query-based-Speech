"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { MoonIcon, SunIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useT } from "@/components/locale-provider";

const OPTIONS = [
  { value: "light", Icon: SunIcon },
  { value: "dark", Icon: MoonIcon },
] as const;

export default function ThemeToggle() {
  const t = useT();
  const { theme, setTheme } = useTheme();
  // next-themes only knows the real theme after mount; render a neutral
  // group until then so SSR and the first client paint match.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const current = mounted ? theme : undefined;

  return (
    <div
      role="group"
      aria-label={t.theme.groupLabel}
      className="inline-flex overflow-hidden rounded-md border border-input bg-card p-0.5"
    >
      {OPTIONS.map(({ value, Icon }) => {
        const on = current === value;
        const label = t.theme[value];
        return (
          <Tooltip key={value}>
            <TooltipTrigger asChild>
              <button
                type="button"
                aria-pressed={on}
                aria-label={label}
                onClick={() => setTheme(value)}
                className={cn(
                  "grid size-7 place-items-center rounded-[4px] text-muted-foreground transition-colors",
                  "hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring/60 focus-visible:outline-none",
                  on && "bg-primary text-primary-foreground hover:text-primary-foreground",
                )}
              >
                <Icon className="size-3.5" aria-hidden="true" />
              </button>
            </TooltipTrigger>
            <TooltipContent>{label}</TooltipContent>
          </Tooltip>
        );
      })}
    </div>
  );
}
