import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority";
import { cn, debugWarn } from "@/lib/utils"

const buttonVariants = cva(
  "relative overflow-hidden inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background focus:outline-none active:outline-none disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 select-none cursor-pointer",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline:
          "border border-border bg-transparent hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

const Button = React.forwardRef(({ className, variant, size, onMouseDown, asChild = false, ...props }, ref) => {
  const Comp = asChild ? Slot : "button"

  const handleMouseDown = (e) => {
    const button = e.currentTarget
    const rect = button.getBoundingClientRect()
    const rippleSize = Math.max(rect.width, rect.height)
    const rippleRadius = rippleSize / 2
    const left = e.clientX - rect.left - rippleRadius
    const top = e.clientY - rect.top - rippleRadius

    const ripple = document.createElement("span")
    ripple.style.width = ripple.style.height = `${rippleSize}px`
    ripple.style.left = `${left}px`
    ripple.style.top = `${top}px`

    const classList = button.classList
    const isOutline = classList.contains('border') && classList.contains('bg-background')
    const isGhost = classList.contains('hover:bg-accent')
    const isLink = classList.contains('underline-offset-4')
    const isTransparentVariant = isGhost || isLink || isOutline

    const computedStyle = window.getComputedStyle(button)
    const backgroundColor = computedStyle.backgroundColor
    const textColor = computedStyle.color

    const getRGBFromColor = (color) => {
      try {
        const canvas = document.createElement('canvas')
        canvas.width = canvas.height = 1
        const ctx = canvas.getContext('2d')
        ctx.fillStyle = '#ffffff'
        ctx.fillRect(0, 0, 1, 1)
        ctx.fillStyle = color
        ctx.fillRect(0, 0, 1, 1)
        const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data
        return [r, g, b]
      } catch (e) {
        const temp = document.createElement('div')
        temp.style.color = color
        temp.style.position = 'absolute'
        temp.style.left = '-9999px'
        document.body.appendChild(temp)
        const computed = window.getComputedStyle(temp).color
        document.body.removeChild(temp)
        const match = computed.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/)
        if (match) {
          return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])]
        }
        throw new Error('Unable to parse color')
      }
    }

    if (isTransparentVariant) {
      const isDarkMode = document.documentElement.classList.contains('dark')
      try {
        const [r, g, b] = getRGBFromColor(textColor)
        if (isDarkMode) {
          ripple.style.background = `rgba(${r}, ${g}, ${b}, 0.3)`
        } else {
          ripple.style.background = `rgba(${r}, ${g}, ${b}, 0.15)`
        }
      } catch (e) {
        debugWarn('Failed to parse text color:', textColor, e)
        const isDarkMode = document.documentElement.classList.contains('dark')
        if (isDarkMode) {
          ripple.style.background = 'rgba(200, 200, 200, 0.4)'
        } else {
          ripple.style.background = 'rgba(100, 100, 100, 0.2)'
        }
      }
    } else {
      try {
        const [r, g, b] = getRGBFromColor(backgroundColor)
        const brightness = (r * 299 + g * 587 + b * 114) / 1000
        const isDarkMode = document.documentElement.classList.contains('dark')
        if (brightness > 128) {
          const opacity = isDarkMode ? 0.25 : 0.15
          ripple.style.background = `rgba(0, 0, 0, ${opacity})`
        } else {
          const opacity = isDarkMode ? 0.3 : 0.4
          ripple.style.background = `rgba(255, 255, 255, ${opacity})`
        }
      } catch (e) {
        const isDarkMode = document.documentElement.classList.contains('dark')
        if (isDarkMode) {
          ripple.style.background = 'rgba(200, 200, 200, 0.4)'
        } else {
          ripple.style.background = 'rgba(100, 100, 100, 0.2)'
        }
      }
    }

    ripple.className = "ripple"
    button.appendChild(ripple)
    setTimeout(() => {
      ripple.remove()
    }, 800)

    if (onMouseDown) onMouseDown(e)
  }

  return (
    <Comp
      className={cn(buttonVariants({ variant, size, className }))}
      ref={ref}
      onMouseDown={handleMouseDown}
      {...props}
    />
  );
})
Button.displayName = "Button"

export { Button, buttonVariants }