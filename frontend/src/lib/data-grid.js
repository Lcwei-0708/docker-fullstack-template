import {
  AlignLeft,
  Calendar,
  CheckSquare,
  File,
  Hash,
  Link,
  ListChecks,
  List,
  Type,
} from "lucide-react";

export function flexRender(Comp, props) {
  if (typeof Comp === "string") {
    return Comp;
  }
  return Comp?.(props);
}

export function getIsFileCellData(item) {
  return (
    !!item &&
    typeof item === "object" &&
    "id" in item &&
    "name" in item &&
    "size" in item &&
    "type" in item
  );
}

export function matchSelectOption(value, options) {
  return options.find((o) =>
    o.value === value ||
    o.value.toLowerCase() === value.toLowerCase() ||
    o.label.toLowerCase() === value.toLowerCase())?.value;
}

export function getCellKey(rowIndex, columnId) {
  return `${rowIndex}:${columnId}`;
}

export function parseCellKey(cellKey) {
  const parts = cellKey.split(":");
  const rowIndexStr = parts[0];
  const columnId = parts[1];
  if (rowIndexStr && columnId) {
    const rowIndex = parseInt(rowIndexStr, 10);
    if (!Number.isNaN(rowIndex)) {
      return { rowIndex, columnId };
    }
  }
  return { rowIndex: 0, columnId: "" };
}

export function getRowHeightValue(rowHeight) {
  const rowHeightMap = {
    short: 40,
    medium: 60,
    tall: 80,
    "extra-tall": 100,
  };

  return rowHeightMap[rowHeight];
}

export function getLineCount(rowHeight) {
  const lineCountMap = {
    short: 1,
    medium: 2,
    tall: 3,
    "extra-tall": 4,
  };

  return lineCountMap[rowHeight];
}

export function getCommonPinningStyles(params) {
  const { column, withBorder = false, dir = "ltr" } = params;

  const isPinned = column.getIsPinned();
  const isLastLeftPinnedColumn =
    isPinned === "left" && column.getIsLastColumn("left");
  const isFirstRightPinnedColumn =
    isPinned === "right" && column.getIsFirstColumn("right");

  const isRtl = dir === "rtl";

  const leftPosition =
    isPinned === "left" ? `${column.getStart("left")}px` : undefined;
  const rightPosition =
    isPinned === "right" ? `${column.getAfter("right")}px` : undefined;

  return {
    boxShadow: withBorder
      ? isLastLeftPinnedColumn
        ? isRtl
          ? "4px 0 4px -4px var(--border) inset"
          : "-4px 0 4px -4px var(--border) inset"
        : isFirstRightPinnedColumn
          ? isRtl
            ? "-4px 0 4px -4px var(--border) inset"
            : "4px 0 4px -4px var(--border) inset"
          : undefined
      : undefined,
    left: isRtl ? rightPosition : leftPosition,
    right: isRtl ? leftPosition : rightPosition,
    opacity: isPinned ? 0.97 : 1,
    position: isPinned ? "sticky" : "relative",
    background: isPinned ? "inherit" : undefined,
    width: column.getSize(),
    zIndex: isPinned ? 1 : undefined,
  };
}

export function getScrollDirection(direction) {
  if (
    direction === "left" ||
    direction === "right" ||
    direction === "home" ||
    direction === "end"
  ) {
    return direction;
  }
  if (direction === "pageleft") return "left";
  if (direction === "pageright") return "right";
  return undefined;
}

export function scrollCellIntoView(params) {
  const { container, targetCell, tableRef, direction, viewportOffset, isRtl } =
    params;

  const containerRect = container.getBoundingClientRect();
  const cellRect = targetCell.getBoundingClientRect();

  const hasNegativeScroll = container.scrollLeft < 0;
  const isActuallyRtl = isRtl || hasNegativeScroll;

  const currentTable = tableRef.current;
  const leftPinnedColumns = currentTable?.getLeftVisibleLeafColumns() ?? [];
  const rightPinnedColumns = currentTable?.getRightVisibleLeafColumns() ?? [];

  const leftPinnedWidth = leftPinnedColumns.reduce((sum, c) => sum + c.getSize(), 0);
  const rightPinnedWidth = rightPinnedColumns.reduce((sum, c) => sum + c.getSize(), 0);

  const viewportLeft = isActuallyRtl
    ? containerRect.left + rightPinnedWidth + viewportOffset
    : containerRect.left + leftPinnedWidth + viewportOffset;
  const viewportRight = isActuallyRtl
    ? containerRect.right - leftPinnedWidth - viewportOffset
    : containerRect.right - rightPinnedWidth - viewportOffset;

  const isFullyVisible =
    cellRect.left >= viewportLeft && cellRect.right <= viewportRight;

  if (isFullyVisible) return;

  const isClippedLeft = cellRect.left < viewportLeft;
  const isClippedRight = cellRect.right > viewportRight;

  let scrollDelta = 0;

  if (!direction) {
    if (isClippedRight) {
      scrollDelta = cellRect.right - viewportRight;
    } else if (isClippedLeft) {
      scrollDelta = -(viewportLeft - cellRect.left);
    }
  } else {
    const shouldScrollRight = isActuallyRtl
      ? direction === "right" || direction === "home"
      : direction === "right" || direction === "end";

    if (shouldScrollRight) {
      scrollDelta = cellRect.right - viewportRight;
    } else {
      scrollDelta = -(viewportLeft - cellRect.left);
    }
  }

  container.scrollLeft += scrollDelta;
}

export function getIsInPopover(element) {
  return (element instanceof Element && (element.closest("[data-grid-cell-editor]") ||
    element.closest("[data-grid-popover]")) !== null);
}

export function getColumnVariant(variant) {
  switch (variant) {
    case "short-text":
      return { label: "Short text", icon: AlignLeft };
    case "long-text":
      return { label: "Long text", icon: Type };
    case "number":
      return { label: "Number", icon: Hash };
    case "url":
      return { label: "URL", icon: Link };
    case "checkbox":
      return { label: "Checkbox", icon: CheckSquare };
    case "select":
      return { label: "Select", icon: List };
    case "multi-select":
      return { label: "Multi-select", icon: ListChecks };
    case "date":
      return { label: "Date", icon: Calendar };
    case "file":
      return { label: "File", icon: File };
    default:
      return null;
  }
}
