import * as React from "react";
import { Eye, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const Input = React.forwardRef(
  ({ className, type, showPasswordToggle = false, startIcon = null, ...props }, ref) => {
    const [showPassword, setShowPassword] = React.useState(false);
    const isPasswordType = type === "password";
    const shouldShowToggle = isPasswordType && showPasswordToggle;
    const hasStartIcon = Boolean(startIcon);
    const needsRelative = hasStartIcon || shouldShowToggle;

    return (
      <div
        data-slot="input-wrapper"
        className={cn(
          "flex h-10 w-full min-w-0 items-center overflow-hidden rounded-sm border border-border bg-input transition-[box-shadow,ring-width] duration-200 ease-in-out",
          needsRelative && "relative",
          "focus-within:border-transparent focus-within:ring-ring/70 focus-within:ring-[2px]",
          "has-[[aria-invalid=true]]:ring-destructive has-[[aria-invalid=true]]:ring-1",
          "has-[[aria-invalid=true]]:focus-within:ring-[2px]",
          "has-[:disabled]:pointer-events-none has-[:disabled]:opacity-70",
          className
        )}
      >
        {hasStartIcon ? (
          <span className="pointer-events-none absolute left-2.5 top-1/2 z-10 -translate-y-1/2 text-muted-foreground [&_svg]:size-4 [&_svg]:shrink-0">
            {startIcon}
          </span>
        ) : null}
        <input
          type={shouldShowToggle ? (showPassword ? "text" : "password") : type}
          data-slot="input"
          className={cn(
            "file:text-foreground placeholder:text-muted-foreground placeholder:select-none h-full w-full min-w-0 border-0 bg-transparent py-1 text-base outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:cursor-not-allowed md:text-sm",
            hasStartIcon ? "pl-8" : "pl-3",
            shouldShowToggle ? "pr-10" : "pr-3"
          )}
          ref={ref}
          {...props}
        />
        {shouldShowToggle ? (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute right-1 top-1 h-8 w-8 rounded-full"
            onMouseDown={(e) => {
              e.preventDefault();
            }}
            onClick={() => {
              setShowPassword(!showPassword);
            }}
            disabled={props.disabled}
            tabIndex={-1}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            <span className="sr-only">{showPassword ? "Hide password" : "Show password"}</span>
          </Button>
        ) : null}
      </div>
    );
  }
);

Input.displayName = "Input";

export { Input };
