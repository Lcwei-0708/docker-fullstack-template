import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({
  className,
  ...props
}) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        "placeholder:text-muted-foreground placeholder:select-none bg-input border border-border w-full min-w-0 rounded-sm px-3 py-2 text-base transition-[box-shadow,ring-width] duration-200 ease-in-out outline-none md:text-sm",
        "focus-visible:border-transparent focus-visible:ring-ring/70 focus-visible:ring-[2px]",
        "aria-invalid:ring-destructive dark:aria-invalid:ring-destructive aria-invalid:ring-1",
        "aria-invalid:focus-visible:ring-[2px]",
        "disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-70",
        "flex field-sizing-content min-h-16",
        className
      )}
      {...props}
    />
  );
}

export { Textarea }