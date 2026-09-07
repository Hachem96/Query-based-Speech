"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { MonitorIcon, MoonIcon, SunIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const OPTIONS = [
  { value: "light", label: "فاتح", Icon: SunIcon },
  { value: "dark", label: "داكن", Icon: MoonIcon },
  { value: "system", label: "حسب النظام", Icon: MonitorIcon },
] as const;

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  // next-themes only knows the real theme after mount; render a neutral
  // group until then so SSR and the first client paint match.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const current = mounted ? theme : undefined;

  return (
    <div
      role="group"
      aria-label="سمة العرض"
      className="inline-flex overflow-hidden rounded-md border border-input bg-card p-0.5"
    >
      {OPTIONS.map(({ value, label, Icon }) => {
        const on = current === value;
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
