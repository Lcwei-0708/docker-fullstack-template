import { useDirection } from "@radix-ui/react-direction";
import { Slot } from "@radix-ui/react-slot";
import * as React from "react";
import * as ReactDOM from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useComposedRefs } from "@/lib/compose-refs";
import { cn } from "@/lib/utils";
import { useAsRef } from "@/hooks/useAsRef";
import { useIsomorphicLayoutEffect } from "@/hooks/useIsomorphicLayoutEffect";

const ROOT_NAME = "ActionBar";
const GROUP_NAME = "ActionBarGroup";
const ITEM_NAME = "ActionBarItem";
const CLOSE_NAME = "ActionBarClose";
const SEPARATOR_NAME = "ActionBarSeparator";
const ITEM_SELECT = "actionbar.itemSelect";
const ENTRY_FOCUS = "actionbarFocusGroup.onEntryFocus";
const EVENT_OPTIONS = { bubbles: false, cancelable: true };

function focusFirst(
  candidates,
  preventScroll = false,
) {
  const PREVIOUSLY_FOCUSED_ELEMENT = document.activeElement;
  for (const candidateRef of candidates) {
    const candidate = candidateRef.current;
    if (!candidate) continue;
    if (candidate === PREVIOUSLY_FOCUSED_ELEMENT) return;
    candidate.focus({ preventScroll });
    if (document.activeElement !== PREVIOUSLY_FOCUSED_ELEMENT) return;
  }
}

function wrapArray(array, startIndex) {
  return array.map((_, index) => array[(startIndex + index) % array.length]);
}

function getDirectionAwareKey(key, dir) {
  if (dir !== "rtl") return key;
  return key === "ArrowLeft"
    ? "ArrowRight"
    : key === "ArrowRight"
      ? "ArrowLeft"
      : key;
}

const ActionBarContext = React.createContext(null);

function useActionBarContext(consumerName) {
  const context = React.useContext(ActionBarContext);
  if (!context) {
    throw new Error(`\`${consumerName}\` must be used within \`${ROOT_NAME}\``);
  }
  return context;
}

const FocusContext = React.createContext(null);

function useFocusContext(consumerName) {
  const context = React.useContext(FocusContext);
  if (!context) {
    throw new Error(`\`${consumerName}\` must be used within \`FocusProvider\``);
  }
  return context;
}

function ActionBar(props) {
  const {
    open = false,
    onOpenChange,
    onEscapeKeyDown,
    side = "bottom",
    alignOffset = 0,
    align = "center",
    sideOffset = 16,
    portalContainer: portalContainerProp,
    dir: dirProp,
    orientation = "horizontal",
    loop = true,
    className,
    style,
    ref,
    asChild,
    ...rootProps
  } = props;

  const [mounted, setMounted] = React.useState(false);

  const rootRef = React.useRef(null);
  const composedRef = useComposedRefs(ref, rootRef);

  const propsRef = useAsRef({
    onEscapeKeyDown,
    onOpenChange,
  });

  const dir = useDirection(dirProp);

  React.useLayoutEffect(() => {
    setMounted(true);
  }, []);

  React.useEffect(() => {
    if (!open) return;

    const ownerDocument = rootRef.current?.ownerDocument ?? document;

    function onKeyDown(event) {
      if (event.key === "Escape") {
        propsRef.current.onEscapeKeyDown?.(event);
        if (!event.defaultPrevented) {
          propsRef.current.onOpenChange?.(false);
        }
      }
    }

    ownerDocument.addEventListener("keydown", onKeyDown);
    return () => ownerDocument.removeEventListener("keydown", onKeyDown);
  }, [open, propsRef]);

  const contextValue = React.useMemo(() => ({
    onOpenChange,
    dir,
    orientation,
    loop,
  }), [onOpenChange, dir, orientation, loop]);

  const portalContainer =
    portalContainerProp ?? (mounted ? globalThis.document?.body : null);

  if (!portalContainer || !open) return null;

  const RootPrimitive = asChild ? Slot : motion.div;

  return (
    <ActionBarContext.Provider value={contextValue}>
      {ReactDOM.createPortal(<RootPrimitive
        role="toolbar"
        aria-orientation={orientation}
        data-slot="action-bar"
        data-side={side}
        data-align={align}
        data-orientation={orientation}
        dir={dir}
        {...rootProps}
        ref={composedRef}
        layout
        initial={{ 
          opacity: 0, 
          scale: 0.95, 
          y: orientation === "horizontal" ? 0 : 16,
        }}
        animate={{ 
          opacity: 1, 
          scale: 1, 
          y: 0,
          transition: {
            type: "spring",
            stiffness: 400,
            damping: 35,
            opacity: { duration: 0.15 },
          }
        }}
        exit={{ 
          opacity: 0, 
          scale: 0.95, 
          y: orientation === "horizontal" ? 0 : 16,
          transition: {
            duration: 0.15,
          }
        }}
        transition={{
          layout: {
            type: "spring",
            stiffness: 500,
            damping: 40,
          }
        }}
        style={{
          [side]: `${sideOffset}px`,
          ...(align === "center" && {
            left: "50%",
            translate: "-50% 0",
          }),
          ...(align === "start" && { left: `${alignOffset}px` }),
          ...(align === "end" && { right: `${alignOffset}px` }),
          ...style,
        }}
        className={cn(
          "fixed z-50 rounded-lg border bg-card/70 shadow-lg backdrop-blur-sm outline-none",
          orientation === "horizontal"
            ? "flex flex-row items-center gap-2 px-2 py-1.5"
            : "flex flex-col items-start gap-2 px-1.5 py-2",
          className
        )} />, portalContainer)}
    </ActionBarContext.Provider>
  );
}

