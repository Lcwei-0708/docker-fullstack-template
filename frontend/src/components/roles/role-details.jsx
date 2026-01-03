import * as React from "react"
import { cn } from "@/lib/utils"
import { useTranslation } from "react-i18next"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Spinner } from "@/components/ui/spinner"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Scroller } from "@/components/ui/scroller"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { AlertDialog, AlertDialogTrigger } from "@/components/ui/alert-dialog"
import { DeleteRoleDialog } from "@/components/roles/delete-role-dialog"
import { RoleFormDialog } from "@/components/roles/role-form-dialog"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Edit, Trash2, Shield, CheckCircle2, Circle, ChevronRight } from "lucide-react"

const toCamelKey = (input) => {
  if (!input || typeof input !== "string") return "";
  const parts = input.split(/[-_\s]+/).filter(Boolean);
  if (parts.length === 0) return "";
  return parts
    .map((p, idx) => {
      const s = String(p);
      if (idx === 0) return s.charAt(0).toLowerCase() + s.slice(1);
      return s.charAt(0).toUpperCase() + s.slice(1);
    })
    .join("");
};

const normalizeGroupsForDisplay = (groups, attributesFlat = {}) => {
  if (!Array.isArray(groups)) return [];

  return groups
    .filter((g) => !!g && typeof g === "object")
    .map((g) => {
      const groupName = g.group || "default";
      const categoriesObj = g.categories && typeof g.categories === "object" ? g.categories : {};
      const categories = Object.entries(categoriesObj).map(([categoryName, list]) => {
        const attrs = (Array.isArray(list) ? list : [])
          .filter((a) => a?.name)
          .map((a) => ({
            name: a.name,
            value: typeof attributesFlat?.[a.name] === "boolean" ? attributesFlat[a.name] : !!a.value,
          }));

        return { name: categoryName, attributes: attrs };
      });

      return {
        group: groupName,
        categories,
      };
    });
};

const normalizeLegacyAttributesForDisplay = (attributesFlat = {}) => {
  return Object.entries(attributesFlat).map(([name, value]) => ({ name, value: !!value }));
};

