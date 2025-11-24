import * as React from "react"
import { Eye, EyeOff } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

const Input = React.forwardRef(({ 
  className, 
  type,
  showPasswordToggle = false,
  ...props 
}, ref) => {
  const [showPassword, setShowPassword] = React.useState(false)
  const isPasswordType = type === "password"
  const shouldShowToggle = isPasswordType && showPasswordToggle

  const inputElement = (
    <input
      type={shouldShowToggle ? (showPassword ? "text" : "password") : type}
      data-slot="input"
      className={cn(
        "file:text-foreground placeholder:text-muted-foreground bg-input border border-border h-10 w-full min-w-0 rounded-sm px-3 py-1 text-base transition-[box-shadow,ring-width] duration-200 ease-in-out outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
        "focus-visible:border-transparent focus-visible:ring-ring/70 focus-visible:ring-[2px]",
        "aria-invalid:ring-destructive dark:aria-invalid:ring-destructive aria-invalid:ring-1",
        "aria-invalid:focus-visible:ring-[2px]",
        shouldShowToggle && "pr-10",
        className
      )}
      ref={ref}
      {...props} />
  )

  if (shouldShowToggle) {
    return (
      <div className="relative">
        {inputElement}
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="absolute right-1 top-1 h-8 w-8 rounded-full"
          onMouseDown={(e) => {
            e.preventDefault()
          }}
          onClick={() => {
            setShowPassword(!showPassword)
          }}
          disabled={props.disabled}
          tabIndex={-1}
        >
          {showPassword ? (
            <EyeOff className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
          <span className="sr-only">
            {showPassword ? "Hide password" : "Show password"}
          </span>
        </Button>
      </div>
    )
  }

  return inputElement
})

Input.displayName = "Input"

export { Input }