function ActionBarSelection(props) {
  const { className, asChild, ...selectionProps } = props;

  const SelectionPrimitive = asChild ? Slot : motion.div;

  return (
    <SelectionPrimitive
      data-slot="action-bar-selection"
      {...selectionProps}
      layout
      className={cn(
        "bg-input flex items-center gap-1 rounded-sm border px-3 py-1 font-medium text-sm tabular-nums shrink-0",
        className
      )} />
  );
}

function ActionBarGroup(props) {
  const {
    onBlur: onBlurProp,
    onFocus: onFocusProp,
    onMouseDown: onMouseDownProp,
    className,
    asChild,
    ref,
    ...groupProps
  } = props;

  const [tabStopId, setTabStopId] = React.useState(null);
  const [isTabbingBackOut, setIsTabbingBackOut] = React.useState(false);
  const [focusableItemCount, setFocusableItemCount] = React.useState(0);

  const groupRef = React.useRef(null);
  const composedRef = useComposedRefs(ref, groupRef);
  const isClickFocusRef = React.useRef(false);
  const itemsRef = React.useRef(new Map());

  const { dir, orientation } = useActionBarContext(GROUP_NAME);

  const onItemFocus = React.useCallback((tabStopId) => {
    setTabStopId(tabStopId);
  }, []);

  const onItemShiftTab = React.useCallback(() => {
    setIsTabbingBackOut(true);
  }, []);

  const onFocusableItemAdd = React.useCallback(() => {
    setFocusableItemCount((prevCount) => prevCount + 1);
  }, []);

  const onFocusableItemRemove = React.useCallback(() => {
    setFocusableItemCount((prevCount) => prevCount - 1);
  }, []);

  const onItemRegister = React.useCallback((item) => {
    itemsRef.current.set(item.id, item);
  }, []);

  const onItemUnregister = React.useCallback((id) => {
    itemsRef.current.delete(id);
  }, []);

  const getItems = React.useCallback(() => {
    return Array.from(itemsRef.current.values())
      .filter((item) => item.ref.current)
      .sort((a, b) => {
        const elementA = a.ref.current;
        const elementB = b.ref.current;
        if (!elementA || !elementB) return 0;
        const position = elementA.compareDocumentPosition(elementB);
        if (position & Node.DOCUMENT_POSITION_FOLLOWING) {
          return -1;
        }
        if (position & Node.DOCUMENT_POSITION_PRECEDING) {
          return 1;
        }
        return 0;
      });
  }, []);

  const onBlur = React.useCallback((event) => {
    onBlurProp?.(event);
    if (event.defaultPrevented) return;

    setIsTabbingBackOut(false);
  }, [onBlurProp]);

  const onFocus = React.useCallback((event) => {
    onFocusProp?.(event);
    if (event.defaultPrevented) return;

    const isKeyboardFocus = !isClickFocusRef.current;
    if (
      event.target === event.currentTarget &&
      isKeyboardFocus &&
      !isTabbingBackOut
    ) {
      const entryFocusEvent = new CustomEvent(ENTRY_FOCUS, EVENT_OPTIONS);
      event.currentTarget.dispatchEvent(entryFocusEvent);

      if (!entryFocusEvent.defaultPrevented) {
        const items = Array.from(itemsRef.current.values()).filter((item) => !item.disabled);
        const currentItem = items.find((item) => item.id === tabStopId);

        const candidateItems = [currentItem, ...items].filter(Boolean);
        const candidateRefs = candidateItems.map((item) => item.ref);
        focusFirst(candidateRefs, false);
      }
    }
    isClickFocusRef.current = false;
  }, [onFocusProp, isTabbingBackOut, tabStopId]);

  const onMouseDown = React.useCallback((event) => {
    onMouseDownProp?.(event);
    if (event.defaultPrevented) return;

    isClickFocusRef.current = true;
  }, [onMouseDownProp]);

  const focusContextValue = React.useMemo(() => ({
    tabStopId,
    onItemFocus,
    onItemShiftTab,
    onFocusableItemAdd,
    onFocusableItemRemove,
    onItemRegister,
    onItemUnregister,
    getItems,
  }), [
    tabStopId,
    onItemFocus,
    onItemShiftTab,
    onFocusableItemAdd,
    onFocusableItemRemove,
    onItemRegister,
    onItemUnregister,
    getItems,
  ]);

  const GroupPrimitive = asChild ? Slot : motion.div;

  return (
    <FocusContext.Provider value={focusContextValue}>
      <GroupPrimitive
        role="group"
        data-slot="action-bar-group"
        data-orientation={orientation}
        dir={dir}
        tabIndex={isTabbingBackOut || focusableItemCount === 0 ? -1 : 0}
        {...groupProps}
        ref={composedRef}
        layout
        transition={{
          layout: {
            type: "spring",
            stiffness: 500,
            damping: 40,
          }
        }}
        className={cn("flex gap-2 outline-none shrink-0", orientation === "horizontal"
          ? "items-center"
          : "w-full flex-col items-start", className)}
        onBlur={onBlur}
        onFocus={onFocus}
        onMouseDown={onMouseDown} />
    </FocusContext.Provider>
  );
}

