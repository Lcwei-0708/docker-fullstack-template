import * as React from "react";
import { useSearchParams } from "react-router-dom";
import { DataGrid, DataGridContainer } from "@/components/data-grid/data-grid";
import { DataGridTable } from "@/components/data-grid/data-grid-table";
import { DataGridPagination } from "@/components/data-grid/data-grid-pagination";
import { DataGridToolbar } from "@/components/data-grid/data-grid-toolbar";
import { usersService } from "@/services/users.service";
import { rolesService } from "@/services/roles.service";
import { useTranslation } from "react-i18next";
import { useAuthStatus, useAuth } from "@/hooks/useAuth";
import { UserFormDialog } from "./user-form-dialog";
import { DeleteUserDialog } from "./delete-user-dialog";
import { ResetPasswordDialog } from "./reset-password-dialog";
import { useUsersTableColumns } from "./users-table-columns";
import {
  getCoreRowModel,
  getPaginationRowModel,
  useReactTable,
} from "@tanstack/react-table";

// Users table component with CRUD operations
export function UsersTable() {
  const { t } = useTranslation();
  const { hasPermission } = useAuthStatus();
  const { userId: currentUserId, user: currentUser } = useAuth();
  const canManageUsers = hasPermission("manage-users");

  // Control when component state is allowed to write back to URL params
  const allowUrlSyncRef = React.useRef(false);
  
  const effectiveCurrentUserId = React.useMemo(() => {
    return currentUserId || currentUser?.id;
  }, [currentUserId, currentUser]);
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [pagination, setPagination] = React.useState({
    total: 0,
    page: 1,
    per_page: 10,
    total_pages: 0,
  });

  // Query parameters state
  const [queryParams, setQueryParams] = React.useState({
    keyword: '',
    status: null,
    role: null,
    sort_by: null,
    desc: false,
  });

  // Parse URL search params to query params
  const parseUrlParams = React.useCallback((paramsToParse = null) => {
    const params = paramsToParse || searchParams;
    const result = {
      keyword: params.get('keyword') || '',
      status: params.get('status') || null,
      role: params.get('role') || null,
      sort_by: params.get('sort_by') || null,
      desc: params.get('desc') === 'true',
      page: parseInt(params.get('page') || '1', 10),
      per_page: parseInt(params.get('per_page') || '10', 10),
    };

    // Parse status and role as arrays if they contain commas
    if (result.status) {
      result.status = result.status.includes(',')
        ? result.status.split(',').filter(Boolean)
        : result.status;
    }
    if (result.role) {
      result.role = result.role.includes(',')
        ? result.role.split(',').filter(Boolean)
        : result.role;
    }

    return result;
  }, [searchParams]);

  // Update URL search params from query params and pagination
  const updateUrlParams = React.useCallback((params, paginationState) => {
    const newSearchParams = new URLSearchParams();

    if (params.keyword && params.keyword.trim()) {
      newSearchParams.set('keyword', params.keyword.trim());
    }

    if (params.status !== null && params.status !== undefined && params.status !== '') {
      const statusValue = Array.isArray(params.status)
        ? params.status.join(',')
        : params.status;
      newSearchParams.set('status', statusValue);
    }

    if (params.role !== null && params.role !== undefined && params.role !== '') {
      const roleValue = Array.isArray(params.role)
        ? params.role.join(',')
        : params.role;
      newSearchParams.set('role', roleValue);
    }

    if (params.sort_by) {
      newSearchParams.set('sort_by', params.sort_by);
      newSearchParams.set('desc', params.desc ? 'true' : 'false');
    }

    if (paginationState.page && paginationState.page > 1) {
      newSearchParams.set('page', paginationState.page.toString());
    }

    if (paginationState.per_page && paginationState.per_page !== 10) {
      newSearchParams.set('per_page', paginationState.per_page.toString());
    }

    // Only update URL if params changed
    const currentParams = searchParams.toString();
    const newParams = newSearchParams.toString();

    if (currentParams !== newParams) {
      setSearchParams(newSearchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  // Selection mode state
  const [enableSelection, setEnableSelection] = React.useState(false);

  // Row selection state
  const [rowSelection, setRowSelection] = React.useState({});

  // Dialog states
  const [isUserFormDialogOpen, setIsUserFormDialogOpen] = React.useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = React.useState(false);
  const [isDeleteSelectedDialogOpen, setIsDeleteSelectedDialogOpen] = React.useState(false);
  const [isResetPasswordDialogOpen, setIsResetPasswordDialogOpen] = React.useState(false);
  const [selectedUser, setSelectedUser] = React.useState(null);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [isDeleting, setIsDeleting] = React.useState(false);
  const [isResettingPassword, setIsResettingPassword] = React.useState(false);

  const [roles, setRoles] = React.useState([]);
  const rolesFetchingRef = React.useRef(false);
  const rolesFetchedRef = React.useRef(false);

  // Fetch roles list
  const fetchRoles = React.useCallback(async () => {
    if (rolesFetchingRef.current || rolesFetchedRef.current) {
      return;
    }

    rolesFetchingRef.current = true;
    const response = await rolesService.getAllRoles({ returnStatus: true });
    
    if (response.status === "success" && response.data) {
      const rolesList = Array.isArray(response.data)
        ? response.data
        : (response.data.roles || []);
      setRoles(rolesList);
      rolesFetchedRef.current = true;
    }
    
    rolesFetchingRef.current = false;
  }, []);

  // Load roles on component mount
  React.useEffect(() => {
    fetchRoles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fetch users data from API
  const fetchUsers = React.useCallback(async (params = {}) => {
    setIsLoading(true);

    const {
      page = 1,
      per_page = 10,
      keyword = '',
      status = null,
      role = null,
      sort_by = null,
      desc = false,
    } = params;

    const apiParams = {
      page,
      per_page,
    };

    if (keyword && keyword.trim()) {
      apiParams.keyword = keyword.trim();
    }

    if (status !== null && status !== undefined && status !== '') {
      const statusValue = Array.isArray(status) ? status.join(',') : status;
      apiParams.status = statusValue;
    }

    if (role !== null && role !== undefined && role !== '') {
      const roleValue = Array.isArray(role) ? role.join(',') : role;
      apiParams.role = roleValue;
    }

    if (sort_by) {
      apiParams.sort_by = sort_by;
      apiParams.desc = desc;
    }

    const response = await usersService.getAllUsers(apiParams, { returnStatus: true });

    if (response.status === "success" && response.data) {
      if (response.data.users && Array.isArray(response.data.users)) {
        setData(response.data.users);
        setPagination({
          total: response.data.total || 0,
          page: response.data.page || page,
          per_page: response.data.per_page || per_page,
          total_pages: response.data.total_pages || 0,
        });
      } else if (Array.isArray(response.data)) {
        setData(response.data);
      } else {
        setData([]);
      }
    }

    setIsLoading(false);
  }, []);

  // Open edit dialog for user
  const handleEdit = React.useCallback((user) => {
    React.startTransition(() => {
      setSelectedUser(user);
      setIsUserFormDialogOpen(true);
    });
  }, []);

  // Open delete confirmation dialog
  const handleDelete = React.useCallback((user) => {
    React.startTransition(() => {
      setSelectedUser(user);
      setIsDeleteDialogOpen(true);
    });
  }, []);

  // Open reset password dialog
  const handleResetPassword = React.useCallback((user) => {
    React.startTransition(() => {
      setSelectedUser(user);
      setIsResetPasswordDialogOpen(true);
    });
  }, []);

  // Confirm and execute user deletion
  const handleDeleteConfirm = React.useCallback(async (user) => {
    if (!user || !user.id) return;

    setIsDeleting(true);
    const response = await usersService.deleteUsers([user.id], { returnStatus: true });

    if (response.status === "success") {
      setIsDeleteDialogOpen(false);
      setSelectedUser(null);
      fetchUsers({
        page: pagination.page,
        per_page: pagination.per_page,
        keyword: queryParams.keyword || '',
        status: queryParams.status,
        role: queryParams.role,
        sort_by: queryParams.sort_by,
        desc: queryParams.desc,
      });
    }

    setIsDeleting(false);
  }, [pagination, queryParams, fetchUsers]);

  // Confirm and execute password reset
  const handleResetPasswordConfirm = React.useCallback(async (user, newPassword) => {
    if (!user || !user.id || !newPassword) return;

    setIsResettingPassword(true);
    const response = await usersService.resetUserPassword(user.id, newPassword, { returnStatus: true });

    if (response.status === "success") {
      setIsResetPasswordDialogOpen(false);
      setSelectedUser(null);
    }

    setIsResettingPassword(false);
  }, []);

  // Handle form submission (create or update user)
  const handleFormSubmit = React.useCallback(async (formValues) => {
    setIsSubmitting(true);

    const userData = { ...formValues };

    if (selectedUser) {
      delete userData.password;
    }

    const response = selectedUser
      ? await usersService.updateUser(selectedUser.id, userData, { returnStatus: true })
      : await usersService.createUser(userData, { returnStatus: true });

    if (response.status === "success") {
      setIsUserFormDialogOpen(false);
      setSelectedUser(null);
      fetchUsers({
        page: pagination.page,
        per_page: pagination.per_page,
        keyword: queryParams.keyword || '',
        status: queryParams.status,
        role: queryParams.role,
        sort_by: queryParams.sort_by,
        desc: queryParams.desc,
      });
    }

    setIsSubmitting(false);
  }, [selectedUser, pagination, queryParams, fetchUsers]);

  // Toggle row selection mode (only if user has manager-users permission)
  const handleSelectionToggle = React.useCallback(() => {
    if (canManageUsers) {
      setEnableSelection((prev) => !prev);
    }
  }, [canManageUsers]);

  // Disable selection mode if user loses manager-users permission
  React.useEffect(() => {
    if (!canManageUsers && enableSelection) {
      setEnableSelection(false);
      setRowSelection({});
    }
  }, [canManageUsers, enableSelection]);

  const columns = useUsersTableColumns({
    t,
    handleEdit,
    handleDelete,
    handleResetPassword,
    enableSelection,
    roles,
    canManageUsers,
  });

  // Open create user dialog
  const handleAdd = React.useCallback(() => {
    React.startTransition(() => {
      setSelectedUser(null);
      setIsUserFormDialogOpen(true);
    });
  }, []);

  // Create table instance with server-side pagination, sorting, and filtering
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: {
      pagination: {
        pageIndex: pagination.page - 1,
        pageSize: pagination.per_page,
      },
      columnPinning: {
        left: [],
        right: ['actions'],
      },
    },
    state: {
      rowSelection: enableSelection ? rowSelection : {},
    },
    onRowSelectionChange: React.useCallback((updater) => {
      if (enableSelection) {
        setRowSelection(updater);
      }
    }, [enableSelection]),
    // Avoid clamping pageIndex when total pages are not known yet
    pageCount: pagination.total_pages > 0 ? pagination.total_pages : -1,
    manualPagination: true,
    manualSorting: true,
    manualFiltering: true,
    enableRowSelection: enableSelection,
    getRowId: (row) => row.id,
    columnResizeMode: 'onChange',
    enableColumnResizing: true,
    enableColumnPinning: true,
  });

  // Open delete confirmation dialog for selected users
  const handleDeleteSelected = React.useCallback(() => {
    const rowSelectionState = table.getState().rowSelection || {};
    const selectedIds = Object.keys(rowSelectionState).filter(
      (key) => rowSelectionState[key] === true
    );
    if (!selectedIds || selectedIds.length === 0) return;
    setIsDeleteSelectedDialogOpen(true);
  }, [table]);

  // Confirm and execute deletion of selected users
  const handleDeleteSelectedConfirm = React.useCallback(async (filteredIds = null) => {
    const rowSelectionState = table.getState().rowSelection || {};
    let selectedUserIds = Object.keys(rowSelectionState).filter(
      (key) => rowSelectionState[key] === true
    );

    // If filteredIds is provided (from dialog when current user is included), use it
    if (filteredIds && Array.isArray(filteredIds)) {
      selectedUserIds = filteredIds;
    } else if (effectiveCurrentUserId) {
      // Otherwise, filter out current user ID if it exists
      const currentUserIdStr = String(effectiveCurrentUserId).trim();
      selectedUserIds = selectedUserIds.filter(id => {
        const idStr = String(id).trim();
        return idStr !== currentUserIdStr;
      });
    }

    if (!selectedUserIds || selectedUserIds.length === 0) {
      setIsDeleteSelectedDialogOpen(false);
      return;
    }

    setIsDeleting(true);
    const response = await usersService.deleteUsers(selectedUserIds, { returnStatus: true });

    if (response.status === "success") {
      setIsDeleteSelectedDialogOpen(false);
      setRowSelection({});
      table.resetRowSelection();
      fetchUsers({
        page: pagination.page,
        per_page: pagination.per_page,
        keyword: queryParams.keyword || '',
        status: queryParams.status,
        role: queryParams.role,
        sort_by: queryParams.sort_by,
        desc: queryParams.desc,
      });
    }

    setIsDeleting(false);
  }, [table, pagination, queryParams, fetchUsers, effectiveCurrentUserId]);

  const isAdjustingPinningRef = React.useRef(false);
  const prevRightPinnedRef = React.useRef('');

  // Clear selection when disabling selection mode
  React.useEffect(() => {
    if (!enableSelection) {
      setRowSelection({});
      if (table) {
        table.resetRowSelection();
      }
    }
  }, [enableSelection, table]);

  // Ensure select column is pinned to left and actions column is pinned to right
  React.useEffect(() => {
    if (isAdjustingPinningRef.current) {
      return;
    }

    const currentPinning = table.getState().columnPinning;
    const leftPinned = currentPinning.left || [];
    const rightPinned = currentPinning.right || [];

    let needsUpdate = false;
    const newPinning = { ...currentPinning };

    if (enableSelection) {
      if (!leftPinned.includes('select') || leftPinned[0] !== 'select') {
        const otherLeftPinned = leftPinned.filter(id => id !== 'select');
        newPinning.left = ['select', ...otherLeftPinned];
        needsUpdate = true;
      }
    } else {
      if (leftPinned.includes('select')) {
        newPinning.left = leftPinned.filter(id => id !== 'select');
        needsUpdate = true;
      }
    }

    // Ensure actions column is always the rightmost pinned column
    const otherRightPinned = rightPinned.filter(id => id !== 'actions');
    if (rightPinned.length === 0 || rightPinned[rightPinned.length - 1] !== 'actions') {
      newPinning.right = [...otherRightPinned, 'actions'];
      needsUpdate = true;
    }

    if (needsUpdate) {
      isAdjustingPinningRef.current = true;
      prevRightPinnedRef.current = newPinning.right?.join(',') || '';

      table.setColumnPinning(newPinning);
      requestAnimationFrame(() => {
        isAdjustingPinningRef.current = false;
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enableSelection, table.getState().columnPinning.right?.join(',')]);

  const prevTablePageRef = React.useRef(pagination.page);
  const prevTablePageSizeRef = React.useRef(pagination.per_page);
  const prevSortingRef = React.useRef(null);
  const prevFiltersRef = React.useRef(null);
  const isInitialMountRef = React.useRef(true);
  const isUpdatingUrlRef = React.useRef(false);
  const urlParamsInitializedRef = React.useRef(false);
  const skipNextUrlUpdateRef = React.useRef(false);
  const isHydratingFromUrlRef = React.useRef(false);
  const [urlParamsReady, setUrlParamsReady] = React.useState(false);

  // Initialize state from URL params on mount
  React.useEffect(() => {
    if (urlParamsInitializedRef.current) return;

    const urlParams = parseUrlParams();
    const hasUrlParams = urlParams.keyword || urlParams.status || urlParams.role ||
      urlParams.sort_by || urlParams.page > 1 || urlParams.per_page !== 10;

    if (hasUrlParams) {
      isUpdatingUrlRef.current = true;
      skipNextUrlUpdateRef.current = true;
      isHydratingFromUrlRef.current = true;
      allowUrlSyncRef.current = false;

      setPagination((prev) => ({
        ...prev,
        page: urlParams.page,
        per_page: urlParams.per_page,
      }));

      setQueryParams({
        keyword: urlParams.keyword || '',
        status: urlParams.status,
        role: urlParams.role,
        sort_by: urlParams.sort_by,
        desc: urlParams.desc,
      });

      setUrlParamsReady(true);

      requestAnimationFrame(() => {
        isUpdatingUrlRef.current = false;
      });
    } else {
      setUrlParamsReady(true);
      allowUrlSyncRef.current = true;
    }

    urlParamsInitializedRef.current = true;
  }, [parseUrlParams]);

  // Update URL when query params or pagination changes
  React.useEffect(() => {
    if (!urlParamsReady || isUpdatingUrlRef.current || isHydratingFromUrlRef.current) {
      return;
    }

    if (!allowUrlSyncRef.current) {
      return;
    }

    if (skipNextUrlUpdateRef.current) {
      skipNextUrlUpdateRef.current = false;
      return;
    }

    isUpdatingUrlRef.current = true;
    updateUrlParams(queryParams, {
      page: pagination.page,
      per_page: pagination.per_page,
    });

    // Reset flag after a short delay to allow state updates to complete
    requestAnimationFrame(() => {
      isUpdatingUrlRef.current = false;
    });
  }, [queryParams, pagination.page, pagination.per_page, updateUrlParams, urlParamsReady]);

  // Update search keyword state
  const handleSearchChange = React.useCallback((keyword) => {
    allowUrlSyncRef.current = true;
    setQueryParams((prev) => ({ ...prev, keyword }));
  }, []);

  // Execute search and fetch users
  const handleSearch = React.useCallback((keyword) => {
    allowUrlSyncRef.current = true;
    if (table.getState().pagination.pageIndex !== 0) {
      table.setPageIndex(0);
    }

    setQueryParams((prev) => ({ ...prev, keyword }));

    const tableState = table.getState();
    const tablePage = 1;
    const tablePageSize = tableState.pagination.pageSize;
    const sorting = tableState.sorting;
    const columnFilters = tableState.columnFilters;

    let sort_by = null;
    let desc = false;
    if (sorting && sorting.length > 0) {
      const sort = sorting[0];
      sort_by = sort.id;
      desc = sort.desc || false;
    }

    let status = null;
    const statusFilter = columnFilters.find((f) => f.id === 'status');
    if (statusFilter && statusFilter.value) {
      status = Array.isArray(statusFilter.value) ? statusFilter.value : [statusFilter.value];
    }

    let role = null;
    const roleFilter = columnFilters.find((f) => f.id === 'role');
    if (roleFilter && roleFilter.value) {
      role = Array.isArray(roleFilter.value) ? roleFilter.value : [roleFilter.value];
    }

    fetchUsers({
      page: tablePage,
      per_page: tablePageSize,
      keyword: keyword || '',
      status,
      role,
      sort_by,
      desc,
    });
  }, [table, fetchUsers]);

  // Handle pagination, sorting, and filtering changes
  const tableState = table.getState();
  const tablePageIndex = tableState.pagination.pageIndex;
  const tablePageSize = tableState.pagination.pageSize;
  const tableSorting = tableState.sorting;
  const tableFilters = tableState.columnFilters;

  React.useEffect(() => {
    // Skip if still initializing URL params
    if (!urlParamsReady) {
      return;
    }

    const tablePage = tablePageIndex + 1;
    const sorting = tableSorting;
    const columnFilters = tableFilters;

    let sort_by = null;
    let desc = false;
    if (sorting && sorting.length > 0) {
      const sort = sorting[0];
      sort_by = sort.id;
      desc = sort.desc || false;
    }

    let status = null;
    const statusFilter = columnFilters.find((f) => f.id === 'status');
    if (statusFilter && statusFilter.value) {
      status = Array.isArray(statusFilter.value) ? statusFilter.value : [statusFilter.value];
    }

    let role = null;
    const roleFilter = columnFilters.find((f) => f.id === 'role');
    if (roleFilter && roleFilter.value) {
      role = Array.isArray(roleFilter.value) ? roleFilter.value : [roleFilter.value];
    }

    const paginationChanged =
      tablePage !== prevTablePageRef.current || tablePageSize !== prevTablePageSizeRef.current;
    const sortingChanged = JSON.stringify(sorting) !== JSON.stringify(prevSortingRef.current);
    const filtersChanged = JSON.stringify(columnFilters) !== JSON.stringify(prevFiltersRef.current);
    const shouldResetPage = sortingChanged || filtersChanged;
    const targetPage = shouldResetPage ? 1 : tablePage;

    if (isInitialMountRef.current) {
      isInitialMountRef.current = false;

      // Use URL params if available, otherwise use table state
      const urlParams = parseUrlParams();
      const hasUrlParams = urlParams.keyword || urlParams.status || urlParams.role ||
        urlParams.sort_by || urlParams.page > 1 || urlParams.per_page !== 10;

      const initialPage = hasUrlParams ? urlParams.page : tablePage;
      const initialPerPage = hasUrlParams ? urlParams.per_page : tablePageSize;
      const initialKeyword = hasUrlParams ? urlParams.keyword : (queryParams.keyword || '');
      const initialStatus = hasUrlParams ? urlParams.status : status;
      const initialRole = hasUrlParams ? urlParams.role : role;
      const initialSortBy = hasUrlParams ? urlParams.sort_by : sort_by;
      const initialDesc = hasUrlParams && urlParams.sort_by ? urlParams.desc : desc;

      // Update query params if URL params exist
      if (hasUrlParams) {
        setQueryParams({
          keyword: initialKeyword,
          status: initialStatus,
          role: initialRole,
          sort_by: initialSortBy,
          desc: initialDesc,
        });
      }

      // Prepare sorting and filters for prev refs based on URL params
      let initialSorting = sorting;
      let initialFilters = columnFilters;
      if (hasUrlParams) {
        if (urlParams.sort_by) {
          initialSorting = [{ id: urlParams.sort_by, desc: urlParams.desc }];
        }
        const newFilters = [];
        if (urlParams.status) {
          const statusValue = Array.isArray(urlParams.status) ? urlParams.status : [urlParams.status];
          newFilters.push({ id: 'status', value: statusValue });
        }
        if (urlParams.role) {
          const roleValue = Array.isArray(urlParams.role) ? urlParams.role : [urlParams.role];
          newFilters.push({ id: 'role', value: roleValue });
        }
        if (newFilters.length > 0) {
          initialFilters = newFilters;
        }
      }

      // Update prev refs BEFORE updating table state to prevent double fetch
      // Use URL params values so when table state updates, prev refs match
      prevTablePageRef.current = initialPage;
      prevTablePageSizeRef.current = initialPerPage;
      prevSortingRef.current = initialSorting;
      prevFiltersRef.current = initialFilters;

      // Fetch users first (using URL params if available)
      fetchUsers({
        page: initialPage,
        per_page: initialPerPage,
        keyword: initialKeyword,
        status: initialStatus,
        role: initialRole,
        sort_by: initialSortBy,
        desc: initialDesc,
      });

      // Update table state to match URL
      if (hasUrlParams) {
        if (urlParams.page) {
          table.setPageIndex(urlParams.page - 1);
        }
        if (urlParams.per_page) {
          table.setPageSize(urlParams.per_page);
        }
        if (urlParams.sort_by) {
          table.setSorting([{ id: urlParams.sort_by, desc: urlParams.desc }]);
        }
        // Set column filters if URL has filter params
        const newFilters = [];
        if (urlParams.status) {
          const statusValue = Array.isArray(urlParams.status) ? urlParams.status : [urlParams.status];
          newFilters.push({ id: 'status', value: statusValue });
        }
        if (urlParams.role) {
          const roleValue = Array.isArray(urlParams.role) ? urlParams.role : [urlParams.role];
          newFilters.push({ id: 'role', value: roleValue });
        }
        if (newFilters.length > 0) {
          table.setColumnFilters(newFilters);
        }

        // Allow URL sync after hydration
        requestAnimationFrame(() => {
          isHydratingFromUrlRef.current = false;
          skipNextUrlUpdateRef.current = true;
        });
      }
      return;
    }

    if (paginationChanged || sortingChanged || filtersChanged) {
      allowUrlSyncRef.current = true;
      if (shouldResetPage && tablePage !== 1) {
        table.setPageIndex(0);
      }

      prevTablePageRef.current = targetPage;
      prevTablePageSizeRef.current = tablePageSize;
      prevSortingRef.current = sorting;
      prevFiltersRef.current = columnFilters;

      setQueryParams((prev) => ({
        ...prev,
        status,
        role,
        sort_by,
        desc,
      }));

      fetchUsers({
        page: targetPage,
        per_page: tablePageSize,
        keyword: queryParams.keyword || '',
        status,
        role,
        sort_by,
        desc,
      });
    }
  }, [
    tablePageIndex,
    tablePageSize,
    tableSorting,
    tableFilters,
    fetchUsers,
    queryParams.keyword,
    parseUrlParams,
    table,
    urlParamsReady,
  ]);

  // Sync table pagination state with server response
  React.useEffect(() => {
    const currentTablePage = table.getState().pagination.pageIndex + 1;

    if (currentTablePage !== pagination.page) {
      table.setPageIndex(pagination.page - 1);
      prevTablePageRef.current = pagination.page;
    }
    if (table.getState().pagination.pageSize !== pagination.per_page) {
      table.setPageSize(pagination.per_page);
      prevTablePageSizeRef.current = pagination.per_page;
    }
  }, [pagination.total_pages, pagination.page, pagination.per_page, table]);

  return (
    <>
      <DataGrid
        table={table}
        recordCount={pagination.total}
        isLoading={isLoading}
        loadingDelayMs={0}
        emptyMessage={t("components.dataGrid.table.noData", "No data available")}
        loadingMessage={t("components.dataGrid.table.loading", "Loading...")}
        tableLayout={{
          dense: false,
          cellBorder: false,
          rowBorder: true,
          rowRounded: false,
          stripped: false,
          headerSticky: true,
          headerBackground: true,
          headerBorder: true,
          columnsVisibility: true,
          columnsResizable: true,
          columnsPinnable: true,
          columnsMovable: false,
          columnsDraggable: false,
          rowsDraggable: false
        }}>
        <DataGridContainer border={true}>
          <DataGridToolbar
            onAdd={canManageUsers ? handleAdd : undefined}
            showAdd={canManageUsers}
            showSelect={canManageUsers}
            searchPlaceholder={t("components.dataGrid.toolbar.searchPlaceholder", "Search users...")}
            onSearchChange={handleSearchChange}
            onSearch={handleSearch}
            searchValue={queryParams.keyword}
            enableSelection={enableSelection}
            onSelectionToggle={canManageUsers ? handleSelectionToggle : undefined}
            onDeleteSelected={canManageUsers ? handleDeleteSelected : undefined}
          />
          <div className="overflow-auto max-h-[56dvh]">
            <DataGridTable />
          </div>
          <div className="border-t bg-sidebar py-3 px-4">
            <DataGridPagination />
          </div>
        </DataGridContainer>
      </DataGrid>

      {/* User Form Dialog */}
      <UserFormDialog
        open={isUserFormDialogOpen}
        onOpenChange={setIsUserFormDialogOpen}
        user={selectedUser}
        onSubmit={handleFormSubmit}
        isSubmitting={isSubmitting}
        roles={roles}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteUserDialog
        open={isDeleteDialogOpen}
        onOpenChange={setIsDeleteDialogOpen}
        user={selectedUser}
        currentUserId={effectiveCurrentUserId}
        onConfirm={handleDeleteConfirm}
        isDeleting={isDeleting}
      />

      {/* Delete Selected Users Confirmation Dialog */}
      <DeleteUserDialog
        open={isDeleteSelectedDialogOpen}
        onOpenChange={setIsDeleteSelectedDialogOpen}
        count={Object.keys(table.getState().rowSelection || {}).filter(
          (key) => table.getState().rowSelection[key] === true
        ).length}
        selectedUserIds={Object.keys(table.getState().rowSelection || {}).filter(
          (key) => table.getState().rowSelection[key] === true
        )}
        currentUserId={effectiveCurrentUserId}
        onConfirm={handleDeleteSelectedConfirm}
        isDeleting={isDeleting}
      />

      {/* Reset Password Dialog */}
      <ResetPasswordDialog
        open={isResetPasswordDialogOpen}
        onOpenChange={setIsResetPasswordDialogOpen}
        user={selectedUser}
        onConfirm={handleResetPasswordConfirm}
        isResetting={isResettingPassword}
      />
    </>
  );
}

export default UsersTable;