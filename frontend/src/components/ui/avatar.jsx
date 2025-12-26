import * as React from "react"
import { cn } from "@/lib/utils"

const Avatar = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      "relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full",
      className
    )}
    {...props}
  />
))
Avatar.displayName = "Avatar"

const AvatarImage = React.forwardRef(({ className, src, onError, ...props }, ref) => {
  const [imageError, setImageError] = React.useState(false)

  const handleError = (e) => {
    setImageError(true)
    if (onError) onError(e)
  }

  // If no src or image error, don't render the image
  if (!src || imageError) {
    return null
  }

  return (
    <img
      ref={ref}
      src={src}
      className={cn("aspect-square h-full w-full object-cover relative z-10", className)}
      onError={handleError}
      {...props}
    />
  )
})
AvatarImage.displayName = "AvatarImage"

const AvatarFallback = React.forwardRef(({ className, children, ...props }, ref) => {
  // If children is provided, use it; otherwise show default fallback
  const displayText = children || "U"
  
  // If it's a single character or initials (2 chars), show as is
  // Otherwise, show first character of the text
  const fallbackText = displayText.length <= 2 
    ? displayText 
    : displayText.charAt(0).toUpperCase()
  
  return (
    <div
      ref={ref}
      className={cn(
        "absolute inset-0 flex h-full w-full items-center justify-center rounded-full bg-muted text-muted-foreground text-sm font-medium",
        className
      )}
      {...props}
    >
      {fallbackText}
    </div>
  )
})
AvatarFallback.displayName = "AvatarFallback"

export { Avatar, AvatarImage, AvatarFallback }