function ActionBarItem(props) {
  const {
    onSelect,
    onClick: onClickProp,
    onFocus: onFocusProp,
    onKeyDown: onKeyDownProp,
    onMouseDown: onMouseDownProp,
    className,
    disabled,
    ref,
    ...itemProps
  } = props;

  const itemRef = React.useRef(null);
  const composedRef = useComposedRefs(ref, itemRef);
  const isMouseClickRef = React.useRef(false);

  const { onOpenChange, dir, orientation, loop } =
    useActionBarContext(ITEM_NAME);
  const focusContext = useFocusContext(ITEM_NAME);

  const itemId = React.useId();
  const isTabStop = focusContext.tabStopId === itemId;

  useIsomorphicLayoutEffect(() => {
    focusContext.onItemRegister({
      id: itemId,
      ref: itemRef,
      disabled: !!disabled,
    });

    if (!disabled) {
      focusContext.onFocusableItemAdd();
    }

    return () => {
      focusContext.onItemUnregister(itemId);
      if (!disabled) {
        focusContext.onFocusableItemRemove();
      }
    };
  }, [focusContext, itemId, disabled]);

  const onClick = React.useCallback((event) => {
    onClickProp?.(event);
    if (event.defaultPrevented) return;

    const item = itemRef.current;
    if (!item) return;

    const itemSelectEvent = new CustomEvent(ITEM_SELECT, {
      bubbles: true,
      cancelable: true,
    });

    item.addEventListener(ITEM_SELECT, (event) => onSelect?.(event), {
      once: true,
    });

    item.dispatchEvent(itemSelectEvent);

    if (!itemSelectEvent.defaultPrevented) {
      onOpenChange?.(false);
    }
  }, [onClickProp, onOpenChange, onSelect]);

  const onFocus = React.useCallback((event) => {
    onFocusProp?.(event);
    if (event.defaultPrevented) return;

    focusContext.onItemFocus(itemId);
    isMouseClickRef.current = false;
  }, [onFocusProp, focusContext, itemId]);

  const onKeyDown = React.useCallback((event) => {
    onKeyDownProp?.(event);
    if (event.defaultPrevented) return;

    if (event.key === "Tab" && event.shiftKey) {
      focusContext.onItemShiftTab();
      return;
    }

    if (event.target !== event.currentTarget) return;

    const key = getDirectionAwareKey(event.key, dir);
    let focusIntent;

    if (orientation === "horizontal") {
      if (key === "ArrowLeft") focusIntent = "prev";
      else if (key === "ArrowRight") focusIntent = "next";
      else if (key === "Home") focusIntent = "first";
      else if (key === "End") focusIntent = "last";
    } else {
      if (key === "ArrowUp") focusIntent = "prev";
      else if (key === "ArrowDown") focusIntent = "next";
      else if (key === "Home") focusIntent = "first";
      else if (key === "End") focusIntent = "last";
    }

    if (focusIntent !== undefined) {
      if (event.metaKey || event.ctrlKey || event.altKey || event.shiftKey)
        return;
      event.preventDefault();

      const items = focusContext.getItems().filter((item) => !item.disabled);
      let candidateRefs = items.map((item) => item.ref);

      if (focusIntent === "last") {
        candidateRefs.reverse();
      } else if (focusIntent === "prev" || focusIntent === "next") {
        if (focusIntent === "prev") candidateRefs.reverse();
        const currentIndex = candidateRefs.findIndex((ref) => ref.current === event.currentTarget);
        candidateRefs = loop
          ? wrapArray(candidateRefs, currentIndex + 1)
          : candidateRefs.slice(currentIndex + 1);
      }

      queueMicrotask(() => focusFirst(candidateRefs));
    }
  }, [onKeyDownProp, focusContext, dir, orientation, loop]);

  const onMouseDown = React.useCallback((event) => {
    onMouseDownProp?.(event);
    if (event.defaultPrevented) return;

    isMouseClickRef.current = true;

    if (disabled) {
      event.preventDefault();
    } else {
      focusContext.onItemFocus(itemId);
    }
  }, [onMouseDownProp, focusContext, itemId, disabled]);

  return (
    <Button
      type="button"
      data-slot="action-bar-item"
      variant="ghost"
      size="icon"
      disabled={disabled}
      tabIndex={isTabStop ? 0 : -1}
      {...itemProps}
      className={cn(
        "shrink-0",
        orientation === "vertical" && "w-full",
        className
      )}
      ref={composedRef}
      onClick={onClick}
      onFocus={onFocus}
      onKeyDown={onKeyDown}
      onMouseDown={onMouseDown} />
  );
}

