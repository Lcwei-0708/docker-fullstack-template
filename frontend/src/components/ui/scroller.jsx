import * as React from "react"
import { cn } from "@/lib/utils"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority"
import { useComposedRefs } from "@/lib/compose-refs"
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
} from "lucide-react"

const DATA_TOP_SCROLL = "data-top-scroll";
const DATA_BOTTOM_SCROLL = "data-bottom-scroll";
const DATA_LEFT_SCROLL = "data-left-scroll";
const DATA_RIGHT_SCROLL = "data-right-scroll";
const DATA_TOP_BOTTOM_SCROLL = "data-top-bottom-scroll";
const DATA_LEFT_RIGHT_SCROLL = "data-left-right-scroll";

const scrollerVariants = cva("", {
  variants: {
    orientation: {
      vertical: [
        "overflow-y-auto",
        "data-[top-scroll=true]:[mask-image:linear-gradient(0deg,#000_calc(100%_-_var(--scroll-shadow-size)),transparent)]",
        "data-[bottom-scroll=true]:[mask-image:linear-gradient(180deg,#000_calc(100%_-_var(--scroll-shadow-size)),transparent)]",
        "data-[top-bottom-scroll=true]:[mask-image:linear-gradient(#000,#000,transparent_0,#000_var(--scroll-shadow-size),#000_calc(100%_-_var(--scroll-shadow-size)),transparent)]",
      ],
      horizontal: [
        "overflow-x-auto",
        "data-[left-scroll=true]:[mask-image:linear-gradient(270deg,#000_calc(100%_-_var(--scroll-shadow-size)),transparent)]",
        "data-[right-scroll=true]:[mask-image:linear-gradient(90deg,#000_calc(100%_-_var(--scroll-shadow-size)),transparent)]",
        "data-[left-right-scroll=true]:[mask-image:linear-gradient(to_right,#000,#000,transparent_0,#000_var(--scroll-shadow-size),#000_calc(100%_-_var(--scroll-shadow-size)),transparent)]",
      ],
    },
    hideScrollbar: {
      true: "[-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden",
      // Hide scrollbar by default; show it on hover (for better aesthetics in panels)
      hover: [
        // Reserve scrollbar gutter to avoid layout shift
        "[scrollbar-width:auto]",
        "[scrollbar-gutter:stable]",
        // Firefox: keep width reserved but make it visually transparent until hover
        "[scrollbar-color:transparent_transparent]",
        "hover:[scrollbar-color:hsl(var(--muted-foreground)/0.55)_transparent]",
        "dark:hover:[scrollbar-color:hsl(var(--muted-foreground)/0.35)_transparent]",
        // WebKit: use a more standard width/height than w-2
        "[&::-webkit-scrollbar]:w-3",
        "[&::-webkit-scrollbar]:h-3",
        "[&::-webkit-scrollbar]:bg-transparent",
        "[&::-webkit-scrollbar-thumb]:rounded-full",
        "[&::-webkit-scrollbar-thumb]:bg-transparent",
        "[&::-webkit-scrollbar-thumb]:border-2",
        "[&::-webkit-scrollbar-thumb]:border-transparent",
        "[&::-webkit-scrollbar-thumb]:shadow-none",
        "[&::-webkit-scrollbar-thumb]:bg-clip-padding",
        "hover:[&::-webkit-scrollbar-thumb]:bg-muted-foreground/60",
        "dark:hover:[&::-webkit-scrollbar-thumb]:bg-muted-foreground/40",
        "[&::-webkit-scrollbar-track]:bg-transparent",
        "[&::-webkit-scrollbar-corner]:bg-transparent",
      ].join(" "),
      false: "",
    },
  },
  defaultVariants: {
    orientation: "vertical",
    hideScrollbar: false,
  },
});

