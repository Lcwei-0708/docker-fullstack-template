import * as React from 'react';
import { Fragment } from 'react';
import { useTranslation } from 'react-i18next';
import { Checkbox } from '@/components/ui/checkbox';
import { Skeleton } from '@/components/ui/skeleton';
import { useDataGrid } from '@/components/data-grid/data-grid';
import { flexRender } from '@tanstack/react-table';
import { cva } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const headerCellSpacingVariants = cva('', {
  variants: {
    size: {
      dense: 'px-2.5 h-9',
      default: 'px-0 h-11',
    },
  },
  defaultVariants: {
    size: 'default',
  },
});

const bodyCellSpacingVariants = cva('', {
  variants: {
    size: {
      dense: 'px-2.5 py-2',
      default: 'px-4 py-3',
    },
  },
  defaultVariants: {
    size: 'default',
  },
});

function getPinningStyles(column) {
  const isPinned = column.getIsPinned();

  return {
    left: isPinned === 'left' ? `${column.getStart('left')}px` : undefined,
    right: isPinned === 'right' ? `${column.getAfter('right')}px` : undefined,
    position: isPinned ? 'sticky' : 'relative',
    width: column.getSize(),
    zIndex: isPinned ? 1 : 0,
  };
}

// Base table element wrapper
const DataGridTableBase = React.forwardRef(function DataGridTableBase({
  children
}, ref) {
  const { props, table } = useDataGrid();
  const isResizing = table.getState().columnSizingInfo.isResizingColumn;

  return (
    <table
      ref={ref}
      data-slot="data-grid-table"
      className={cn(
        'w-full align-middle caption-bottom text-left rtl:text-right text-foreground font-normal text-sm',
        !props.tableLayout?.columnsDraggable && 'border-separate border-spacing-0',
        props.tableLayout?.width === 'fixed' ? 'table-fixed' : 'table-auto',
        isResizing && '[&_*]:!transition-none [&_*]:!transform-none',
        props.tableClassNames?.base
      )}
      style={{
        ...(isResizing && {
          contain: 'layout style',
        }),
      }}>
      {children}
    </table>
  );
});

// Table head element
function DataGridTableHead({
  children
}) {
  const { props } = useDataGrid();

  return (
    <thead
      className={cn(
        props.tableClassNames?.header,
        props.tableLayout?.headerSticky && props.tableClassNames?.headerSticky
      )}>
      {children}
    </thead>
  );
}

// Table header row
function DataGridTableHeadRow(
  {
    children,
    headerGroup
  }
) {
  const { props } = useDataGrid();

  return (
    <tr
      key={headerGroup.id}
      className={cn(
        'bg-muted/30',
        props.tableLayout?.headerBorder && '[&>th]:border-b',
        props.tableLayout?.cellBorder && 
          !props.tableLayout?.columnsResizable && 
          '[&_>:last-child]:border-e-0',
        props.tableLayout?.stripped && 'bg-transparent',
        props.tableLayout?.headerBackground === false && 'bg-transparent',
        props.tableClassNames?.headerRow
      )}>
      {children}
    </tr>
  );
}