function ActionBarClose(props) {
  const { asChild, className, onClick, ...closeProps } = props;

  const { onOpenChange } = useActionBarContext(CLOSE_NAME);

  const onCloseClick = React.useCallback((event) => {
    onClick?.(event);
    if (event.defaultPrevented) return;

    onOpenChange?.(false);
  }, [onOpenChange, onClick]);

  const ClosePrimitive = asChild ? Slot : Button;

  return (
    <ClosePrimitive
      type="button"
      data-slot="action-bar-close"
      variant="ghost"
      size="icon"
      {...closeProps}
      className={cn(
        "shrink-0 opacity-70 outline-none hover:opacity-100 focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 disabled:pointer-events-none [&_svg:not([class*='size-'])]:size-3.5 [&_svg]:pointer-events-none [&_svg]:shrink-0",
        className
      )}
      onClick={onCloseClick} />
  );
}

function ActionBarSeparator(props) {
  const {
    orientation: orientationProp,
    asChild,
    className,
    ...separatorProps
  } = props;

  const context = useActionBarContext(SEPARATOR_NAME);
  const orientation = orientationProp ?? context.orientation;

  const SeparatorPrimitive = asChild ? Slot : "div";

  return (
    <SeparatorPrimitive
      role="separator"
      aria-orientation={orientation}
      aria-hidden="true"
      data-slot="action-bar-separator"
      {...separatorProps}
      className={cn(
        "in-data-[slot=action-bar-selection]:ml-0.5 in-data-[slot=action-bar-selection]:h-4 in-data-[slot=action-bar-selection]:w-px bg-border",
        orientation === "horizontal" ? "h-6 w-px" : "h-px w-full",
        className
      )} />
  );
}

export { ActionBar, ActionBarSelection, ActionBarGroup, ActionBarItem, ActionBarClose, ActionBarSeparator };