export function RoleDetails({
  selectedRole,
  isEditingRole = false,
  editedRoleData = {
    name: "",
    description: "",
  },
  attributes = {},
  attributeGroups = [],
  isLoadingAttributes = false,
  hasChanges = false,
  isSubmitting = false,
  canManageRoles = false,
  onDeleteClick,
  onRoleDataChange,
  onAttributeToggle,
  onSaveRole,
  onSaveRoleFromDialog,
  onSaveAttributes,
  onResetAttributes,
  onCancelEdit,
}) {
  const { t } = useTranslation();
  const [isEditDialogOpen, setIsEditDialogOpen] = React.useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = React.useState(false);
  const [isEditTooltipOpen, setIsEditTooltipOpen] = React.useState(false);
  const [openGroups, setOpenGroups] = React.useState({});

  // Build grouped permissions for the UI.
  const organizedGroups = React.useMemo(() => {
    if (Array.isArray(attributeGroups) && attributeGroups.length > 0) {
      return normalizeGroupsForDisplay(attributeGroups, attributes);
    }
    return [];
  }, [attributeGroups, attributes]);

  // Fallback: show flat permissions when grouped data is missing.
  const legacyAttributes = React.useMemo(() => {
    if (organizedGroups.length > 0) return [];
    if (Object.keys(attributes).length === 0) return [];
    return normalizeLegacyAttributesForDisplay(attributes);
  }, [attributes, organizedGroups.length]);

  const hasPermissionsData = organizedGroups.length > 0 || legacyAttributes.length > 0;

  // Open all groups by default, but keep the user's open/close state.
  React.useEffect(() => {
    if (organizedGroups.length === 0) return;
    setOpenGroups((prev) => {
      const next = { ...(prev || {}) };
      organizedGroups.forEach((g) => {
        if (typeof next[g.group] !== "boolean") next[g.group] = true;
      });
      return next;
    });
  }, [organizedGroups]);
  // Open the role form dialog when user enters create mode.
  React.useEffect(() => {
    if (!canManageRoles) return;

    if (isEditingRole) {
      setIsEditDialogOpen(true);
    }
  }, [isEditingRole, selectedRole, canManageRoles]);
  // Close dialogs when switching roles.
  React.useEffect(() => {
    setIsDeleteDialogOpen(false);
  }, [selectedRole?.id]);
  React.useEffect(() => {
    setIsEditTooltipOpen(false);
  }, [selectedRole?.id]);
  const getGroupLabel = (name) => {
    const key = toCamelKey(name);
    return t(`pages.rolesManagement.groups.${key}`, name);
  };
  const getCategoryLabel = (name) => {
    const key = toCamelKey(name);
    return t(`pages.rolesManagement.categories.${key}`, name);
  };
  const getAttributeLabel = (name) => {
    const key = toCamelKey(name);
    return t(`pages.rolesManagement.attributes.${key}`, name);
  };
  const getGroupAttributeNames = React.useCallback((groupObj) => {
    return (groupObj?.categories || [])
      .flatMap((cat) => (cat?.attributes || []).map((a) => a?.name).filter(Boolean))
      .filter(Boolean);
  }, []);
  // Toggle all permissions in a group.
  const handleSelectAllGroup = React.useCallback(
    (groupObj) => {
      const allAttrNames = getGroupAttributeNames(groupObj);
      const allSelected = allAttrNames.length > 0 && allAttrNames.every((name) => !!attributes?.[name]);
      allAttrNames.forEach((name) => {
        if (allSelected) {
          if (attributes?.[name]) onAttributeToggle?.(name);
        } else {
          if (!attributes?.[name]) onAttributeToggle?.(name);
        }
      });
    },
    [attributes, onAttributeToggle, getGroupAttributeNames]
  );
  const isGroupAllSelected = React.useCallback(
    (groupObj) => {
      const allAttrNames = getGroupAttributeNames(groupObj);
      if (allAttrNames.length === 0) return false;
      return allAttrNames.every((name) => !!attributes?.[name]);
    },
    [attributes, getGroupAttributeNames]
  );
  const handleSelectAllLegacy = React.useCallback(() => {
    const names = legacyAttributes.map((a) => a.name);
    const allSelected = names.length > 0 && names.every((n) => !!attributes?.[n]);
    names.forEach((n) => {
      if (allSelected) {
        if (attributes?.[n]) onAttributeToggle?.(n);
      } else {
        if (!attributes?.[n]) onAttributeToggle?.(n);
      }
    });
  }, [legacyAttributes, attributes, onAttributeToggle]);
  // Submit role form (create/edit).
  const handleRoleFormSubmit = React.useCallback(
    async (data) => {
      if (!data?.name?.trim()) return;

      // Save via parent handler when available.
      if (onSaveRoleFromDialog) {
        const targetRoleId = isEditingRole ? null : (selectedRole?.id || null);
        const ok = await onSaveRoleFromDialog(targetRoleId, data);
        setIsEditDialogOpen(false);
        if (ok === false && isEditingRole) {
          onCancelEdit?.();
        }
        return;
      }
      // Fallback: update state then call legacy save.
      onRoleDataChange?.(data);
      setTimeout(() => {
        onSaveRole?.();
      }, 0);
      setIsEditDialogOpen(false);
    },
    [isEditingRole, selectedRole, onRoleDataChange, onSaveRole, onSaveRoleFromDialog, onCancelEdit]
  );
  // Cancel role form.
  const handleRoleFormCancel = React.useCallback(() => {
    if (isEditingRole) {
      onCancelEdit?.();
    }
    setIsEditDialogOpen(false);
  }, [isEditingRole, onCancelEdit]);
  // Open edit dialog.
  const handleEditButtonClick = React.useCallback(() => {
    setIsEditTooltipOpen(false);
    setIsEditDialogOpen(true);
  }, []);
  return (
    <>
      <Card className="flex-1 flex flex-col py-0 gap-0">
        <CardHeader className="border-b !p-5 flex items-center justify-between">
          <div className="flex flex-1 items-center justify-between">
            <div className="flex-1 min-w-0">
              {" "}
              {selectedRole ? (
                <>
                  <CardTitle className="mb-2"> {selectedRole.name} </CardTitle>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {selectedRole.description || t("pages.rolesManagement.noDescription", "No description")}
                  </p>
                </>
              ) : (
                <CardTitle>
                  {isEditingRole
                    ? t("pages.rolesManagement.dialog.createTitle", "Create role")
                    : t("pages.rolesManagement.selectRole", "Select a role")}
                </CardTitle>
              )}{" "}
            </div>
            {selectedRole && canManageRoles && !isEditingRole && (
              <div className="flex items-center gap-2 flex-shrink-0">
                <Tooltip
                  open={isEditTooltipOpen}
                  onOpenChange={setIsEditTooltipOpen}
                  disableHoverableContent={false}
                >
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      onPointerDown={() => setIsEditTooltipOpen(false)}
                      onClick={() => {
                        setIsEditTooltipOpen(false);
                        handleEditButtonClick();
                      }}
                      aria-label={t("common.actions.edit", "Edit")}
                    >
                      <Edit className="size-4.5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent sideOffset={3}>
                    <p>{t("common.actions.edit", "Edit")}</p>
                  </TooltipContent>
                </Tooltip>
                <AlertDialog
                  open={isDeleteDialogOpen}
                  onOpenChange={(next) => {
                    setIsDeleteDialogOpen(next);
                  }}
                >
                  <Tooltip disableHoverableContent={false}>
                    <TooltipTrigger asChild>
                      <span
                        className="inline-flex"
                      >
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            disabled={isSubmitting}
                            aria-label={t("common.actions.delete", "Delete")}
                          >
                            <Trash2 className="size-4.5" />
                          </Button>
                        </AlertDialogTrigger>
                      </span>
                    </TooltipTrigger>
                    <TooltipContent sideOffset={3}>
                      <p>{t("common.actions.delete", "Delete")}</p>
                    </TooltipContent>
                  </Tooltip>
                  <DeleteRoleDialog
                    roleName={selectedRole?.name || ""}
                    isSubmitting={isSubmitting}
                    onConfirm={onDeleteClick}
                  />
                </AlertDialog>
              </div>
            )}{" "}
          </div>
        </CardHeader>
        <CardContent className="flex-1 p-0">
          <Scroller
            hideScrollbar={false}
            className="h-full max-h-[calc(100dvh-290px)]"
            style={{
              paddingLeft: 20,
              paddingRight: 20,
            }}
          >
            {selectedRole || isEditingRole ? (
              <div className="flex flex-col py-5">
                {selectedRole && (
                  <>
                    {isLoadingAttributes && !hasPermissionsData ? (
                      <div className="flex items-center justify-center py-12">
                        <Spinner className="size-6" />
                      </div>
                    ) : organizedGroups.length === 0 && legacyAttributes.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-12 text-center">
                        <Shield className="size-12 text-muted-foreground mb-4" />
                        <p className="text-muted-foreground"> {t("pages.rolesManagement.dialog.noAttributes", "No available permissions")} </p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {organizedGroups.length > 0 &&
                          organizedGroups.map((g) => {
                            const groupAttrNames = getGroupAttributeNames(g);
                            const groupTotal = groupAttrNames.length;
                            const groupSelectedCount = groupAttrNames.reduce((acc, name) => acc + (attributes?.[name] ? 1 : 0), 0);
                            const groupCheckedState =
                              groupTotal > 0 && groupSelectedCount === groupTotal
                                ? true
                                : groupTotal > 0 && groupSelectedCount > 0
                                  ? "indeterminate"
                                  : false;
                            const groupCheckboxId = `role-perms-${selectedRole?.id ?? "new"}-${toCamelKey(g.group) || "group"}`;
                            const groupAllSelected = isGroupAllSelected(g);
                            const isOpen = openGroups?.[g.group] ?? true;
                            return (
                              <Collapsible
                                key={g.group}
                                open={isOpen}
                                onOpenChange={(nextOpen) => {
                                  setOpenGroups((prev) => ({ ...(prev || {}), [g.group]: nextOpen }));
                                }}
                                className="border rounded-lg overflow-hidden bg-card"
                              >
                                <CollapsibleTrigger asChild>
                                  <div className="flex items-center justify-between gap-3 px-4 py-2.5 bg-muted/30 data-[state=open]:border-b cursor-pointer select-none">
                                    <div className="flex items-center gap-2">
                                      <h4 className="text-sm font-semibold text-foreground truncate">{getGroupLabel(g.group)}</h4>
                                      <ChevronRight className={cn("size-4 transition-transform", isOpen && "rotate-90")} />
                                    </div>
                                    {groupTotal > 0 && (
                                      <label
                                        className={cn(
                                          "flex items-center gap-2 rounded-sm px-2 py-1.5 select-none",
                                          canManageRoles && !isSubmitting ? "cursor-pointer hover:bg-accent" : "cursor-default"
                                        )}
                                        htmlFor={groupCheckboxId}
                                        onClick={(e) => e.stopPropagation()}
                                        onKeyDown={(e) => e.stopPropagation()}
                                      >
                                        {canManageRoles && (
                                          <>
                                            <span className="sr-only">
                                              {groupAllSelected
                                                ? t("pages.rolesManagement.actions.deselectAll", "Deselect all")
                                                : t("pages.rolesManagement.actions.selectAll", "Select all")}
                                            </span>
                                            <Checkbox
                                              id={groupCheckboxId}
                                              className="rounded-2xs"
                                              checked={groupCheckedState}
                                              disabled={isSubmitting}
                                              aria-label={
                                                groupAllSelected
                                                  ? t("pages.rolesManagement.actions.deselectAll", "Deselect all")
                                                  : t("pages.rolesManagement.actions.selectAll", "Select all")
                                              }
                                              onCheckedChange={() => handleSelectAllGroup(g)}
                                            />
                                          </>
                                        )}
                                        <span className="text-sm text-muted-foreground tabular-nums font-medium">
                                          {groupSelectedCount}/{groupTotal}
                                        </span>
                                      </label>
                                    )}
                                  </div>
                                </CollapsibleTrigger>

                                <CollapsibleContent>
                                  <div className="divide-y divide-border bg-popover">
                                    {g.categories.map((cat) => {
                                      return (
                                        <div key={cat.name} className="flex items-center justify-between gap-4 px-4 py-4">
                                          <div className="text-sm font-semibold text-foreground truncate">
                                            {getCategoryLabel(cat.name)}
                                          </div>
                                          <div className="flex flex-wrap items-center justify-end gap-2">
                                            {cat.attributes.map((attr) => {
                                              const isEnabled = !!attributes?.[attr.name];
                                              return (
                                                <Button
                                                  key={attr.name}
                                                  variant="outline"
                                                  onClick={() => onAttributeToggle?.(attr.name)}
                                                  disabled={!canManageRoles || isSubmitting}
                                                  aria-pressed={isEnabled}
                                                  className={cn(
                                                    "inline-flex items-center justify-center gap-2 rounded-md px-3 h-9 text-sm font-normal",
                                                    "border",
                                                    isEnabled
                                                      ? "bg-primary/10 border-primary/50 text-primary hover:text-primary hover:border-primary/75 hover:bg-primary/15"
                                                      : "bg-background border-border text-muted-foreground",
                                                    (!canManageRoles || isSubmitting) && "pointer-events-none opacity-60"
                                                  )}
                                                >
                                                  {isEnabled ? <CheckCircle2 className="size-4" /> : <Circle className="size-4 text-muted-foreground" />}
                                                  <span className="truncate">{getAttributeLabel(attr.name)}</span>
                                                </Button>
                                              );
                                            })}
                                          </div>
                                        </div>
                                      );
                                    })}
                                  </div>
                                </CollapsibleContent>
                              </Collapsible>
                            );
                          })}

                        {/* Legacy UI fallback */}
                        {organizedGroups.length === 0 &&
                          legacyAttributes.length > 0 && (() => {
                            const allSelected = legacyAttributes.every((a) => !!attributes?.[a.name]);
                            const total = legacyAttributes.length;
                            const selectedCount = legacyAttributes.reduce((acc, a) => acc + (attributes?.[a.name] ? 1 : 0), 0);
                            const checkedState =
                              total > 0 && selectedCount === total ? true : total > 0 && selectedCount > 0 ? "indeterminate" : false;
                            const legacyCheckboxId = `role-perms-${selectedRole?.id ?? "new"}-legacy`;
                            return (
                              <div key="legacy-attributes" className="border rounded-lg overflow-hidden bg-card">
                                <div className="flex items-center justify-between p-4 bg-muted/50 border-b">
                                  <div className="flex items-center gap-3">
                                    <Shield className="size-5 text-primary" />
                                    <h4 className="text-lg font-semibold text-primary">{t("pages.rolesManagement.categories.other", "其他")}</h4>
                                  </div>
                                  {total > 0 && (
                                    <label
                                      className={cn(
                                        "flex items-center gap-2 rounded-md px-1 py-1 select-none",
                                        canManageRoles && !isSubmitting ? "cursor-pointer hover:bg-accent/40" : "cursor-default"
                                      )}
                                      htmlFor={legacyCheckboxId}
                                    >
                                      {canManageRoles && (
                                        <>
                                          <span className="sr-only">
                                            {allSelected
                                              ? t("pages.rolesManagement.actions.deselectAll", "Deselect all")
                                              : t("pages.rolesManagement.actions.selectAll", "Select all")}
                                          </span>
                                          <Checkbox
                                            id={legacyCheckboxId}
                                            className="rounded-2xs"
                                            checked={checkedState}
                                            disabled={isSubmitting}
                                            aria-label={
                                              allSelected
                                                ? t("pages.rolesManagement.actions.deselectAll", "Deselect all")
                                                : t("pages.rolesManagement.actions.selectAll", "Select all")
                                            }
                                            onCheckedChange={handleSelectAllLegacy}
                                          />
                                        </>
                                      )}
                                      <span className="text-sm text-muted-foreground tabular-nums">
                                        {selectedCount}/{total}
                                      </span>
                                    </label>
                                  )}
                                </div>

                                <div className="p-4">
                                  <div className="flex flex-wrap items-center gap-2">
                                    {legacyAttributes.map((attr) => {
                                      const isEnabled = !!attributes?.[attr.name];
                                      return (
                                        <Button
                                          key={attr.name}
                                          variant="outline"
                                          onClick={() => onAttributeToggle?.(attr.name)}
                                          disabled={!canManageRoles || isSubmitting}
                                          aria-pressed={isEnabled}
                                          className={cn(
                                            "inline-flex items-center justify-center gap-2 rounded-full px-3 py-2 min-h-9 text-sm font-medium",
                                            "border",
                                            isEnabled
                                              ? "bg-primary/10 border-primary/50 text-primary hover:text-primary hover:border-primary/50 hover:bg-primary/10"
                                              : "bg-background border-border text-muted-foreground hover:text-foreground hover:bg-accent/40",
                                            (!canManageRoles || isSubmitting) && "pointer-events-none opacity-60"
                                          )}
                                        >
                                          {isEnabled ? <CheckCircle2 className="size-4 mt-0.5" /> : <Circle className="size-4 opacity-60 mt-0.5" />}
                                          <span className="truncate">{getAttributeLabel(attr.name)}</span>
                                        </Button>
                                      );
                                    })}
                                  </div>
                                </div>
                              </div>
                            );
                          })()}
                      </div>
                    )}
                    {hasChanges && canManageRoles && (
                      <div className="mt-4 rounded-lg border border-primary/20 bg-primary/5 py-4 px-4">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <span className="text-sm text-primary font-medium truncate">
                            {t("pages.rolesManagement.dialog.hasChanges", "Unsaved changes")}
                          </span>
                          <div className="flex items-center gap-2 sm:shrink-0">
                            <Button variant="outline" onClick={onResetAttributes} disabled={isSubmitting}>
                              {t("common.actions.cancel", "Cancel")}
                            </Button>
                            <Button onClick={onSaveAttributes} disabled={isSubmitting} className="bg-primary hover:bg-primary/90">
                              {isSubmitting ? (
                                <span className="inline-flex items-center gap-2">
                                  <Spinner className="size-4" />
                                </span>
                              ) : (
                                <>{t("common.actions.save", "Save")}</>
                              )}
                            </Button>
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            ) : (
              <div className="flex items-center justify-center min-h-[400px]">
                <div className="text-center">
                  <Shield className="size-16 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground"> {t("pages.rolesManagement.selectRoleFromLeft", "Select a role from the left")} </p>
                </div>
              </div>
            )}
          </Scroller>
        </CardContent>
      </Card>
      <RoleFormDialog
        open={isEditDialogOpen}
        mode={isEditingRole ? "create" : selectedRole ? "edit" : "create"}
        isSubmitting={isSubmitting}
        onOpenChange={setIsEditDialogOpen}
        initialData={
          isEditingRole
            ? {
              name: editedRoleData?.name || "",
              description: editedRoleData?.description || "",
            }
            : selectedRole
              ? {
                name: selectedRole?.name || "",
                description: selectedRole?.description || "",
              }
              : {
                name: editedRoleData?.name || "",
                description: editedRoleData?.description || "",
              }
        }
        onCancel={handleRoleFormCancel}
        onSubmit={handleRoleFormSubmit}
      />
    </>
  );
}

export default RoleDetails;