// Table header cell with border and pinning logic
const DataGridTableHeadRowCell = React.memo(
  function DataGridTableHeadRowCell(
    {
      children,
      header,
      dndRef,
      dndStyle
    }
  ) {
    const { props, hasVerticalScrollbar = false } = useDataGrid();

    const { column } = header;
    const isPinned = column.getIsPinned();
    const isLastLeftPinned = isPinned === 'left' && column.getIsLastColumn('left');
    const isFirstRightPinned = isPinned === 'right' && column.getIsFirstColumn('right');
    const isResizing = column.getIsResizing();
    const columnSize = column.getSize();
    const headerCellSpacing = headerCellSpacingVariants({
      size: props.tableLayout?.dense ? 'dense' : 'default',
    });

    // Determine border visibility based on scrollbar and column position
    const isLastColumn = header.headerGroup.headers[header.headerGroup.headers.length - 1].id === header.id;
    let shouldHideRightBorder = false;
    const currentIndex = header.headerGroup.headers.findIndex(h => h.id === header.id);
    const nextHeader = header.headerGroup.headers[currentIndex + 1];
    const isSelectColumn = column.id === 'select';
    const isCurrentPinned = isPinned !== false || isSelectColumn;
    
    if (isLastColumn) {
      shouldHideRightBorder = !hasVerticalScrollbar;
    } else if (!isCurrentPinned && nextHeader) {
      const isNextColumnPinned = nextHeader.column.getIsPinned() !== false || nextHeader.column.id === 'select';
      shouldHideRightBorder = isNextColumnPinned;
    }

    return (
      <th
        key={header.id}
        ref={dndRef}
        style={{
          ...(props.tableLayout?.width === 'fixed' && {
            width: `${columnSize}px`,
            minWidth: `${columnSize}px`,
            maxWidth: `${columnSize}px`,
          }),
          ...(props.tableLayout?.columnsPinnable && column.getCanPin() && getPinningStyles(column)),
          ...(dndStyle ? dndStyle : null),
          ...(isResizing && {
            willChange: 'width',
            contain: 'layout style',
          }),
        }}
        data-pinned={isPinned || undefined}
        data-last-col={isLastLeftPinned ? 'left' : isFirstRightPinned ? 'right' : undefined}
        data-resizing={isResizing || undefined}
        className={cn(
          'relative h-10 text-left rtl:text-right align-middle font-normal text-foreground [&:has([role=checkbox])]:pe-0',
          headerCellSpacing,
          column.id === 'select' && '!px-4',
          !shouldHideRightBorder && 'border-e',
          props.tableLayout?.columnsResizable && column.getCanResize() && !shouldHideRightBorder && !(hasVerticalScrollbar && isLastColumn) && '!border-e',
          props.tableLayout?.columnsResizable && column.getCanResize() && 'truncate',
          props.tableLayout?.columnsPinnable &&
            column.getCanPin() &&
            '[&:not([data-pinned]):has(+[data-pinned])_div.cursor-col-resize:last-child]:opacity-0 [&[data-last-col=left]_div.cursor-col-resize:last-child]:opacity-0 [&[data-pinned=left][data-last-col=left]]:border-e! [&[data-pinned=right]:last-child_div.cursor-col-resize:last-child]:opacity-0 [&[data-pinned=right][data-last-col=right]]:border-s! [&[data-pinned][data-last-col]]:border-border [&[data-pinned]]:bg-sidebar-muted/90 [&[data-pinned]]:backdrop-blur-sm',
          isResizing && 'select-none [&_*]:pointer-events-none',
          header.column.columnDef.meta?.headerClassName,
          column.getIndex() === 0 || column.getIndex() === header.headerGroup.headers.length - 1
            ? props.tableClassNames?.edgeCell
            : ''
        )}
        data-column-id={column.id}>
        {children}
      </th>
    );
  },
  (prev, next) => {
    const prevColumn = prev.header.column;
    const nextColumn = next.header.column;
    const prevIsResizing = prevColumn.getIsResizing();
    const nextIsResizing = nextColumn.getIsResizing();
    
    if (prevIsResizing || nextIsResizing) {
      const resizingColumnId = prevIsResizing 
        ? prevColumn.id 
        : nextIsResizing 
          ? nextColumn.id 
          : null;
      
      if (resizingColumnId && prevColumn.id !== resizingColumnId && nextColumn.id !== resizingColumnId) {
        return true;
      }
    }
    
    return (
      prevColumn.getSize() === nextColumn.getSize() &&
      prevIsResizing === nextIsResizing &&
      prevColumn.getIsPinned() === nextColumn.getIsPinned() &&
      prev.children === next.children &&
      prev.dndStyle === next.dndStyle
    );
  }
);

