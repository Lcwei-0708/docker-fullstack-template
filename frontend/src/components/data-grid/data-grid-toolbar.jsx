import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { Search, X, Plus, Settings2, CheckSquare, Square, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useDataGrid } from '@/components/data-grid/data-grid';
import { DataGridColumnVisibility } from '@/components/data-grid/data-grid-column-visibility';

// Toolbar component with search, add, delete, and column visibility controls
function DataGridToolbar({
  onAdd,
  searchPlaceholder,
  className,
  showSearch = true,
  showAdd = true,
  showColumns = true,
  showSelect = true,
  searchValue: controlledSearchValue,
  onSearchChange,
  onSearch,
  enableSelection,
  onSelectionToggle,
  onDeleteSelected,
}) {
  const { t } = useTranslation();
  const { table } = useDataGrid();
  const [internalSearchValue, setInternalSearchValue] = React.useState('');
  const [, forceUpdate] = React.useReducer(x => x + 1, 0);

  // Get selected rows count
  const rowSelection = table.getState().rowSelection || {};
  const selectedRows = table.getSelectedRowModel().rows;
  const selectedCountFromState = Object.keys(rowSelection).filter(
    (key) => rowSelection[key] === true
  ).length;
  const selectedCountFromModel = selectedRows.length;
  const selectedRowCount = Math.max(selectedCountFromState, selectedCountFromModel);
  const hasSelectedRows = enableSelection && selectedRowCount > 0;

  // Monitor row selection changes and force re-render
  const rowSelectionStr = JSON.stringify(rowSelection);
  React.useEffect(() => {
    const checkInterval = setInterval(() => {
      const currentSelection = table.getState().rowSelection || {};
      const currentStr = JSON.stringify(currentSelection);
      if (currentStr !== rowSelectionStr) {
        forceUpdate();
      }
    }, 50);
    
    return () => clearInterval(checkInterval);
  }, [table, rowSelectionStr]);

  // Support both controlled and uncontrolled search
  const isControlled = controlledSearchValue !== undefined;
  const searchValue = isControlled ? controlledSearchValue : internalSearchValue;

  const handleSearchChange = (e) => {
    const value = e.target.value;
    if (isControlled && onSearchChange) {
      onSearchChange(value);
    } else {
      setInternalSearchValue(value);
    }
  };

  const handleSearchClick = () => {
    if (isControlled && onSearch) {
      onSearch(searchValue);
    } else {
      table.setGlobalFilter(searchValue);
    }
  };

  const handleSearchClear = () => {
    if (isControlled && onSearchChange) {
      onSearchChange('');
      if (onSearch) {
        onSearch('');
      }
    } else {
      setInternalSearchValue('');
      table.setGlobalFilter(undefined);
    }
  };

  const handleSearchKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearchClick();
    }
  };

  return (
    <div
      data-slot="data-grid-toolbar"
      className={cn(
        'flex flex-wrap items-center justify-between gap-2 p-4 border-b bg-sidebar',
        className
      )}>
      <div className="flex flex-wrap items-center gap-2 flex-1 min-w-[200px]">
        {showSearch && (
          <div className="flex items-center gap-2 flex-1 min-w-[200px] max-w-xs">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
              <Input
                id="data-grid-search"
                name="data-grid-search"
                placeholder={searchPlaceholder || t('components.dataGrid.toolbar.searchPlaceholder', 'Search...')}
                value={searchValue}
                onChange={handleSearchChange}
                onKeyDown={handleSearchKeyDown}
                className="px-9 h-9"
              />
              {searchValue && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
                  onClick={handleSearchClear}
                  aria-label={t('common.actions.reset', 'Reset')}>
                  <X className="size-4" />
                </Button>
              )}
            </div>
            <Button
              onClick={handleSearchClick}
              size="sm"
              variant="secondary"
              className="size-9">
              <Search className="size-4" />
            </Button>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        {(() => {
          const shouldShow = hasSelectedRows && onDeleteSelected;
          return shouldShow ? true : null;
        })() && (
          <Button
            onClick={onDeleteSelected}
            variant="destructive"
            size="sm">
            <Trash2 className="size-4" />
            {t('components.dataGrid.toolbar.deleteSelected', 'Delete selected')}
          </Button>
        )}

        {showAdd && onAdd && (
          <Button onClick={onAdd} size="sm">
            <Plus className="size-4" />
            {t('common.actions.create', 'Create')}
          </Button>
        )}

        {showSelect && onSelectionToggle && (
          <Button
            onClick={onSelectionToggle}
            variant={enableSelection ? 'default' : 'outline'}
            size="sm">
            {enableSelection ? (
              <CheckSquare className="size-4" />
            ) : (
              <Square className="size-4" />
            )}
            {t('components.dataGrid.toolbar.toggleSelection', 'Toggle selection')}
          </Button>
        )}

        {showColumns && (
          <DataGridColumnVisibility
            table={table}
            trigger={
              <Button variant="outline" size="sm">
                <Settings2 className="size-4" />
                {t('components.dataGrid.columnVisibility.toggleColumns', 'Toggle columns')}
              </Button>
            }
          />
        )}
      </div>
    </div>
  );
}

export { DataGridToolbar };

