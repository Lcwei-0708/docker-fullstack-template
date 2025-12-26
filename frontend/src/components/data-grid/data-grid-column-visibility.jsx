import { useTranslation } from 'react-i18next';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

// Column visibility toggle dropdown
function DataGridColumnVisibility(
  {
    table,
    trigger
  }
) {
  const { t } = useTranslation();

  // Get display title for column
  const getColumnTitle = (column) => {
    if (column.columnDef.meta?.headerTitle) {
      return column.columnDef.meta.headerTitle;
    }

    if (typeof column.columnDef.header === 'string') {
      return column.columnDef.header;
    }

    return column.id;
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>{trigger}</DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[150px]">
        <DropdownMenuLabel className="font-medium">{t('components.dataGrid.columnVisibility.toggleColumns', 'Toggle columns')}</DropdownMenuLabel>
        {table
          .getAllColumns()
          .filter(
          (column) => typeof column.accessorFn !== 'undefined' && column.getCanHide()
        )
          .map((column) => {
            const title = getColumnTitle(column);
            return (
              <DropdownMenuCheckboxItem
                key={column.id}
                className="capitalize"
                checked={column.getIsVisible()}
                onSelect={(event) => event.preventDefault()}
                onCheckedChange={(value) => column.toggleVisibility(!!value)}>
                {title}
              </DropdownMenuCheckboxItem>
            );
          })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export { DataGridColumnVisibility };

