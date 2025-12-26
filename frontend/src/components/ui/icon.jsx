import * as React from "react"
import { cn, debugWarn } from "@/lib/utils"

const iconRegistry = {}

const iconModules = import.meta.glob("@/assets/icons/*.svg", { eager: true, query: "?raw", import: "default" })

function getIconPair(iconName) {
  const activeEntry = Object.entries(iconModules).find(([path]) => 
    path.includes(`${iconName}-active.svg`)
  )
  
  const inactiveEntry = Object.entries(iconModules).find(([path]) => 
    path.includes(`${iconName}.svg`)
  )

  if (activeEntry && inactiveEntry) {
    return {
      active: activeEntry[1],
      inactive: inactiveEntry[1],
    }
  }
  return null
}

/**
 * Icon component that displays icons from the assets folder
 * Supports active/inactive state switching for icons in assets/icons/
 * Allows control over stroke and fill properties via CSS
 * 
 * @param {string} name - Icon name (must match a key in iconRegistry or be in assets/icons/)
 * @param {boolean} [isActive=false] - Whether to show active version (for icons in assets/icons/)
 * @param {string} [className] - Additional CSS classes
 * @param {number|string} [size] - Icon size (default: 24, can be number or Tailwind size class like "w-6 h-6")
 * @param {string} [alt] - Alt text for the icon
 * @param {string} [fill] - Fill color (default: "currentColor", can be CSS color or "none")
 * @param {string} [stroke] - Stroke color (default: "currentColor", can be CSS color or "none")
 * @param {string|number} [strokeWidth] - Stroke width (default: undefined, uses SVG's original stroke-width)
 * @param {object} [props] - Additional props to pass to the SVG element
 * 
 * @example
 * <Icon name="nginx" size={32} />
 * <Icon name="home" isActive={true} size="w-8 h-8" fill="currentColor" />
 * <Icon name="profile" isActive={false} className="text-primary" stroke="currentColor" strokeWidth={2} />
 */