// Column resize handle component
const DataGridTableHeadRowCellResize = React.memo(
  function DataGridTableHeadRowCellResize(
    {
      header
    }
  ) {
    const { column } = header;
    const isResizing = column.getIsResizing();
    const isPinned = column.getIsPinned();
    const isLastLeftPinned = isPinned === 'left' && column.getIsLastColumn('left');
    const isFirstRightPinned = isPinned === 'right' && column.getIsFirstColumn('right');

    const handleDoubleClick = React.useCallback(() => {
      column.resetSize();
    }, [column]);

    // Align resize line with pin border when column is pinned at edge
    const isPinnedEdge = isLastLeftPinned || isFirstRightPinned;
    const resizeLinePosition = isPinnedEdge ? 'before:right-0' : 'before:left-1/2 before:-translate-x-1/2';

    return (
      <div
        onDoubleClick={handleDoubleClick}
        onMouseDown={header.getResizeHandler()}
        onTouchStart={header.getResizeHandler()}
        className={cn(
          'absolute top-0 h-full w-4 cursor-ew-resize select-none touch-none -end-2 z-10 flex justify-center before:absolute before:w-[2px] before:inset-y-0 before:opacity-0',
          resizeLinePosition,
          isResizing && 'will-change-[width]'
        )}
        style={{
          willChange: isResizing ? 'width' : 'auto',
        }}
      />
    );
  },
  (prev, next) => {
    return (
      prev.header.column.getIsResizing() === next.header.column.getIsResizing() &&
      prev.header.column.getSize() === next.header.column.getSize()
    );
  }
);

// Spacer row between header and body
function DataGridTableRowSpacer() {
  return <tbody aria-hidden="true" className="h-2"></tbody>;
}

// Table body element
function DataGridTableBody({
  children
}) {
  const { props } = useDataGrid();

  return (
    <tbody
      className={cn(
        '[&_tr:last-child]:border-0',
        props.tableLayout?.rowRounded && '[&_td:first-child]:rounded-s-lg [&_td:last-child]:rounded-e-lg',
        props.tableClassNames?.body
      )}>
      {children}
    </tbody>
  );
}

// Skeleton row for loading state
function DataGridTableBodyRowSkeleton({
  children
}) {
  const { table, props } = useDataGrid();

  return (
    <tr
      className={cn(
        'bg-sidebar hover:bg-accent/40 data-[state=selected]:bg-accent/50',
        props.onRowClick && 'cursor-pointer',
        !props.tableLayout?.stripped &&
          props.tableLayout?.rowBorder &&
          'border-b border-border [&:not(:last-child)>td]:border-b',
        props.tableLayout?.cellBorder && '[&_>:last-child]:border-e-0',
        props.tableLayout?.stripped && 'odd:bg-card hover:bg-transparent odd:hover:bg-accent',
        table.options.enableRowSelection && '[&_>:first-child]:relative',
        props.tableClassNames?.bodyRow
      )}>
      {children}
    </tr>
  );
}

// Skeleton cell for loading state
function DataGridTableBodyRowSkeletonCell(
  {
    children,
    column
  }
) {
  const { props, table } = useDataGrid();
  const bodyCellSpacing = bodyCellSpacingVariants({
    size: props.tableLayout?.dense ? 'dense' : 'default',
  });

  const skeletonContent = children || <Skeleton className="h-5 w-full !rounded-2xs" />;

  return (
    <td
      className={cn(
        'align-middle',
        bodyCellSpacing,
        props.tableLayout?.cellBorder && 'border-e',
        props.tableLayout?.columnsResizable && column.getCanResize() && 'truncate',
        column.columnDef.meta?.cellClassName,
        props.tableLayout?.columnsPinnable &&
          column.getCanPin() &&
          '[&[data-pinned=left][data-last-col=left]]:border-e! [&[data-pinned=right][data-last-col=right]]:border-s! [&[data-pinned][data-last-col]]:border-border data-pinned:bg-popover data-pinned:backdrop-blur-xs',
        column.getIndex() === 0 || column.getIndex() === table.getVisibleFlatColumns().length - 1
          ? props.tableClassNames?.edgeCell
          : ''
      )}>
      <div className="h-full flex items-center">
        {skeletonContent}
      </div>
    </td>
  );
}

