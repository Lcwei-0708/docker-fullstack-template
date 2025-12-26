import * as React from "react";
import { useSearchParams } from "react-router-dom";
import { usersService } from "@/services/users.service";
import { rolesService } from "@/services/roles.service";
import { useTranslation } from "react-i18next";
import { useAuthStatus, useAuth } from "@/hooks/useAuth";
import { UserFormDialog } from "./user-form-dialog";
import { DeleteUserDialog } from "./delete-user-dialog";
import { ResetPasswordDialog } from "./reset-password-dialog";
import { UserCard } from "./users-card";
import { Virtuoso } from "react-virtuoso";
import { Spinner } from "@/components/ui/spinner";
import { UsersCardListToolbar } from "./users-card-list-toolbar";

// Users card list view component for mobile with CRUD operations
export const UsersCardList = React.forwardRef(function UsersCardList(_, ref) {
  const { t } = useTranslation();
  const { hasPermission } = useAuthStatus();
  const { userId: currentUserId, user: currentUser } = useAuth();
  const canManageUsers = hasPermission("manage-users");
  
  // Get current user ID from user object if userId is not available
  const effectiveCurrentUserId = React.useMemo(() => {
    return currentUserId || currentUser?.id;
  }, [currentUserId, currentUser]);
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isLoadingMore, setIsLoadingMore] = React.useState(false);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [hasMore, setHasMore] = React.useState(true);
  const perPage = 15;
  const initialLoadCompleteRef = React.useRef(false);

  // Selection mode state
  const [isSelectionMode, setIsSelectionMode] = React.useState(false);
  const [selectedUsers, setSelectedUsers] = React.useState(new Set());

  // Query parameters state
  const [queryParams, setQueryParams] = React.useState({
    keyword: '',
    status: null,
    role: null,
    sort_by: 'first_name',
    desc: false,
  });

  // Parse URL search params to query params
  const parseUrlParams = React.useCallback((paramsToParse = null) => {
    const params = paramsToParse || searchParams;
    const sortByParam = params.get('sort_by');
    const descParam = params.get('desc');
    const result = {
      keyword: params.get('keyword') || '',
      status: params.get('status') || null,
      role: params.get('role') || null,
      sort_by: sortByParam || 'first_name',
      desc: descParam === 'true' ? true : (descParam === 'false' ? false : false),
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

  // Update URL search params from query params
  const updateUrlParams = React.useCallback((params) => {
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

    // Only update URL if params changed
    const currentParams = searchParams.toString();
    const newParams = newSearchParams.toString();

    if (currentParams !== newParams) {
      setSearchParams(newSearchParams, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  // Dialog states
  const [isUserFormDialogOpen, setIsUserFormDialogOpen] = React.useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = React.useState(false);
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
  const fetchUsers = React.useCallback(async (params = {}, append = false) => {
    if (append) {
      setIsLoadingMore(true);
    } else {
      setIsLoading(true);
    }

    const {
      page = 1,
      keyword = '',
      status = null,
      role = null,
      sort_by = null,
      desc = false,
    } = params;

    const apiParams = {
      page,
      per_page: perPage,
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

    try {
      const response = await usersService.getAllUsers(apiParams, { returnStatus: true });

      if (response.status === "success" && response.data) {
        if (response.data.users && Array.isArray(response.data.users)) {
          if (append) {
            setData((prev) => [...prev, ...response.data.users]);
          } else {
            setData(response.data.users);
            // Mark initial load as complete when first page is loaded
            if (page === 1) {
              initialLoadCompleteRef.current = true;
            }
          }
          
          const totalPages = response.data.total_pages || 0;
          setHasMore(page < totalPages);
          setCurrentPage(page);
        } else if (Array.isArray(response.data)) {
          if (append) {
            setData((prev) => [...prev, ...response.data]);
          } else {
            setData(response.data);
            // Mark initial load as complete when first page is loaded
            if (page === 1) {
              initialLoadCompleteRef.current = true;
            }
          }
          setHasMore(response.data.length >= perPage);
        } else {
          if (!append) {
            setData([]);
            initialLoadCompleteRef.current = true;
          }
          setHasMore(false);
        }
      }
    } catch (error) {
      console.error("Failed to fetch users:", error);
      if (!append) {
        setData([]);
        initialLoadCompleteRef.current = true;
      }
      setHasMore(false);
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
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
      // Remove deleted user from list
      setData((prev) => prev.filter((u) => u.id !== user.id));
    }

    setIsDeleting(false);
  }, []);

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
      
      if (selectedUser) {
        // Update existing user in list
        setData((prev) =>
          prev.map((u) => (u.id === selectedUser.id ? { ...u, ...userData } : u))
        );
      } else {
        // Reset and reload from first page for new user
        setCurrentPage(1);
        setHasMore(true);
        fetchUsers({
          page: 1,
          keyword: queryParams.keyword || '',
          status: queryParams.status,
          role: queryParams.role,
          sort_by: queryParams.sort_by,
          desc: queryParams.desc,
        });
      }
    }

    setIsSubmitting(false);
  }, [selectedUser, queryParams, fetchUsers]);

  // Open create user dialog
  const handleAdd = React.useCallback(() => {
    React.startTransition(() => {
      setSelectedUser(null);
      setIsUserFormDialogOpen(true);
    });
  }, []);

  // Expose handleAdd via ref for parent component
  React.useImperativeHandle(ref, () => ({
    handleAdd,
  }), [handleAdd]);

  // Handle selection mode toggle
  const handleSelectionModeToggle = React.useCallback(() => {
    setIsSelectionMode((prev) => {
      if (prev) {
        // Exit selection mode - clear selections
        setSelectedUsers(new Set());
      }
      return !prev;
    });
  }, []);

  // Handle user selection toggle
  const handleUserSelect = React.useCallback((user) => {
    if (!user || !user.id) return;
    
    setSelectedUsers((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(user.id)) {
        newSet.delete(user.id);
      } else {
        newSet.add(user.id);
      }
      return newSet;
    });
  }, []);

  // Open delete confirmation dialog for selected users
  const handleDeleteSelected = React.useCallback(() => {
    if (selectedUsers.size === 0) return;
    setIsDeleteDialogOpen(true);
  }, [selectedUsers]);

  // Confirm and execute deletion of selected users
  const handleDeleteSelectedConfirm = React.useCallback(async (userIds) => {
    if (!userIds || userIds.length === 0) {
      // If no userIds provided (e.g., only current user was selected), just close dialog
      setIsDeleteDialogOpen(false);
      setSelectedUsers(new Set());
      setIsSelectionMode(false);
      return;
    }

    setIsDeleting(true);
    const response = await usersService.deleteUsers(userIds, { returnStatus: true });

    if (response.status === "success") {
      setIsDeleteDialogOpen(false);
      // Remove deleted users from list
      setData((prev) => prev.filter((u) => !userIds.includes(u.id)));
      setSelectedUsers(new Set());
      setIsSelectionMode(false);
    }

    setIsDeleting(false);
  }, []);

  // Handle select all users
  const handleSelectAll = React.useCallback(() => {
    const allUserIds = new Set(data.map((user) => user.id));
    setSelectedUsers(allUserIds);
  }, [data]);

  // Handle deselect all users
  const handleDeselectAll = React.useCallback(() => {
    setSelectedUsers(new Set());
  }, []);

  // Track loading pages to prevent duplicate requests
  const loadingPagesRef = React.useRef(new Set());
  const isRequestingRef = React.useRef(false);

  // Infinite scroll: Load more users when reaching bottom
  const loadMoreUsers = React.useCallback(() => {
    if (isLoadingMore || !hasMore || isLoading || isRequestingRef.current) return;

    const nextPage = currentPage + 1;
    
    // Prevent duplicate requests for the same page
    if (loadingPagesRef.current.has(nextPage)) {
      return;
    }

    isRequestingRef.current = true;
    loadingPagesRef.current.add(nextPage);
    
    // Wrap fetchUsers in Promise to track completion
    Promise.resolve(fetchUsers(
      {
        page: nextPage,
        keyword: queryParams.keyword || '',
        status: queryParams.status,
        role: queryParams.role,
        sort_by: queryParams.sort_by,
        desc: queryParams.desc,
      },
      true // append mode
    )).finally(() => {
      loadingPagesRef.current.delete(nextPage);
      isRequestingRef.current = false;
    });
  }, [currentPage, hasMore, isLoading, isLoadingMore, queryParams, fetchUsers]);

  // Virtualization: Container ref for Virtuoso
  const containerRef = React.useRef(null);
  const [listHeight, setListHeight] = React.useState(600); // Default height
  
  // Calculate list height from container
  React.useEffect(() => {
    const updateHeight = () => {
      if (containerRef.current) {
        // Use clientHeight directly since container now uses h-full
        const height = containerRef.current.clientHeight;
        setListHeight(Math.max(height, 400)); // Minimum height
      }
    };
    
    // Use ResizeObserver for better performance
    const resizeObserver = new ResizeObserver(() => {
      updateHeight();
    });
    
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
      updateHeight();
    }
    
    // Also listen to window resize as fallback
    window.addEventListener('resize', updateHeight);
    
    return () => {
      resizeObserver.disconnect();
      window.removeEventListener('resize', updateHeight);
    };
  }, []);

  // Track if user has scrolled (to prevent immediate endReached trigger)
  const hasUserScrolledRef = React.useRef(false);
  
  // Infinite scroll: Load more when reaching the end
  const handleEndReached = React.useCallback(() => {
    // Prevent loading more during initialization or before initial load completes
    if (!urlParamsInitializedRef.current || isInitializingRef.current) {
      return;
    }
    
    // Only load more if we have more data and not already loading
    if (hasMore && !isLoadingMore && !isRequestingRef.current && !isLoading && initialLoadCompleteRef.current) {
      loadMoreUsers();
    }
  }, [hasMore, isLoadingMore, isLoading, loadMoreUsers]);


  const isUpdatingUrlRef = React.useRef(false);
  const urlParamsInitializedRef = React.useRef(false);
  const isInitializingRef = React.useRef(false);

  // Initialize state from URL params on mount (only once)
  React.useEffect(() => {
    if (urlParamsInitializedRef.current) return;

    isInitializingRef.current = true;
    const urlParams = parseUrlParams();

    // Always set query params, using URL params or defaults
    isUpdatingUrlRef.current = true;

    const initialParams = {
      keyword: urlParams.keyword || '',
      status: urlParams.status,
      role: urlParams.role,
      sort_by: urlParams.sort_by || 'first_name',
      desc: urlParams.desc || false,
    };

    // Set prevQueryParamsRef BEFORE setQueryParams to prevent useEffect from triggering
    prevQueryParamsRef.current = { ...initialParams };
    
    // Mark as fetching to prevent other effects from triggering
    isFetchingRef.current = true;
    
    // Reset initial load flag for new initialization
    initialLoadCompleteRef.current = false;
    hasUserScrolledRef.current = false;
    
    // Mark as initialized immediately to prevent re-initialization
    urlParamsInitializedRef.current = true;
    
    setQueryParams(initialParams);

    // Reset flag after state updates
    requestAnimationFrame(() => {
      isUpdatingUrlRef.current = false;
      isInitializingRef.current = false;
      
      // Trigger initial fetch after initialization is complete
      setCurrentPage(1);
      setHasMore(true);
      fetchUsersRef.current({
        page: 1,
        keyword: initialParams.keyword || '',
        status: initialParams.status,
        role: initialParams.role,
        sort_by: initialParams.sort_by,
        desc: initialParams.desc,
      }).finally(() => {
        isFetchingRef.current = false;
      });
    });
  }, []); // Only run once on mount, not when searchParams change

  // Update URL when query params change
  React.useEffect(() => {
    if (!urlParamsInitializedRef.current || isUpdatingUrlRef.current) {
      return;
    }

    isUpdatingUrlRef.current = true;
    updateUrlParams(queryParams);

    // Reset flag after a short delay to allow state updates to complete
    requestAnimationFrame(() => {
      isUpdatingUrlRef.current = false;
    });
  }, [queryParams, updateUrlParams]);

  // Update search keyword state
  const handleSearchChange = React.useCallback((keyword) => {
    setQueryParams((prev) => ({ ...prev, keyword }));
  }, []);

  // Execute search and fetch users
  const handleSearch = React.useCallback((keyword) => {
    setQueryParams((prev) => ({ ...prev, keyword }));
    // Note: fetchUsers will be triggered by useEffect when queryParams changes
  }, []);

  // Handle filter changes
  const handleFilter = React.useCallback((filterParams) => {
    setQueryParams((prev) => ({
      ...prev,
      status: filterParams.status,
      role: filterParams.role,
    }));
    // Note: fetchUsers will be triggered by useEffect when queryParams changes
  }, []);

  // Handle sort changes
  const handleSort = React.useCallback((sortParams) => {
    setQueryParams((prev) => ({
      ...prev,
      sort_by: sortParams.sort_by,
      desc: sortParams.desc,
    }));
    // Note: fetchUsers will be triggered by useEffect when queryParams changes
  }, []);

  // Track previous query params to detect changes
  const prevQueryParamsRef = React.useRef(null);
  const isInitialMountRef = React.useRef(true);
  const fetchUsersRef = React.useRef(fetchUsers);
  const isFetchingRef = React.useRef(false);
  
  // Keep fetchUsers ref up to date
  React.useEffect(() => {
    fetchUsersRef.current = fetchUsers;
  }, [fetchUsers]);
  
  // Load users when query params change (not on initial mount)
  React.useEffect(() => {
    if (!urlParamsInitializedRef.current) return;
    if (isInitializingRef.current) return; // Skip during initialization
    if (isFetchingRef.current) return; // Prevent concurrent fetches

    // Check if query params actually changed
    const prev = prevQueryParamsRef.current;
    if (prev === null) return; // Initial mount is handled separately
    
    const queryParamsChanged = (
      prev.keyword !== queryParams.keyword ||
      prev.status !== queryParams.status ||
      prev.role !== queryParams.role ||
      prev.sort_by !== queryParams.sort_by ||
      prev.desc !== queryParams.desc
    );

    // Only load when query params actually changed
    if (queryParamsChanged) {
      prevQueryParamsRef.current = { ...queryParams };
      isFetchingRef.current = true;
      initialLoadCompleteRef.current = false; // Reset initial load flag when params change
      hasUserScrolledRef.current = false; // Reset scroll flag when params change
      
      setCurrentPage(1);
      setHasMore(true);
      
      fetchUsersRef.current({
        page: 1,
        keyword: queryParams.keyword || '',
        status: queryParams.status,
        role: queryParams.role,
        sort_by: queryParams.sort_by,
        desc: queryParams.desc,
      }).finally(() => {
        isFetchingRef.current = false;
      });
    }
  }, [queryParams]);

  return (
    <>
      <div className="flex flex-col h-[calc(100dvh-8rem)]">
        <div className="shrink-0 pb-2">
          <UsersCardListToolbar
            keyword={queryParams.keyword}
            onSearchChange={handleSearchChange}
            onSearch={handleSearch}
            onClear={() => {
              handleSearchChange('');
              handleSearch('');
            }}
            status={queryParams.status}
            role={queryParams.role}
            sortBy={queryParams.sort_by}
            desc={queryParams.desc}
            roles={roles}
            onFilter={handleFilter}
            onSort={handleSort}
            isSelectionMode={isSelectionMode}
            onSelectionModeToggle={handleSelectionModeToggle}
            selectedCount={selectedUsers.size}
            onDeleteSelected={handleDeleteSelected}
            onSelectAll={handleSelectAll}
            onDeselectAll={handleDeselectAll}
            totalCount={data.length}
          />
        </div>

        <div className="flex-1 min-h-0 border-t-1 border-accent-foreground/20 shadow-xs">
          <div 
            ref={containerRef}
            className="h-full bg-muted/60"
          >
            {isLoading && data.length === 0 ? (
              <div className="flex items-center justify-center py-12 text-muted-foreground px-0">
                <Spinner className="!size-6" />
              </div>
            ) : data.length === 0 ? (
              <div className="flex items-center justify-center py-12 text-muted-foreground px-0">
                <p>{t("components.dataGrid.table.noData", "No data available")}</p>
              </div>
            ) : (
              <Virtuoso
                style={{ height: `${listHeight}px`, width: '100%' }}
                data={data}
                totalCount={data.length}
                itemContent={(index, user) => {
                  if (!user) return null;

                  return (
                    <div className="px-0 bg-muted/60">
                      <UserCard
                        user={user}
                        onEdit={handleEdit}
                        onDelete={handleDelete}
                        onResetPassword={handleResetPassword}
                        canManageUsers={canManageUsers}
                        isSelectionMode={isSelectionMode}
                        isSelected={selectedUsers.has(user.id)}
                        onSelect={handleUserSelect}
                        onLongPress={() => {
                          if (!isSelectionMode && canManageUsers) {
                            setIsSelectionMode(true);
                            setSelectedUsers(new Set([user.id]));
                          }
                        }}
                      />
                    </div>
                  );
                }}
                endReached={handleEndReached}
                onScroll={(e) => {
                  // Mark that user has scrolled
                  if (e.scrollTop > 0) {
                    hasUserScrolledRef.current = true;
                  }
                }}
                overscan={200}
                components={{
                  Footer: () => {
                    if (isLoadingMore) {
                      return (
                        <div className="flex items-center justify-center py-4 px-0">
                          <Spinner className="size-6" />
                        </div>
                      );
                    }
                    if (!hasMore && data.length > 0) {
                      return (
                        <div className="flex items-center justify-center pt-4 pb-12 px-0">
                          <p className="text-sm text-muted-foreground">
                            {t("components.dataGrid.table.noMoreData", "No more data")}
                          </p>
                        </div>
                      );
                    }
                    return null;
                  },
              }}
              />
            )}
          </div>
        </div>
      </div>

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
        user={selectedUsers.size > 0 ? null : selectedUser}
        count={selectedUsers.size > 0 ? selectedUsers.size : undefined}
        selectedUserIds={selectedUsers.size > 0 ? Array.from(selectedUsers) : undefined}
        currentUserId={effectiveCurrentUserId}
        onConfirm={(userOrIds) => {
          if (selectedUsers.size > 0) {
            // Batch delete
            if (Array.isArray(userOrIds)) {
              handleDeleteSelectedConfirm(userOrIds);
            } else {
              // No IDs to delete (e.g., only current user was selected)
              handleDeleteSelectedConfirm([]);
            }
          } else {
            // Single delete
            handleDeleteConfirm(userOrIds);
          }
        }}
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
});