export function Icon({
  name,
  isActive = false,
  className,
  size = 24,
  alt,
  fill,
  stroke,
  strokeWidth,
  ...props
}) {
  const registryIcon = iconRegistry[name]

  const iconPair = React.useMemo(() => {
    if (!registryIcon && name) {
      const pair = getIconPair(name)
      if (pair) {
        iconRegistry[name] = pair
        return pair
      }
    }
    return null
  }, [name, registryIcon])

  let iconContent = null

  if (registryIcon) {
    if (typeof registryIcon === "object" && registryIcon.active && registryIcon.inactive) {
      iconContent = isActive ? registryIcon.active : registryIcon.inactive
    } else {
      iconContent = registryIcon
    }
  } else if (iconPair) {
    iconContent = isActive ? iconPair.active : iconPair.inactive
  }

  if (!iconContent) {
    debugWarn(`Icon "${name}" not found. Available icons: ${Object.keys(iconRegistry).join(", ")}`)
    return null
  }

  const fillColor = fill !== undefined 
    ? fill 
    : isActive 
      ? "var(--primary)" 
      : "currentColor"
  
  const hasExplicitFill = fill !== undefined
  const hasSizeClass = className && /size-|w-\d|h-\d/.test(className)
  const defaultSize = typeof size === "number" ? size : 24
  
  const sizeClasses = hasSizeClass
    ? { width: defaultSize, height: defaultSize }
    : typeof size === "number"
      ? { width: size, height: size }
      : {}
  
  const sizeClassName = typeof size === "string" ? size : ""

  const processedSvg = React.useMemo(() => {
    if (typeof iconContent !== "string") {
      return null
    }

    const parser = new DOMParser()
    const svgDoc = parser.parseFromString(iconContent, "image/svg+xml")
    const svgElement = svgDoc.querySelector("svg")

    if (!svgElement) {
      return iconContent
    }

    if (fillColor !== undefined) {
      const setFill = (element) => {
        const tagName = element.tagName.toLowerCase()
        const fillableElements = ["path", "circle", "rect", "ellipse", "polygon", "polyline", "line", "text", "tspan"]
        
        if (fillableElements.includes(tagName)) {
          const currentFill = element.getAttribute("fill")
          
          if (hasExplicitFill) {
            if (currentFill !== "none") {
              element.setAttribute("fill", fillColor)
            }
          } else {
            if (currentFill !== null && currentFill !== "none") {
              element.setAttribute("fill", fillColor)
            }
          }
        }
        
        Array.from(element.children).forEach(setFill)
      }
      setFill(svgElement)
    }

    if (stroke !== undefined) {
      const setStroke = (element) => {
        const strokeableElements = ["path", "circle", "rect", "ellipse", "polygon", "polyline", "line", "text", "tspan"]
        if (strokeableElements.includes(element.tagName.toLowerCase())) {
          element.setAttribute("stroke", stroke)
        }
        Array.from(element.children).forEach(setStroke)
      }
      setStroke(svgElement)
    }

    if (strokeWidth !== undefined) {
      const setStrokeWidth = (element) => {
        const strokeableElements = ["path", "circle", "rect", "ellipse", "polygon", "polyline", "line", "text", "tspan"]
        if (strokeableElements.includes(element.tagName.toLowerCase())) {
          element.setAttribute("stroke-width", String(strokeWidth))
        }
        Array.from(element.children).forEach(setStrokeWidth)
      }
      setStrokeWidth(svgElement)
    }

    if (hasSizeClass) {
      const originalWidth = svgElement.getAttribute("width")
      const originalHeight = svgElement.getAttribute("height")
      svgElement.removeAttribute("width")
      svgElement.removeAttribute("height")
      if (!svgElement.getAttribute("viewBox")) {
        if (originalWidth && originalHeight) {
          svgElement.setAttribute("viewBox", `0 0 ${originalWidth} ${originalHeight}`)
        } else {
          svgElement.setAttribute("viewBox", "0 0 24 24")
        }
      }
    } else if (typeof size === "number") {
      svgElement.setAttribute("width", String(size))
      svgElement.setAttribute("height", String(size))
    } else {
      svgElement.removeAttribute("width")
      svgElement.removeAttribute("height")
      if (!svgElement.getAttribute("viewBox")) {
        const originalWidth = svgElement.getAttribute("width") || "24"
        const originalHeight = svgElement.getAttribute("height") || "24"
        svgElement.setAttribute("viewBox", `0 0 ${originalWidth} ${originalHeight}`)
      }
    }

    return svgElement.outerHTML
  }, [iconContent, fillColor, hasExplicitFill, stroke, strokeWidth, size, className])

  if (processedSvg) {
    return (
      <span
        className={cn(
          "inline-flex items-center justify-center shrink-0",
          "text-current",
          sizeClassName && !hasSizeClass ? sizeClassName : "",
          className
        )}
        style={sizeClasses}
        dangerouslySetInnerHTML={{ __html: processedSvg }}
        role="img"
        aria-label={alt || name}
        {...props}
      />
    )
  }

  return (
    <span
      className={cn(
        "inline-block",
        "bg-current",
        sizeClassName,
        className
      )}
      style={{
        ...sizeClasses,
        WebkitMaskImage: `url(${iconContent})`,
        WebkitMaskSize: "contain",
        WebkitMaskRepeat: "no-repeat",
        WebkitMaskPosition: "center",
        maskImage: `url(${iconContent})`,
        maskSize: "contain",
        maskRepeat: "no-repeat",
        maskPosition: "center",
      }}
      role="img"
      aria-label={alt || name}
      {...props}
    />
  )
}

export function getAvailableIcons() {
  return Object.keys(iconRegistry)
}

export function hasIcon(name) {
  return name in iconRegistry
}

export default Icon