// Table body row
function DataGridTableBodyRow(
  {
    children,
    row,
    dndRef,
    dndStyle
  }
) {
  const { props, table } = useDataGrid();

  // Handle row click for row selection and row click event
  const handleRowClick = React.useCallback((event) => {
    const target = event.target;
    const isCheckboxClick = target.closest('button[role="checkbox"]') || 
                           target.closest('[role="checkbox"]') ||
                           target.closest('input[type="checkbox"]');
    
    if (isCheckboxClick) {
      return;
    }

    if (table.options.enableRowSelection) {
      row.toggleSelected();
    }

    if (props.onRowClick) {
      props.onRowClick(row.original);
    }
  }, [table.options.enableRowSelection, row, props.onRowClick]);

  return (
    <tr
      ref={dndRef}
      style={{ ...(dndStyle ? dndStyle : null) }}
      data-state={table.options.enableRowSelection && row.getIsSelected() ? 'selected' : undefined}
      onClick={handleRowClick}
      className={cn(
        'bg-popover hover:bg-accent/10 data-[state=selected]:bg-accent/50',
        (props.onRowClick || table.options.enableRowSelection) && 'cursor-pointer',
        !props.tableLayout?.stripped &&
          props.tableLayout?.rowBorder &&
          'border-b border-border [&:not(:last-child)>td]:border-b',
        props.tableLayout?.cellBorder && '[&_>:last-child]:border-e-0',
        props.tableLayout?.stripped && 'odd:bg-popover hover:bg-transparent odd:hover:bg-accent',
        table.options.enableRowSelection && '[&_>:first-child]:relative',
        props.tableClassNames?.bodyRow
      )}>
      {children}
    </tr>
  );
}

// Expanded row content
function DataGridTableBodyRowExpandded(
  {
    row
  }
) {
  const { props, table } = useDataGrid();

  return (
    <tr
      className={cn(props.tableLayout?.rowBorder && '[&:not(:last-child)>td]:border-b')}>
      <td colSpan={row.getVisibleCells().length}>
        {table
          .getAllColumns()
          .find((column) => column.columnDef.meta?.expandedContent)
          ?.columnDef.meta?.expandedContent?.(row.original)}
      </td>
    </tr>
  );
}

