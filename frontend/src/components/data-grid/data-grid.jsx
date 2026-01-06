import * as React from 'react';
import { createContext, useContext } from 'react';
import { cn } from '@/lib/utils';

const DataGridContext = createContext(// eslint-disable-next-line @typescript-eslint/no-explicit-any
undefined);

// Hook to access DataGrid context
function useDataGrid() {
  const context = useContext(DataGridContext);
  if (!context) {
    throw new Error('useDataGrid must be used within a DataGridProvider');
  }
  return context;
}

// Context provider for DataGrid state
function DataGridProvider(
  {
    children,
    table,
    ...props
  }
) {
  const [hasVerticalScrollbar, setHasVerticalScrollbar] = React.useState(false);
  const [delayedLoading, setDelayedLoading] = React.useState(false);
  const rawIsLoading = props.isLoading || false;

  // Delay showing loading to avoid brief skeleton flashes on fast responses
  React.useEffect(() => {
    const delayMs = Number(props.loadingDelayMs ?? 0);

    if (!rawIsLoading) {
      setDelayedLoading(false);
      return undefined;
    }

    if (!delayMs || delayMs <= 0) {
      setDelayedLoading(true);
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setDelayedLoading(true);
    }, delayMs);

    return () => {
      window.clearTimeout(timer);
    };
  }, [rawIsLoading, props.loadingDelayMs]);

  return (
    <DataGridContext.Provider
      value={{
        props,
        table,
        recordCount: props.recordCount,
        isLoading: delayedLoading,
        rawIsLoading,
        hasVerticalScrollbar,
        setHasVerticalScrollbar,
      }}>
      {children}
    </DataGridContext.Provider>
  );
}

// Main DataGrid component with default props
function DataGrid(
  {
    children,
    table,
    ...props
  }
) {
  const defaultProps = {
    loadingMode: 'skeleton',
    loadingDelayMs: 100,
    tableLayout: {
      dense: false,
      cellBorder: false,
      rowBorder: true,
      rowRounded: false,
      stripped: false,
      headerSticky: false,
      headerBackground: true,
      headerBorder: true,
      width: 'fixed',
      columnsVisibility: false,
      columnsResizable: false,
      columnsPinnable: false,
      columnsMovable: false,
      columnsDraggable: false,
      rowsDraggable: false,
    },
    tableClassNames: {
      base: '',
      header: '',
      headerRow: '',
      headerSticky: 'sticky top-0 z-10 bg-background/90 backdrop-blur-xs',
      body: '',
      bodyRow: '',
      footer: '',
      edgeCell: '',
    },
  };

  const mergedProps = {
    ...defaultProps,
    ...props,
    tableLayout: {
      ...defaultProps.tableLayout,
      ...(props.tableLayout || {}),
    },
    tableClassNames: {
      ...defaultProps.tableClassNames,
      ...(props.tableClassNames || {}),
    },
  };

  if (!table) {
    throw new Error('DataGrid requires a "table" prop');
  }

  return (
    <DataGridProvider table={table} {...mergedProps}>
      {children}
    </DataGridProvider>
  );
}

// Container wrapper for DataGrid with border styling
function DataGridContainer({
  children,
  className,
  border = true
}) {
  return (
    <div
      data-slot="data-grid"
      className={cn('grid w-full', border && 'border border-border rounded-xl overflow-hidden shadow-2xs', className)}>
      {children}
    </div>
  );
}

export { useDataGrid, DataGridProvider, DataGrid, DataGridContainer };

