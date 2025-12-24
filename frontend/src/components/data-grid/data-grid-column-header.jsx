import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';
import { useDataGrid } from '@/components/data-grid/data-grid';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuPortal,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  ArrowDown,
  ArrowLeft,
  ArrowLeftToLine,
  ArrowRight,
  ArrowRightToLine,
  ArrowUp,
  Check,
  ChevronsUpDown,
  Settings2,
  ChevronDown,
  Filter
} from 'lucide-react';

function DataGridColumnHeader(
  {
    column,
    title = '',
    icon,
    className,
    filter,
    visibility = false
  }
) {
  const { t } = useTranslation();
  const { isLoading, table, props, recordCount } = useDataGrid();

  if (title && (!column.columnDef.meta || column.columnDef.meta.headerTitle !== title)) {
    if (!column.columnDef.meta) {
      column.columnDef.meta = {};
    }
    column.columnDef.meta.headerTitle = title;
  }

  const moveColumn = (direction) => {
    const currentOrder = [...table.getState().columnOrder];
    const currentIndex = currentOrder.indexOf(column.id);

    if (direction === 'left' && currentIndex > 0) {
      const newOrder = [...currentOrder];
      const [movedColumn] = newOrder.splice(currentIndex, 1);
      newOrder.splice(currentIndex - 1, 0, movedColumn);
      table.setColumnOrder(newOrder);
    }

    if (direction === 'right' && currentIndex < currentOrder.length - 1) {
      const newOrder = [...currentOrder];
      const [movedColumn] = newOrder.splice(currentIndex, 1);
      newOrder.splice(currentIndex + 1, 0, movedColumn);
      table.setColumnOrder(newOrder);
    }
  };

  const canMove = direction => {
    const currentOrder = table.getState().columnOrder;
    const currentIndex = currentOrder.indexOf(column.id);
    if (direction === 'left') {
      return currentIndex > 0;
    } else {
      return currentIndex < currentOrder.length - 1;
    }
  };

  const columnFilters = table.getState().columnFilters;
  const hasFilter = React.useMemo(() => {
    const filterValue = column.getFilterValue();
    if (filterValue === undefined || filterValue === null) return false;
    if (Array.isArray(filterValue)) return filterValue.length > 0;
    if (typeof filterValue === 'string') return filterValue.trim().length > 0;
    return Boolean(filterValue);
  }, [column, columnFilters]);

  const getFilterTooltipContent = React.useMemo(() => {
    if (!hasFilter) return null;
    
    const filterValue = column.getFilterValue();
    let filterOptions = column.columnDef.meta?.filterOptions;
    
    if (!filterOptions || !Array.isArray(filterOptions)) {
      filterOptions = null;
    }
    
    if (!filterValue) return null;
    
    const normalizeValue = (val) => {
      if (val === true) return 'true';
      if (val === false) return 'false';
      if (val === 'true' || val === 'True' || val === 'TRUE') return 'true';
      if (val === 'false' || val === 'False' || val === 'FALSE') return 'false';
      if (val === 1 || val === '1') return 'true';
      if (val === 0 || val === '0') return 'false';
      return String(val);
    };
    
    const findOptionLabel = (value) => {
      if (!filterOptions || !Array.isArray(filterOptions) || filterOptions.length === 0) {
        return null;
      }
      
      const normalizedValue = normalizeValue(value);
      
      for (const opt of filterOptions) {
        if (!opt || typeof opt !== 'object') continue;
        
        const normalizedOptValue = normalizeValue(opt.value);
        if (normalizedOptValue === normalizedValue && opt.label) {
          return opt.label;
        }
      }
      
      return null;
    };
    
    if (Array.isArray(filterValue)) {
      if (filterOptions && Array.isArray(filterOptions) && filterOptions.length > 0) {
        const selectedLabels = filterValue
          .map(value => findOptionLabel(value))
          .filter(label => label !== null && label !== undefined);
        
        if (selectedLabels.length > 0) {
          return selectedLabels.join(', ');
        }
      }
      return filterValue.map(v => {
        const label = findOptionLabel(v);
        return label || String(v);
      }).join(', ');
    }
    
    if (filterOptions && Array.isArray(filterOptions) && filterOptions.length > 0) {
      const label = findOptionLabel(filterValue);
      if (label) {
        return label;
      }
    }
    
    return String(filterValue);
  }, [hasFilter, column, columnFilters]);

  const headerLabel = () => {
    return (
      <div
        className={cn(
          'text-foreground font-normal inline-flex h-full items-center gap-1.5 text-[0.8125rem] leading-[calc(1.125/0.8125)] [&_svg]:size-3.5 [&_svg]:text-muted-foreground',
          className
        )}>
        {icon && icon}
        <span className="text-foreground">{title}</span>
      </div>
    );
  };

  const headerButton = () => {
    return (
      <div
        className={cn(
          'text-foreground rounded-md font-normal -ms-2 px-2 h-7 flex items-center gap-1.5 min-w-0 flex-1',
          className
        )}>
        {icon && <span className="text-foreground shrink-0">{icon}</span>}
        <span className="text-foreground truncate">{title}</span>
        {column.getCanSort() &&
          (column.getIsSorted() === 'desc' ? (
            <ArrowDown className="size-[0.8rem]! mt-px text-muted-foreground shrink-0" />
          ) : column.getIsSorted() === 'asc' ? (
            <ArrowUp className="size-[0.8rem]! mt-px text-muted-foreground shrink-0" />
          ) : (
            <ChevronsUpDown className="size-[0.8rem]! mt-px text-muted-foreground shrink-0" />
          ))}
      </div>
    );
  };

  const headerControls = () => {
    return (
      <div className="flex items-center h-full gap-1.5 justify-between w-full">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <div className="flex items-center h-full flex-1 cursor-pointer min-w-0 px-4 gap-1.5 hover:bg-primary/5 data-[state=open]:bg-primary/5 backdrop-blur-sm">
              {headerButton()}
              {hasFilter ? (
                getFilterTooltipContent ? (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Filter className="size-4 text-primary shrink-0 fill-primary" aria-label="Filtered" />
                    </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    <div className="space-y-1">
                      <div className="font-semibold">{t('components.dataGrid.columnFilter.activeFilter', 'Active filter')}</div>
                      <div className="text-xs">{getFilterTooltipContent}</div>
                    </div>
                  </TooltipContent>
                  </Tooltip>
                ) : (
                  <Filter className="size-4 text-primary shrink-0 fill-primary" aria-label="Filtered" />
                )
              ) : (
                <ChevronDown className="size-4 text-foreground shrink-0" />
              )}
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="min-w-48 w-auto max-w-full" align="end" alignOffset={3}>
            {filter && <DropdownMenuLabel>{filter}</DropdownMenuLabel>}

            {filter && (column.getCanSort() || column.getCanPin() || visibility) && <DropdownMenuSeparator />}

            {column.getCanSort() && (
              <>
                <DropdownMenuItem
                  onClick={() => {
                    if (column.getIsSorted() === 'asc') {
                      column.clearSorting();
                    } else {
                      column.toggleSorting(false);
                    }
                  }}
                  disabled={!column.getCanSort()}>
                  <ArrowUp className="size-3.5!" />
                  <span className="grow">{t('components.dataGrid.columnHeader.asc', 'Ascending')}</span>
                  {column.getIsSorted() === 'asc' && <Check className="size-4 opacity-100! text-foreground" />}
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => {
                    if (column.getIsSorted() === 'desc') {
                      column.clearSorting();
                    } else {
                      column.toggleSorting(true);
                    }
                  }}
                  disabled={!column.getCanSort()}>
                  <ArrowDown className="size-3.5!" />
                  <span className="grow">{t('components.dataGrid.columnHeader.desc', 'Descending')}</span>
                  {column.getIsSorted() === 'desc' && <Check className="size-4 opacity-100! text-foreground" />}
                </DropdownMenuItem>
              </>
            )}

            {(filter || column.getCanSort()) && (column.getCanSort() || column.getCanPin() || visibility) && (
              <DropdownMenuSeparator />
            )}

            {props.tableLayout?.columnsPinnable && column.getCanPin() && (
              <>
                <DropdownMenuItem
                  onClick={() => column.pin(column.getIsPinned() === 'left' ? false : 'left')}>
                  <ArrowLeftToLine className="size-3.5!" aria-hidden="true" />
                  <span className="grow">{t('components.dataGrid.columnHeader.pinToLeft', 'Pin to left')}</span>
                  {column.getIsPinned() === 'left' && <Check className="size-4 opacity-100! text-foreground" />}
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => column.pin(column.getIsPinned() === 'right' ? false : 'right')}>
                  <ArrowRightToLine className="size-3.5!" aria-hidden="true" />
                  <span className="grow">{t('components.dataGrid.columnHeader.pinToRight', 'Pin to right')}</span>
                  {column.getIsPinned() === 'right' && <Check className="size-4 opacity-100! text-foreground" />}
                </DropdownMenuItem>
              </>
            )}

            {props.tableLayout?.columnsMovable && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => moveColumn('left')}
                  disabled={!canMove('left') || column.getIsPinned() !== false}>
                  <ArrowLeft className="size-3.5!" aria-hidden="true" />
                  <span>{t('components.dataGrid.columnHeader.moveToLeft', 'Move to left')}</span>
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => moveColumn('right')}
                  disabled={!canMove('right') || column.getIsPinned() !== false}>
                  <ArrowRight className="size-3.5!" aria-hidden="true" />
                  <span>{t('components.dataGrid.columnHeader.moveToRight', 'Move to right')}</span>
                </DropdownMenuItem>
              </>
            )}

            {props.tableLayout?.columnsVisibility &&
              visibility &&
              (column.getCanSort() || column.getCanPin() || filter) && <DropdownMenuSeparator />}

            {props.tableLayout?.columnsVisibility && visibility && (
              <DropdownMenuSub>
                <DropdownMenuSubTrigger>
                  <Settings2 className="size-3.5!" />
                  <span>{t('components.dataGrid.columnHeader.columns', 'Columns')}</span>
                </DropdownMenuSubTrigger>
                <DropdownMenuPortal>
                  <DropdownMenuSubContent>
                    {table
                      .getAllColumns()
                      .filter((col) => typeof col.accessorFn !== 'undefined' && col.getCanHide())
                      .map((col) => {
                        return (
                          <DropdownMenuCheckboxItem
                            key={col.id}
                            checked={col.getIsVisible()}
                            onSelect={(event) => event.preventDefault()}
                            onCheckedChange={(value) => col.toggleVisibility(!!value)}
                            className="capitalize">
                            {col.columnDef.meta?.headerTitle || col.id}
                          </DropdownMenuCheckboxItem>
                        );
                      })}
                  </DropdownMenuSubContent>
                </DropdownMenuPortal>
              </DropdownMenuSub>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    );
  };

  if (
    props.tableLayout?.columnsMovable ||
    (props.tableLayout?.columnsVisibility && visibility) ||
    (props.tableLayout?.columnsPinnable && column.getCanPin()) ||
    filter
  ) {
    return headerControls();
  }

  if (column.getCanSort() || (props.tableLayout?.columnsResizable && column.getCanResize())) {
    return (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <div className="flex items-center h-full w-full cursor-pointer min-w-0 px-4 gap-1.5 hover:bg-primary/5 data-[state=open]:bg-primary/5">
            {headerButton()}
            {hasFilter ? (
              getFilterTooltipContent ? (
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Filter className="size-4 text-primary shrink-0 fill-primary" aria-label="Filtered" />
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    <div className="space-y-1">
                      <div className="font-semibold">{t('components.dataGrid.columnFilter.activeFilter', 'Active filter')}</div>
                      <div className="text-xs">{getFilterTooltipContent}</div>
                    </div>
                  </TooltipContent>
                </Tooltip>
              ) : (
                <Filter className="size-4 text-primary shrink-0 fill-primary" aria-label="Filtered" />
              )
            ) : (
              <ChevronDown className="size-4 text-foreground shrink-0" />
            )}
          </div>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="min-w-48 w-auto max-w-full" align="end">
          {column.getCanSort() && (
            <>
              <DropdownMenuItem
                onClick={() => {
                  if (column.getIsSorted() === 'asc') {
                    column.clearSorting();
                  } else {
                    column.toggleSorting(false);
                  }
                }}
                disabled={!column.getCanSort()}>
                <ArrowUp className="size-3.5!" />
                <span className="grow">{t('components.dataGrid.columnHeader.asc')}</span>
                {column.getIsSorted() === 'asc' && <Check className="size-4 opacity-100! text-foreground" />}
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => {
                  if (column.getIsSorted() === 'desc') {
                    column.clearSorting();
                  } else {
                    column.toggleSorting(true);
                  }
                }}
                disabled={!column.getCanSort()}>
                <ArrowDown className="size-3.5!" />
                <span className="grow">{t('components.dataGrid.columnHeader.desc')}</span>
                {column.getIsSorted() === 'desc' && <Check className="size-4 opacity-100! text-foreground" />}
              </DropdownMenuItem>
            </>
          )}
        </DropdownMenuContent>
      </DropdownMenu>
    );
  }

  return headerLabel();
}

export { DataGridColumnHeader };

