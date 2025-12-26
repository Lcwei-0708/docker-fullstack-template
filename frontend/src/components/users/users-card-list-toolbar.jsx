import * as React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useIsMobile } from "@/hooks/useMobile";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  ActionBar,
  ActionBarSelection,
  ActionBarGroup,
  ActionBarItem,
  ActionBarClose,
} from "@/components/ui/action-bar";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { Search, Filter, ArrowUpDown, ArrowDownNarrowWide, ArrowUpWideNarrow, Check, CirclePlus, Trash2, CheckCheck, X } from "lucide-react";


// Filter field popover component
function FilterFieldPopover({
  label,
  selectedValues,
  options,
  onValueChange,
  onRemoveValue,
  onClearAll,
  getValueLabel,
  open,
  onOpenChange,
}) {
  const { t } = useTranslation();

  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className="w-auto justify-start font-normal"
        >
          <CirclePlus className="size-4" />
          {label}
          {selectedValues.length > 0 && (
            <>
              <Separator orientation="vertical" className="mx-2 h-5" />
              {selectedValues.length > 2 ? (
                <Badge variant="outline" className="rounded-sm px-2 font-semibold bg-primary/15 text-primary border-primary/50">
                  {selectedValues.length} {t("common.selected", "selected")}
                </Badge>
              ) : (
                <div className="flex space-x-1">
                  {selectedValues.map((value) => (
                    <Badge
                      key={value}
                      variant="outline"
                      className="rounded-xs px-2 py-0.5 font-semibold bg-primary/15 text-primary border-primary/50"
                    >
                      {getValueLabel(value)}
                      <span
                        onClick={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          onRemoveValue(value);
                        }}
                        className="rounded-full hover:bg-primary/20 py-0.5 cursor-pointer inline-flex items-center justify-center"
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.stopPropagation();
                            e.preventDefault();
                            onRemoveValue(value);
                          }
                        }}
                      >
                        <X className="size-4" />
                      </span>
                    </Badge>
                  ))}
                </div>
              )}
            </>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-48 p-0" align="start">
        <Command>
          <CommandInput placeholder={t("common.actions.filter", "Filter")} />
          <CommandList>
            <CommandEmpty>{t("common.noResults", "No results found")}</CommandEmpty>
            <CommandGroup>
              {options.map((option) => {
                const optionValue = typeof option === 'string' ? option : option.value;
                const optionLabel = typeof option === 'string' ? option : option.label;
                const isSelected = selectedValues.includes(optionValue);
                return (
                  <CommandItem
                    key={optionValue}
                    onSelect={() => onValueChange(optionValue)}
                    className="py-2"
                  >
                    <div
                      className={cn(
                        "me-2 flex h-4 w-4 items-center justify-center rounded border border-muted-foreground",
                        isSelected ? "bg-primary border-primary" : "opacity-50 [&_svg]:invisible"
                      )}
                    >
                      <Check className={cn("h-4 w-4", isSelected && "text-primary-foreground")} />
                    </div>
                    <span className={cn(isSelected && "text-foreground")}>
                      {optionLabel}
                    </span>
                  </CommandItem>
                );
              })}
            </CommandGroup>
            {selectedValues.length > 0 && (
              <>
                <CommandSeparator />
                <CommandGroup>
                  <CommandItem
                    onSelect={() => {
                      onClearAll?.();
                    }}
                    className="justify-center text-center"
                  >
                    {t("common.actions.clearFilters", "Clear filters")}
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

/**
 * Toolbar component for users card list
 * Handles search, filter, sort and create actions
 */
export function UsersCardListToolbar({
  keyword,
  onSearchChange,
  onSearch,
  onClear,
  status,
  role,
  sortBy,
  desc,
  roles = [],
  onFilter,
  onSort,
  isSelectionMode = false,
  onSelectionModeToggle,
  selectedCount = 0,
  onDeleteSelected,
  onSelectAll,
  onDeselectAll,
  totalCount = 0,
}) {
  const { t } = useTranslation();
  const isMobile = useIsMobile();
  const [showFilterDialog, setShowFilterDialog] = React.useState(false);
  const [showSortPopover, setShowSortPopover] = React.useState(false);
  const [localKeyword, setLocalKeyword] = React.useState(keyword || '');
  const [localStatus, setLocalStatus] = React.useState(() => {
    if (!status) return [];
    return Array.isArray(status) ? status : [status];
  });
  const [localRole, setLocalRole] = React.useState(() => {
    if (!role) return [];
    return Array.isArray(role) ? role : [role];
  });
  const [showStatusCommand, setShowStatusCommand] = React.useState(false);
  const [showRoleCommand, setShowRoleCommand] = React.useState(false);

  // Sync local keyword with props
  React.useEffect(() => {
    setLocalKeyword(keyword || '');
  }, [keyword]);

  React.useEffect(() => {
    if (showFilterDialog) {
      setLocalStatus(() => {
        if (!status) return [];
        return Array.isArray(status) ? status : [status];
      });
      setLocalRole(() => {
        if (!role) return [];
        return Array.isArray(role) ? role : [role];
      });
    }
  }, [showFilterDialog, status, role]);


  const handleSearch = () => {
    onSearch(localKeyword.trim());
  };

  const handleClear = () => {
    setLocalKeyword('');
    onClear();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleStatusChange = (value) => {
    // Toggle selection
    setLocalStatus((prev) => {
      if (prev.includes(value)) {
        return prev.filter((v) => v !== value);
      } else {
        return [...prev, value];
      }
    });
  };

  const handleRoleChange = (value) => {
    // Toggle selection
    setLocalRole((prev) => {
      if (prev.includes(value)) {
        return prev.filter((v) => v !== value);
      } else {
        return [...prev, value];
      }
    });
  };

  const handleFilterApply = () => {
    onFilter?.({
      status: localStatus.length > 0 ? localStatus : null,
      role: localRole.length > 0 ? localRole : null,
    });
    setShowFilterDialog(false);
  };

  const handleFilterClear = () => {
    setLocalStatus([]);
    setLocalRole([]);
    onFilter?.({
      status: null,
      role: null,
    });
    setShowFilterDialog(false);
  };

  const getStatusLabel = (value) => {
    if (value === "true") {
      return t("pages.usersManagement.fields.status.values.active", "Active");
    }
    if (value === "false") {
      return t("pages.usersManagement.fields.status.values.inactive", "Inactive");
    }
    return value;
  };

  const getRoleLabel = (value) => {
    return value;
  };

  const statusOptions = [
    { value: "true", label: t("pages.usersManagement.fields.status.values.active", "Active") },
    { value: "false", label: t("pages.usersManagement.fields.status.values.inactive", "Inactive") },
  ];

  const roleOptions = roles.map((roleItem) => ({
    value: roleItem.name || roleItem,
    label: roleItem.name || roleItem,
  }));

  const removeStatusBadge = (value) => {
    setLocalStatus((prev) => prev.filter((v) => v !== value));
  };

  const removeRoleBadge = (value) => {
    setLocalRole((prev) => prev.filter((v) => v !== value));
  };

  const handleSortByChange = (field) => {
    // Only trigger if the field actually changed
    if (sortBy === field) {
      return;
    }
    onSort?.({
      sort_by: field,
      desc: desc || false,
    });
  };

  const handleSortDescChange = (newDesc) => {
    // Only trigger if the direction actually changed
    if (desc === newDesc) {
      return;
    }
    onSort?.({
      sort_by: sortBy,
      desc: newDesc,
    });
  };

  const getSortFieldLabel = () => {
    if (!sortBy) {
      return t("common.actions.sort", "Sort");
    }
    const option = sortOptions.find((opt) => opt.value === sortBy);
    return option ? option.label : t("common.actions.sort", "Sort");
  };

  const getSortDirectionLabel = () => {
    return desc
      ? t("common.descending", "Descending")
      : t("common.ascending", "Ascending");
  };

  const getTooltipText = () => {
    if (!sortBy) {
      return t("common.actions.sort", "Sort");
    }
    return `${getSortFieldLabel()} · ${getSortDirectionLabel()}`;
  };

  const sortOptions = [
    { value: "first_name", label: t("pages.usersManagement.fields.firstName.label", "First Name") },
    { value: "last_name", label: t("pages.usersManagement.fields.lastName.label", "Last Name") },
    { value: "email", label: t("pages.usersManagement.fields.email.label", "Email") },
    { value: "phone", label: t("pages.usersManagement.fields.phone.label", "Phone") },
    { value: "role", label: t("pages.usersManagement.fields.role.label", "Role") },
    { value: "status", label: t("pages.usersManagement.fields.status.label", "Status") },
    { value: "created_at", label: t("pages.usersManagement.fields.createdAt.label", "Created At") },
  ];

  const hasActiveFilter = (status && (Array.isArray(status) ? status.length > 0 : status !== null)) || 
                          (role && (Array.isArray(role) ? role.length > 0 : role !== null));
  const hasActiveSort = sortBy;

  return (
    <>
      <div className="flex items-center gap-2 px-6">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <Input
            id="users-card-list-toolbar-search"
            name="users-card-list-toolbar-search"
            type="text"
            placeholder={t("components.dataGrid.toolbar.searchPlaceholder", "Search users...")}
            value={localKeyword}
            onChange={(e) => setLocalKeyword(e.target.value)}
            onKeyDown={handleKeyDown}
            className="pl-9 pr-9"
          />
          {localKeyword && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7"
              onClick={handleClear}
            >
              <X className="size-4" />
              <span className="sr-only">{t("common.actions.clear", "Clear")}</span>
            </Button>
          )}
        </div>
        <Button
          variant="secondary"
          size="icon"
          onClick={handleSearch}
          className="shrink-0"
        >
          <Search className="size-5" />
          <span className="sr-only">{t("common.actions.search", "Search")}</span>
        </Button>
        <Button
          variant="secondary"
          size="icon"
          onClick={() => setShowFilterDialog(true)}
          className={cn("shrink-0")}
        >
          <Filter className="size-5" />
          <span className="sr-only">{t("common.actions.filter", "Filter")}</span>
        </Button>
        <Popover open={showSortPopover} onOpenChange={setShowSortPopover}>
          <Tooltip>
            <TooltipTrigger asChild>
              <PopoverTrigger asChild>
                <Button
                  variant="secondary"
                  size="icon"
                  className={cn("shrink-0")}
                >
                  {hasActiveSort ? (
                    desc ? (
                      <ArrowDownNarrowWide className="size-5" />
                    ) : (
                      <ArrowUpWideNarrow className="size-5" />
                    )
                  ) : (
                    <ArrowUpDown className="size-5" />
                  )}
                  <span className="sr-only">{t("common.actions.sort", "Sort")}</span>
                </Button>
              </PopoverTrigger>
            </TooltipTrigger>
            <TooltipContent sideOffset={6}>
              <p>{getTooltipText()}</p>
            </TooltipContent>
          </Tooltip>
          <PopoverContent className="w-56 p-2" align="end">
            <div className="space-y-2">
              {/* Sort Field */}
              <div className="px-2 pt-1 text-xs font-semibold text-muted-foreground user-select-none">
                {t("common.actions.sortBy", "Sort By")}
              </div>
              <div className="space-y-1">
                {sortOptions.map((option) => {
                  const isActive = sortBy === option.value;
                  return (
                    <Button
                      key={option.value}
                      variant="ghost"
                      onClick={() => handleSortByChange(option.value)}
                      className={cn(
                        "w-full h-9 flex items-center justify-between px-2 text-sm rounded-xs font-normal",
                        isActive && "bg-accent font-medium"
                      )}
                    >
                      <span>{option.label}</span>
                      {isActive && <Check className="h-4 w-4" />}
                    </Button>
                  );
                })}
              </div>

              <Separator className="my-2" />

              {/* Sort Direction */}
              <div className="px-2 pt-1 text-xs font-semibold text-muted-foreground user-select-none">
                {t("common.actions.sortOrder", "Sort Order")}
              </div>
              <div className="space-y-1">
                <Button
                  variant="ghost"
                  onClick={() => handleSortDescChange(false)}
                  disabled={!sortBy}
                  className={cn(
                    "w-full h-9 flex items-center justify-between px-2 text-sm rounded-xs font-normal",
                    !desc && sortBy && "bg-accent font-medium",
                    !sortBy && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <span>{t("common.actions.ascending", "Ascending")}</span>
                  {!desc && sortBy && <Check className="h-4 w-4" />}
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => handleSortDescChange(true)}
                  disabled={!sortBy}
                  className={cn(
                    "w-full h-9 flex items-center justify-between px-2 text-sm rounded-xs font-normal",
                    desc && sortBy && "bg-accent font-medium",
                    !sortBy && "opacity-50 cursor-not-allowed"
                  )}
                >
                  <span>{t("common.actions.descending", "Descending")}</span>
                  {desc && sortBy && <Check className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </PopoverContent>
        </Popover>
      </div>

      {/* Action Bar for selection */}
      {isSelectionMode && (
        <ActionBar 
          open={true} 
          onOpenChange={(open) => {
            if (!open) {
              onSelectionModeToggle?.();
            }
          }}
          className="w-auto max-w-xs"
        >
          <ActionBarSelection>
            <span className="text-sm font-medium whitespace-nowrap">{selectedCount} {t("common.selected", "selected")}</span>
          </ActionBarSelection>
          <ActionBarGroup>
            {selectedCount < totalCount ? (
              <ActionBarItem
                onSelect={(e) => {
                  e.preventDefault();
                  onSelectAll?.();
                }}
                className="size-10 p-0 flex items-center justify-center"
              >
                <CheckCheck className="size-5" />
                <span className="sr-only">{t("common.actions.selectAll", "Select All")}</span>
              </ActionBarItem>
            ) : (
              <ActionBarItem
                onSelect={(e) => {
                  e.preventDefault();
                  onDeselectAll?.();
                }}
                className="size-10 p-0 flex items-center justify-center bg-secondary text-secondary-foreground border-secondary border hover:bg-secondary/90"
              >
                <CheckCheck className="size-5" />
                <span className="sr-only">{t("common.actions.deselectAll", "Deselect All")}</span>
              </ActionBarItem>
            )}
            <ActionBarItem
              onSelect={(e) => {
                e.preventDefault();
                if (selectedCount > 0) {
                  onDeleteSelected?.();
                }
              }}
              disabled={selectedCount === 0}
              className={cn(
                "size-10 p-0 flex items-center justify-center",
                selectedCount > 0
                  ? "text-destructive-foreground bg-destructive hover:text-destructive hover:bg-destructive/10"
                  : "opacity-50 cursor-not-allowed"
              )}
            >
              <Trash2 className="size-5" />
              <span className="sr-only">{t("common.actions.delete", "Delete")}</span>
            </ActionBarItem>
            <ActionBarClose
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onSelectionModeToggle?.();
              }}
              className="size-10 p-0 flex items-center justify-center"
            >
              <X className="size-5" />
              <span className="sr-only">{t("common.actions.cancel", "Cancel")}</span>
            </ActionBarClose>
          </ActionBarGroup>
        </ActionBar>
      )}

      {/* Filter Dialog */}
      <Dialog open={showFilterDialog} onOpenChange={setShowFilterDialog}>
        <DialogContent className="max-w-md" showCloseButton={false}>
          <DialogHeader>
            <DialogTitle>{t("common.actions.filter", "Filter")}</DialogTitle>
            <DialogDescription>
              {t("pages.usersManagement.dialog.filterDescription", "Please set filter options")}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            {/* Status Field */}
            <div className="space-y-2">
              <div className="text-sm font-medium">
                {t("pages.usersManagement.fields.status.label", "Status")}
              </div>
              <FilterFieldPopover
                label={t("pages.usersManagement.fields.status.label", "Status")}
                selectedValues={localStatus}
                options={statusOptions}
                onValueChange={handleStatusChange}
                onRemoveValue={removeStatusBadge}
                onClearAll={() => setLocalStatus([])}
                getValueLabel={getStatusLabel}
                open={showStatusCommand}
                onOpenChange={setShowStatusCommand}
              />
            </div>

            {/* Role Field */}
            <div className="space-y-2">
              <div className="text-sm font-medium">
                {t("pages.usersManagement.fields.role.label", "Role")}
              </div>
              <FilterFieldPopover
                label={t("pages.usersManagement.fields.role.label", "Role")}
                selectedValues={localRole}
                options={roleOptions}
                onValueChange={handleRoleChange}
                onRemoveValue={removeRoleBadge}
                onClearAll={() => setLocalRole([])}
                getValueLabel={getRoleLabel}
                open={showRoleCommand}
                onOpenChange={setShowRoleCommand}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={handleFilterClear}
              disabled={!hasActiveFilter}
            >
              {t("common.actions.clear", "Clear")}
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowFilterDialog(false)}
            >
              {t("common.actions.cancel", "Cancel")}
            </Button>
            <Button
              variant="default"
              onClick={handleFilterApply}
            >
              {t("common.actions.apply", "Apply")}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

    </>
  );
}