// Table body cell with border and pinning logic
const DataGridTableBodyRowCell = React.memo(
  function DataGridTableBodyRowCell(
    {
      children,
      cell,
      dndRef,
      dndStyle
    }
  ) {
    const { props, table, hasVerticalScrollbar = false } = useDataGrid();

    const { column, row } = cell;
    const isPinned = column.getIsPinned();
    const isLastLeftPinned = isPinned === 'left' && column.getIsLastColumn('left');
    const isFirstRightPinned = isPinned === 'right' && column.getIsFirstColumn('right');
    const isResizing = column.getIsResizing();
    const isRowSelected = table.options.enableRowSelection && row.getIsSelected();
    const bodyCellSpacing = bodyCellSpacingVariants({
      size: props.tableLayout?.dense ? 'dense' : 'default',
    });

    // Determine border visibility based on scrollbar and column position
    const visibleCells = row.getVisibleCells();
    const isLastColumn = visibleCells[visibleCells.length - 1].id === cell.id;
    let shouldHideRightBorder = false;
    const currentIndex = visibleCells.findIndex(c => c.id === cell.id);
    const nextCell = visibleCells[currentIndex + 1];
    const isSelectColumn = column.id === 'select';
    const isCurrentPinned = isPinned !== false || isSelectColumn;
    
    if (hasVerticalScrollbar && isLastColumn) {
      shouldHideRightBorder = false;
    } else if (!isCurrentPinned && nextCell) {
      const isNextColumnPinned = nextCell.column.getIsPinned() !== false || nextCell.column.id === 'select';
      shouldHideRightBorder = isNextColumnPinned;
    }

    return (
      <td
        key={cell.id}
        ref={dndRef}
        {...(props.tableLayout?.columnsDraggable && !isPinned ? { cell } : {})}
        style={{
          ...(props.tableLayout?.columnsPinnable && column.getCanPin() && getPinningStyles(column)),
          ...(dndStyle ? dndStyle : null),
          ...(isResizing && {
            willChange: 'width',
            contain: 'layout style',
          }),
        }}
        data-pinned={isPinned || undefined}
        data-last-col={isLastLeftPinned ? 'left' : isFirstRightPinned ? 'right' : undefined}
        data-resizing={isResizing || undefined}
        data-column-id={column.id}
        className={cn(
          'align-middle',
          bodyCellSpacing,
          (hasVerticalScrollbar && isLastColumn) ? '!border-e' : (props.tableLayout?.cellBorder && !shouldHideRightBorder && 'border-e'),
          props.tableLayout?.columnsResizable && column.getCanResize() && 'truncate',
          isResizing && 'select-none [&_*]:pointer-events-none',
          cell.column.columnDef.meta?.cellClassName,
          props.tableLayout?.columnsPinnable &&
            column.getCanPin() &&
            '[&[data-pinned=left][data-last-col=left]]:border-e! [&[data-pinned=right][data-last-col=right]]:border-s! [&[data-pinned][data-last-col]]:border-border',
          props.tableLayout?.columnsPinnable &&
            column.getCanPin() &&
            !isRowSelected &&
            'data-pinned:popover/85 data-pinned:backdrop-blur-sm',
          props.tableLayout?.columnsPinnable &&
            column.getCanPin() &&
            isRowSelected &&
            'data-pinned:bg-accent/50 data-pinned:backdrop-blur-sm',
          column.getIndex() === 0 || column.getIndex() === row.getVisibleCells().length - 1
            ? props.tableClassNames?.edgeCell
            : ''
        )}>
        {children}
      </td>
    );
  },
  (prev, next) => {
    const prevColumn = prev.cell.column;
    const nextColumn = next.cell.column;
    const prevIsResizing = prevColumn.getIsResizing();
    const nextIsResizing = nextColumn.getIsResizing();
    
    if (prevIsResizing || nextIsResizing) {
      const resizingColumnId = prevIsResizing 
        ? prevColumn.id 
        : nextIsResizing 
          ? nextColumn.id 
          : null;
      
      if (resizingColumnId && prevColumn.id !== resizingColumnId && nextColumn.id !== resizingColumnId) {
        return true;
      }
    }
    
    return (
      prevColumn.getSize() === nextColumn.getSize() &&
      prevIsResizing === nextIsResizing &&
      prevColumn.getIsPinned() === nextColumn.getIsPinned() &&
      prev.cell.id === next.cell.id &&
      prev.children === next.children &&
      prev.dndStyle === next.dndStyle
    );
  }
);

// Empty state message when no data
function DataGridTableEmpty() {
  const { t } = useTranslation();
  const { table, props } = useDataGrid();
  const totalColumns = table.getAllColumns().length;

  return (
    <tr>
      <td colSpan={totalColumns} className="text-center text-muted-foreground py-40">
        {props.emptyMessage || t('components.dataGrid.table.noData', 'No data available')}
      </td>
    </tr>
  );
}

// Loading spinner overlay
function DataGridTableLoader() {
  const { t } = useTranslation();
  const { props } = useDataGrid();

  return (
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
      <div
        className="text-muted-foreground bg-card flex items-center gap-2 px-4 py-2 font-medium leading-none text-sm border shadow-xs rounded-md">
        <svg
          className="animate-spin -ml-1 h-5 w-5 text-muted-foreground"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="3"></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        {props.loadingMessage || t('components.dataGrid.table.loading', 'Loading...')}
      </div>
    </div>
  );
}

