import { useTranslation } from 'react-i18next';
import { useDataGrid } from '@/components/data-grid/data-grid';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Separator } from '@/components/ui/separator';
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';
import { cn } from '@/lib/utils';

// Pagination component with page navigation and rows per page selector
function DataGridPagination(props) {
  const { t } = useTranslation();
  const { table, recordCount, isLoading } = useDataGrid();

  const defaultProps = {
    sizes: [5, 10, 25, 50, 100],
    sizesLabel: t('components.pagination.show', 'Show'),
    sizesDescription: t('components.pagination.perPage', 'per page'),
    sizesSkeleton: <Skeleton className="h-8 w-44" />,
    moreLimit: 5,
    more: false,
    info: 'components.pagination.info',
    infoSkeleton: <Skeleton className="h-8 w-108" />,
    rowsPerPageLabel: t('components.pagination.rowsPerPage', 'Rows per page'),
    previousPageLabel: t('components.pagination.previousPage', 'Previous page'),
    nextPageLabel: t('components.pagination.nextPage', 'Next page'),
    ellipsisText: '...',
  };

  const mergedProps = { ...defaultProps, ...props };

  const pageIndex = table.getState().pagination.pageIndex;
  const pageSize = table.getState().pagination.pageSize;
  const pageCount = table.getPageCount();
  const currentPage = pageIndex + 1;

  // Generate page numbers with ellipsis for pagination
  const generatePageNumbers = () => {
    if (pageCount <= 1) return [];
    
    const pages = [];
    const totalPages = pageCount;
    
    // If total pages <= 7, show all pages
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
      return pages;
    }
    
    // Always show first page
    pages.push(1);
    
    // Current page is near the beginning (pages 1-4)
    if (currentPage <= 4) {
      for (let i = 2; i <= 5; i++) {
        pages.push(i);
      }
      pages.push('ellipsis-end');
      pages.push(totalPages);
    }
    // Current page is near the end (last 4 pages)
    else if (currentPage >= totalPages - 3) {
      pages.push('ellipsis-start');
      for (let i = totalPages - 4; i <= totalPages; i++) {
        pages.push(i);
      }
    }
    // Current page is in the middle
    else {
      pages.push('ellipsis-start');
      pages.push(currentPage - 1);
      pages.push(currentPage);
      pages.push(currentPage + 1);
      pages.push('ellipsis-end');
      pages.push(totalPages);
    }
    
    return pages;
  };

  const pageNumbers = generatePageNumbers();

  // Render pagination buttons from page numbers
  const renderPageButtons = () => {
    return pageNumbers.map((page, index) => {
      if (page === 'ellipsis-start' || page === 'ellipsis-end') {
        return (
          <PaginationItem key={`ellipsis-${index}`}>
            <PaginationEllipsis />
          </PaginationItem>
        );
      }
      
      const pageIndexValue = page - 1;
      return (
        <PaginationItem key={page}>
          <PaginationLink
            size="icon"
            isActive={pageIndex === pageIndexValue}
            onClick={() => {
              if (pageIndex !== pageIndexValue) {
                table.setPageIndex(pageIndexValue);
              }
            }}
            className={cn('h-8 w-8 p-0 text-sm rounded-xs', pageIndex === pageIndexValue ? '' : 'text-muted-foreground')}>
            {page}
          </PaginationLink>
        </PaginationItem>
      );
    });
  };

  return (
    <div
      data-slot="data-grid-pagination"
      className={cn(
        'flex flex-wrap flex-col sm:flex-row justify-between items-center gap-2.5 py-2.5 sm:py-0 grow',
        mergedProps?.className
      )}>
      <div
        className="flex flex-wrap items-center space-x-2.5 pb-2.5 sm:pb-0 order-2 sm:order-1">
        {isLoading ? (
          mergedProps?.sizesSkeleton
        ) : (
          <>
            {recordCount !== undefined && recordCount !== null && (
              <div className="text-sm text-muted-foreground">
                {t('components.pagination.totalAccounts', 'Total {{count}} accounts', { count: recordCount.toLocaleString() })}
              </div>
            )}
            <Separator orientation="vertical" className="!w-1 !h-1 bg-muted-foreground rounded-full" />
            <div className="text-sm text-muted-foreground">{mergedProps.rowsPerPageLabel}</div>
            <Select
              value={`${pageSize}`}
              indicatorPosition="right"
              onValueChange={(value) => {
                const newPageSize = Number(value);
                table.setPageSize(newPageSize);
              }}>
              <SelectTrigger 
                className="w-fit font-normal" 
                size="default">
                <SelectValue placeholder={`${pageSize}`} />
              </SelectTrigger>
              <SelectContent side="top" className="min-w-[50px]">
                {mergedProps?.sizes?.map((size) => (
                  <SelectItem key={size} value={`${size}`}>
                    {size}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </>
        )}
      </div>
      <div
        className="flex flex-col sm:flex-row justify-center sm:justify-end items-center gap-2.5 pt-2.5 sm:pt-0 order-1 sm:order-2">
        {isLoading ? (
          mergedProps?.infoSkeleton
        ) : (
          pageCount > 1 && (
            <Pagination>
              <PaginationContent>
                <PaginationItem>
                  <PaginationPrevious
                    onClick={() => {
                      table.previousPage();
                    }}
                    disabled={!table.getCanPreviousPage()}
                    size="sm"
                    aria-label={mergedProps.previousPageLabel} />
                </PaginationItem>

                {renderPageButtons()}

                <PaginationItem>
                  <PaginationNext
                    onClick={() => {
                      table.nextPage();
                    }}
                    disabled={!table.getCanNextPage()}
                    size="sm"
                    aria-label={mergedProps.nextPageLabel} />
                </PaginationItem>
              </PaginationContent>
            </Pagination>
          )
        )}
      </div>
    </div>
  );
}

export { DataGridPagination };