function Scroller(props) {
  const {
    orientation = "vertical",
    hideScrollbar,
    className,
    size = 40,
    offset = 0,
    scrollStep = 40,
    style,
    asChild,
    withNavigation: withNavigationProp,
    scrollTriggerMode = "press",
    ref,
    ...scrollerProps
  } = props;

  const withNavigation = !!withNavigationProp;

  const containerRef = React.useRef(null);
  const composedRef = useComposedRefs(ref, containerRef);
  const maxScrollbarWidthRef = React.useRef(0);
  const maxScrollbarHeightRef = React.useRef(0);
  const [scrollVisibility, setScrollVisibility] =
    React.useState({
    up: false,
    down: false,
    left: false,
    right: false,
  });

  const onScrollBy = React.useCallback((direction) => {
      const container = containerRef.current;
      if (!container) return;

      const scrollMap = {
        up: () => (container.scrollTop -= scrollStep),
        down: () => (container.scrollTop += scrollStep),
        left: () => (container.scrollLeft -= scrollStep),
        right: () => (container.scrollLeft += scrollStep),
      };

      scrollMap[direction]();
  }, [scrollStep]);

  const scrollHandlers = React.useMemo(() => ({
      up: () => onScrollBy("up"),
      down: () => onScrollBy("down"),
      left: () => onScrollBy("left"),
      right: () => onScrollBy("right"),
  }), [onScrollBy]);

  React.useLayoutEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let rafId = null;
    const scheduleRecompute = () => {
      if (rafId !== null) window.cancelAnimationFrame(rafId);
      rafId = window.requestAnimationFrame(() => {
        onScroll();
      });
    };

    function onScroll() {
      if (!container) return;

      // Tolerance for fractional scroll metrics (common under browser zoom)
      const EPS = 1;
      const isVertical = orientation === "vertical";

      // Expose scrollbar size to consumers (so they can keep padding aligned)
      // - Windows: scrollbars take layout space -> this will be > 0
      // - macOS overlay scrollbars: this will likely be 0
      const measuredScrollbarWidth = Math.max(0, container.offsetWidth - container.clientWidth);
      const measuredScrollbarHeight = Math.max(0, container.offsetHeight - container.clientHeight);

      // Some browsers change the measured scrollbar size on hover (overlay vs non-overlay),
      // which can cause content jitter if padding depends on it.
      // Use the max observed size to keep layout stable.
      maxScrollbarWidthRef.current = Math.max(maxScrollbarWidthRef.current, measuredScrollbarWidth);
      maxScrollbarHeightRef.current = Math.max(maxScrollbarHeightRef.current, measuredScrollbarHeight);

      container.style.setProperty("--scroller-scrollbar-width", `${maxScrollbarWidthRef.current}px`);
      container.style.setProperty("--scroller-scrollbar-height", `${maxScrollbarHeightRef.current}px`);

      if (isVertical) {
        const scrollTop = container.scrollTop;
        const clientHeight = container.clientHeight;
        const scrollHeight = container.scrollHeight;
        const bottom = scrollTop + clientHeight;

        if (withNavigation) {
          setScrollVisibility((prev) => {
            const newUp = scrollTop > offset + EPS;
            const newDown = bottom < scrollHeight - EPS;

            if (prev.up !== newUp || prev.down !== newDown) {
              return {
                ...prev,
                up: newUp,
                down: newDown,
              };
            }
            return prev;
          });
        }

        const isVerticallyScrollable = scrollHeight - clientHeight > EPS;
        const hasTopScroll = scrollTop > offset + EPS;
        const hasBottomScroll = bottom + offset < scrollHeight - EPS;

        if (hasTopScroll && hasBottomScroll && isVerticallyScrollable) {
          container.setAttribute(DATA_TOP_BOTTOM_SCROLL, "true");
          container.removeAttribute(DATA_TOP_SCROLL);
          container.removeAttribute(DATA_BOTTOM_SCROLL);
        } else {
          container.removeAttribute(DATA_TOP_BOTTOM_SCROLL);
          if (hasTopScroll) container.setAttribute(DATA_TOP_SCROLL, "true");
          else container.removeAttribute(DATA_TOP_SCROLL);
          if (hasBottomScroll && isVerticallyScrollable) container.setAttribute(DATA_BOTTOM_SCROLL, "true");
          else container.removeAttribute(DATA_BOTTOM_SCROLL);
        }
      }

      const scrollLeft = container.scrollLeft;
      const clientWidth = container.clientWidth;
      const scrollWidth = container.scrollWidth;
      const right = scrollLeft + clientWidth;

      if (withNavigation) {
        setScrollVisibility((prev) => {
          const newLeft = scrollLeft > offset + EPS;
          const newRight = right < scrollWidth - EPS;

          if (prev.left !== newLeft || prev.right !== newRight) {
            return {
              ...prev,
              left: newLeft,
              right: newRight,
            };
          }
          return prev;
        });
      }

      const isHorizontallyScrollable = scrollWidth - clientWidth > EPS;
      const hasLeftScroll = scrollLeft > offset + EPS;
      const hasRightScroll = right + offset < scrollWidth - EPS;

      if (hasLeftScroll && hasRightScroll && isHorizontallyScrollable) {
        container.setAttribute(DATA_LEFT_RIGHT_SCROLL, "true");
        container.removeAttribute(DATA_LEFT_SCROLL);
        container.removeAttribute(DATA_RIGHT_SCROLL);
      } else {
        container.removeAttribute(DATA_LEFT_RIGHT_SCROLL);
        if (hasLeftScroll) container.setAttribute(DATA_LEFT_SCROLL, "true");
        else container.removeAttribute(DATA_LEFT_SCROLL);
        if (hasRightScroll && isHorizontallyScrollable) container.setAttribute(DATA_RIGHT_SCROLL, "true");
        else container.removeAttribute(DATA_RIGHT_SCROLL);
      }
    }

    // Initial compute (and re-compute after layout settles)
    scheduleRecompute();
    scheduleRecompute();

    container.addEventListener("scroll", scheduleRecompute);
    window.addEventListener("resize", scheduleRecompute);
    document.addEventListener("visibilitychange", scheduleRecompute);

    // Observe size/content changes so the mask updates even before first scroll.
    let resizeObserver = null;
    if (typeof ResizeObserver !== "undefined") {
      resizeObserver = new ResizeObserver(() => {
        scheduleRecompute();
      });
      resizeObserver.observe(container);
    }

    return () => {
      if (rafId !== null) window.cancelAnimationFrame(rafId);
      container.removeEventListener("scroll", scheduleRecompute);
      window.removeEventListener("resize", scheduleRecompute);
      document.removeEventListener("visibilitychange", scheduleRecompute);
      resizeObserver?.disconnect?.();
    };
  }, [orientation, offset, withNavigation]);

  const composedStyle = React.useMemo(() => ({
      "--scroll-shadow-size": `${size}px`,
      ...style,
  }), [size, style]);

  const activeDirections = React.useMemo(() => {
    if (!withNavigation) return [];
    return orientation === "vertical" ? ["up", "down"] : ["left", "right"];
  }, [orientation, withNavigation]);

  const ScrollerPrimitive = asChild ? Slot : "div";

  const ScrollerImpl = (
    <ScrollerPrimitive
      data-slot="scroller"
      {...scrollerProps}
      ref={composedRef}
      style={composedStyle}
      className={cn(scrollerVariants({ orientation, hideScrollbar, className }))} />
  );

  const navigationButtons = React.useMemo(() => {
    if (!withNavigation) return null;

    return activeDirections
      .filter((direction) => scrollVisibility[direction])
      .map((direction) => (
        <ScrollButton
          key={direction}
          data-slot="scroll-button"
          direction={direction}
          onClick={scrollHandlers[direction]}
          triggerMode={scrollTriggerMode} />
      ));
  }, [
    activeDirections,
    scrollVisibility,
    scrollHandlers,
    scrollTriggerMode,
    withNavigation,
  ]);

  if (withNavigation) {
    return (
      <div className="relative w-full">
        {navigationButtons}
        {ScrollerImpl}
      </div>
    );
  }

  return ScrollerImpl;
}