// Row selection checkbox
function DataGridTableRowSelect(
  {
    row,
    size,
    className
  }
) {
  return (
    <>
      <div
        className={cn(
          'hidden absolute top-0 bottom-0 start-0 w-[2px] bg-primary/70',
          row.getIsSelected() && 'block'
        )}></div>
      <div className={cn('flex items-center justify-center', className)}>
        <Checkbox
          checked={row.getIsSelected()}
          onCheckedChange={(value) => row.toggleSelected(!!value)}
          aria-label="Select row"
          size={size ?? 'sm'}
          className="align-[inherit]" />
      </div>
    </>
  );
}

// Select all checkbox in header
function DataGridTableRowSelectAll({
  size,
  className
}) {
  const { table, recordCount, isLoading } = useDataGrid();
  const checkboxRef = React.useRef(null);

  const isAllSelected = table.getIsAllPageRowsSelected();
  const isSomeSelected = table.getIsSomePageRowsSelected();
  
  // Set indeterminate state for checkbox
  React.useEffect(() => {
    if (checkboxRef.current) {
      const isIndeterminate = isSomeSelected && !isAllSelected;
      checkboxRef.current.indeterminate = isIndeterminate;
    }
  }, [isAllSelected, isSomeSelected]);

  const checked = isAllSelected;

  const handleCheckedChange = React.useCallback((value) => {
    const shouldSelect = !!value;
    table.toggleAllPageRowsSelected(shouldSelect);
  }, [table]);

  return (
    <div className={cn('flex items-center justify-center', className)}>
      <Checkbox
        ref={checkboxRef}
        checked={checked}
        disabled={isLoading || recordCount === 0}
        onCheckedChange={handleCheckedChange}
        aria-label="Select all"
        size={size}
        className="align-[inherit]" />
    </div>
  );
}

