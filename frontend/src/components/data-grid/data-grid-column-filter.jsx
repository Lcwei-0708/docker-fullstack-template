import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Separator } from '@/components/ui/separator';
import { Check, CirclePlus } from 'lucide-react';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command';

// Column filter component with multi-select dropdown
function DataGridColumnFilter(
  {
    column,
    title,
    options,
    className,
    buttonClassName,
    popoverClassName
  }
) {
  const { t } = useTranslation();
  const facets = column?.getFacetedUniqueValues();
  const selectedValues = new Set(column?.getFilterValue());

  // Store filter options in column meta for tooltip display (set immediately, not just in useEffect)
  if (options && Array.isArray(options)) {
    if (!column.columnDef.meta) {
      column.columnDef.meta = {};
    }
    // Only update if not already set or if options have changed
    if (!column.columnDef.meta.filterOptions || 
        JSON.stringify(column.columnDef.meta.filterOptions) !== JSON.stringify(options)) {
      column.columnDef.meta.filterOptions = options;
    }
  }

  // Also set in useEffect to ensure it's updated when options change
  React.useEffect(() => {
    if (options && Array.isArray(options)) {
      if (!column.columnDef.meta) {
        column.columnDef.meta = {};
      }
      column.columnDef.meta.filterOptions = options;
    }
  }, [column, options]);

  return (
    <Popover className={className}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className={cn("font-normal", buttonClassName)}>
          <CirclePlus className="size-4" />
          {title}
          {selectedValues?.size > 0 && (
            <>
              <Separator orientation="vertical" className="mx-2 h-4" />
              <Badge variant="outline" className="rounded-sm px-2 font-semibold bg-primary/15 text-primary border-primary/50 lg:hidden">
                {selectedValues.size}
              </Badge>
              <div className="hidden space-x-1 lg:flex">
                {selectedValues.size > 2 ? (
                  <Badge variant="outline" className="rounded-sm px-2 font-semibold bg-primary/15 text-primary border-primary/50">
                    {selectedValues.size} {t('components.dataGrid.columnFilter.selected', 'selected')}
                  </Badge>
                ) : (
                  options
                    .filter((option) => selectedValues.has(option.value))
                    .map((option) => (
                      <Badge
                        variant="outline"
                        key={option.value}
                        className="rounded-sm px-2 font-semibold bg-primary/15 text-primary border-primary/50">
                        {option.label}
                      </Badge>
                    ))
                )}
              </div>
            </>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className={cn("w-[93.5%] min-w-24 p-0", popoverClassName)} align="start">
        <Command>
          <CommandInput placeholder={title} />
          <CommandList>
            <CommandEmpty>{t('components.dataGrid.columnFilter.noResults', 'No results found')}</CommandEmpty>
            <CommandGroup>
              {options.map((option) => {
                const isSelected = selectedValues.has(option.value);
                return (
                  <CommandItem
                    key={option.value}
                    onSelect={() => {
                      if (isSelected) {
                        selectedValues.delete(option.value);
                      } else {
                        selectedValues.add(option.value);
                      }
                      const filterValues = Array.from(selectedValues);
                      column?.setFilterValue(filterValues.length ? filterValues : undefined);
                    }}>
                    <div
                      className={cn(
                        'me-2 flex h-4 w-4 items-center justify-center rounded border border-muted-foreground',
                        isSelected ? 'bg-primary border-primary' : 'opacity-50 [&_svg]:invisible'
                      )}>
                      <Check className={cn('h-4 w-4', isSelected && 'text-primary-foreground')} />
                    </div>
                    <span className={cn(isSelected && 'text-foreground')}>{option.label}</span>
                    {facets?.get(option.value) && (
                      <span
                        className="ms-auto flex h-4 w-4 items-center justify-center font-mono text-xs">
                        {facets.get(option.value)}
                      </span>
                    )}
                  </CommandItem>
                );
              })}
            </CommandGroup>
            {selectedValues.size > 0 && (
              <>
                <CommandSeparator />
                <CommandGroup>
                  <CommandItem
                    onSelect={() => column?.setFilterValue(undefined)}
                    className="justify-center text-center">
                    {t('components.dataGrid.columnFilter.clearFilters', 'Clear filters')}
                  </CommandItem>
                </CommandGroup>
              </>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}

export { DataGridColumnFilter };