const scrollButtonVariants = cva(
  "absolute z-10 transition-opacity [&>svg]:size-4 [&>svg]:opacity-80 hover:[&>svg]:opacity-100",
  {
  variants: {
    direction: {
      up: "top-2 left-1/2 -translate-x-1/2",
      down: "bottom-2 left-1/2 -translate-x-1/2",
      left: "top-1/2 left-2 -translate-y-1/2",
      right: "top-1/2 right-2 -translate-y-1/2",
    },
  },
  defaultVariants: {
    direction: "up",
  },
  }
);

const directionToIcon = {
  up: ChevronUp,
  down: ChevronDown,
  left: ChevronLeft,
  right: ChevronRight
};

function ScrollButton(props) {
  const {
    direction,
    className,
    triggerMode = "press",
    onClick,
    ref,
    ...buttonProps
  } = props;

  const [autoScrollTimer, setAutoScrollTimer] = React.useState(null);

  const onAutoScrollStart = React.useCallback((event) => {
      if (autoScrollTimer !== null) return;

      if (triggerMode === "press") {
        const timer = window.setInterval(onClick ?? (() => {}), 50);
        setAutoScrollTimer(timer);
      } else if (triggerMode === "hover") {
        const timer = window.setInterval(() => {
          if (event) onClick?.(event);
        }, 50);
        setAutoScrollTimer(timer);
      }
  }, [autoScrollTimer, onClick, triggerMode]);

  const onAutoScrollStop = React.useCallback(() => {
    if (autoScrollTimer === null) return;

    window.clearInterval(autoScrollTimer);
    setAutoScrollTimer(null);
  }, [autoScrollTimer]);

  const eventHandlers = React.useMemo(() => {
    const triggerModeHandlers = {
      press: {
        onPointerDown: onAutoScrollStart,
        onPointerUp: onAutoScrollStop,
        onPointerLeave: onAutoScrollStop,
        onClick: () => {},
      },

      hover: {
        onPointerEnter: onAutoScrollStart,
        onPointerLeave: onAutoScrollStop,
        onClick: () => {},
      },

      click: {
        onClick,
      }
    };

    return triggerModeHandlers[triggerMode] ?? {};
  }, [triggerMode, onAutoScrollStart, onAutoScrollStop, onClick]);

  React.useEffect(() => {
    return () => onAutoScrollStop();
  }, [onAutoScrollStop]);

  const Icon = directionToIcon[direction];

  return (
    <button
      type="button"
      {...buttonProps}
      {...eventHandlers}
      ref={ref}
      className={cn(scrollButtonVariants({ direction, className }))}>
      <Icon />
    </button>
  );
}

export { Scroller };