// Main table component
const DataGridTable = React.memo(function DataGridTable() {
  const { t } = useTranslation();
  const { table, isLoading, props, setHasVerticalScrollbar } = useDataGrid();
  const pagination = table.getState().pagination;
  const headerGroups = table.getHeaderGroups();
  const rows = table.getRowModel().rows;
  const isResizing = table.getState().columnSizingInfo.isResizingColumn;
  const tableRef = React.useRef(null);

  // Detect vertical scrollbar in parent container
  React.useEffect(() => {
    if (!setHasVerticalScrollbar) return;

    const checkScrollbar = () => {
      if (!tableRef.current) {
        setHasVerticalScrollbar(false);
        return;
      }

      let scrollableParent = null;
      let parent = tableRef.current.parentElement;
      
      while (parent && parent !== document.body) {
        const style = window.getComputedStyle(parent);
        const hasOverflow = style.overflowY === 'auto' ||
                           style.overflowY === 'scroll' ||
                           style.overflow === 'auto' ||
                           style.overflow === 'scroll';
        
        if (hasOverflow) {
          scrollableParent = parent;
          break;
        }
        parent = parent.parentElement;
      }

      if (scrollableParent) {
        const hasScrollbar = scrollableParent.scrollHeight > scrollableParent.clientHeight + 1;
        setHasVerticalScrollbar(hasScrollbar);
      } else {
        setHasVerticalScrollbar(false);
      }
    };

    const timeoutId = setTimeout(() => {
      checkScrollbar();
    }, 0);

    const resizeObserver = new ResizeObserver(() => {
      setTimeout(() => {
        checkScrollbar();
      }, 0);
    });

    let scrollableParent = null;
    if (tableRef.current) {
      let parent = tableRef.current.parentElement;
      while (parent && parent !== document.body) {
        const style = window.getComputedStyle(parent);
        const hasOverflow = style.overflowY === 'auto' ||
                           style.overflowY === 'scroll' ||
                           style.overflow === 'auto' ||
                           style.overflow === 'scroll';
        
        if (hasOverflow) {
          scrollableParent = parent;
          resizeObserver.observe(parent);
          parent.addEventListener('scroll', checkScrollbar);
          break;
        }
        parent = parent.parentElement;
      }
    }

    window.addEventListener('resize', checkScrollbar);

    return () => {
      clearTimeout(timeoutId);
      resizeObserver.disconnect();
      window.removeEventListener('resize', checkScrollbar);
      if (scrollableParent) {
        scrollableParent.removeEventListener('scroll', checkScrollbar);
      }
    };
  }, [setHasVerticalScrollbar, rows.length, isLoading]);

  // Update cursor style during column resizing
  React.useEffect(() => {
    if (isResizing) {
      document.body.style.cursor = 'ew-resize';
      // Prevent text selection during resize
      document.body.style.userSelect = 'none';
    } else {
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    }

    return () => {
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  return (
    <DataGridTableBase ref={tableRef}>
      <DataGridTableHead>
        {headerGroups.map((headerGroup, index) => {
          return (
            <DataGridTableHeadRow headerGroup={headerGroup} key={headerGroup.id || index}>
              {headerGroup.headers.map((header) => {
                const { column } = header;

                return (
                  <DataGridTableHeadRowCell header={header} key={header.id}>
                    {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                    {props.tableLayout?.columnsResizable && column.getCanResize() && (
                      <DataGridTableHeadRowCellResize header={header} />
                    )}
                  </DataGridTableHeadRowCell>
                );
              })}
            </DataGridTableHeadRow>
          );
        })}
      </DataGridTableHead>
      {(props.tableLayout?.stripped || !props.tableLayout?.rowBorder) && <DataGridTableRowSpacer />}
      <DataGridTableBody>
        {isLoading && props.loadingMode === 'skeleton' && pagination?.pageSize ? (
          Array.from({ length: pagination.pageSize }).map((_, rowIndex) => (
            <DataGridTableBodyRowSkeleton key={rowIndex}>
              {table.getVisibleFlatColumns().map((column, colIndex) => {
                return (
                  <DataGridTableBodyRowSkeletonCell column={column} key={colIndex}>
                    {column.columnDef.meta?.skeleton}
                  </DataGridTableBodyRowSkeletonCell>
                );
              })}
            </DataGridTableBodyRowSkeleton>
          ))
        ) : isLoading && props.loadingMode === 'spinner' ? (
          <tr>
            <td colSpan={table.getVisibleFlatColumns().length} className="p-8">
              <div className="flex items-center justify-center">
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-muted-foreground"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                {props.loadingMessage || t('components.dataGrid.table.loading', 'Loading...')}
              </div>
            </td>
          </tr>
        ) : rows.length ? (
          rows.map((row) => {
            return (
              <Fragment key={row.id}>
                <DataGridTableBodyRow row={row}>
                  {row.getVisibleCells().map((cell) => {
                    return (
                      <DataGridTableBodyRowCell cell={cell} key={cell.id}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </DataGridTableBodyRowCell>
                    );
                  })}
                </DataGridTableBodyRow>
                {row.getIsExpanded() && <DataGridTableBodyRowExpandded row={row} />}
              </Fragment>
            );
          })
        ) : (
          <DataGridTableEmpty />
        )}
      </DataGridTableBody>
    </DataGridTableBase>
  );
});

export {
  DataGridTable,
  DataGridTableBase,
  DataGridTableBody,
  DataGridTableBodyRow,
  DataGridTableBodyRowCell,
  DataGridTableBodyRowExpandded,
  DataGridTableBodyRowSkeleton,
  DataGridTableBodyRowSkeletonCell,
  DataGridTableEmpty,
  DataGridTableHead,
  DataGridTableHeadRow,
  DataGridTableHeadRowCell,
  DataGridTableHeadRowCellResize,
  DataGridTableLoader,
  DataGridTableRowSelect,
  DataGridTableRowSelectAll,
  DataGridTableRowSpacer,
};

