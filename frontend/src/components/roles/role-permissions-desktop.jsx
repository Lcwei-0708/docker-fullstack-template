import * as React from "react"
import { cn } from "@/lib/utils"
import { useTranslation } from "react-i18next"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Spinner } from "@/components/ui/spinner"
import { Skeleton } from "@/components/ui/skeleton"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Scroller } from "@/components/ui/scroller"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Shield, CheckCircle2, Circle, ChevronRight } from "lucide-react"

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

export function RolePermissionsDesktop({
  selectedRole,
  attributes = {},
  attributeGroups = [],
  isLoadingAttributes = false,
  isLoadingRoles = false,
  hasChanges = false,
  isSubmitting = false,
  canManageRoles = false,
  onAttributeToggle,
  onSaveAttributes,
  onResetAttributes,
}) {
  const { t } = useTranslation();
  const [openGroups, setOpenGroups] = React.useState({});
  const [delayedLoadingAttrs, setDelayedLoadingAttrs] = React.useState(false);
  const detailsScrollerRef = React.useRef(null);
  const [scrollbarWidth, setScrollbarWidth] = React.useState(0);

  const rawIsLoadingAttrs = !!isLoadingAttributes;
  const loadingDelayMs = 100;

  // Delay showing the attributes spinner to avoid flash on quick responses
  React.useEffect(() => {
    if (!rawIsLoadingAttrs) {
      setDelayedLoadingAttrs(false);
      return undefined;
    }

    if (!loadingDelayMs || loadingDelayMs <= 0) {
      setDelayedLoadingAttrs(true);
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setDelayedLoadingAttrs(true);
    }, loadingDelayMs);

    return () => {
      window.clearTimeout(timer);
    };
  }, [rawIsLoadingAttrs, loadingDelayMs]);

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
  const showEmptyState = !rawIsLoadingAttrs && !hasPermissionsData;
  // Only show skeleton after the delay to avoid flicker on very fast loads
  const showSkeletonView = rawIsLoadingAttrs && delayedLoadingAttrs;

  const recomputeScrollbar = React.useCallback(() => {
    const el = detailsScrollerRef.current;
    if (!el) return;
    const width = Math.max(0, el.offsetWidth - el.clientWidth);
    setScrollbarWidth(width);
  }, []);

  React.useLayoutEffect(() => {
    // Recompute after layout.
    const raf = window.requestAnimationFrame(recomputeScrollbar);
    return () => window.cancelAnimationFrame(raf);
  }, [
    recomputeScrollbar,
    selectedRole?.id,
    showEmptyState,
    showSkeletonView,
    organizedGroups.length,
    legacyAttributes.length,
    openGroups,
  ]);

  React.useEffect(() => {
    window.addEventListener("resize", recomputeScrollbar);
    return () => window.removeEventListener("resize", recomputeScrollbar);
  }, [recomputeScrollbar]);

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

  const baseXPaddingPx = 20;
  const scrollerPaddingRightPx = Math.max(0, baseXPaddingPx - scrollbarWidth - 2);
  const roleTitle = selectedRole?.name || t("pages.rolesManagement.selectRoleFromLeft", "Select a role from the left");

  return (
    <>
      <Card className="flex-1 flex flex-col py-0 gap-0">
        <CardHeader className="border-b px-5 !py-4 h-20 flex items-center justify-between gap-3">
          <CardTitle className="text-base font-semibold leading-none tracking-tight">
            {selectedRole
              ? t("pages.rolesManagement.rolePermissionsFor", "Permissions for {{role}}", { role: roleTitle })
              : t("pages.rolesManagement.selectRoleFromLeft", "Select a role from the left")}
          </CardTitle>
          {hasChanges && canManageRoles && (
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                disabled={isSubmitting}
                onClick={onResetAttributes}
              >
                {t("common.actions.cancel", "Cancel")}
              </Button>
              <Button
                className="bg-primary text-primary-foreground hover:bg-primary/90"
                disabled={isSubmitting}
                onClick={onSaveAttributes}
              >
                {isSubmitting ? <Spinner className="size-4" /> : t("common.actions.save", "Save")}
              </Button>
            </div>
          )}
        </CardHeader>
        <CardContent className="flex flex-col flex-1 p-0 px-0.5 overflow-hidden">
          <Scroller
            ref={detailsScrollerRef}
            hideScrollbar="hover"
            className="h-full max-h-[calc(100dvh-190px)]"
            style={{
              paddingLeft: baseXPaddingPx,
              paddingRight: scrollerPaddingRightPx,
              scrollbarGutter: "stable",
            }}
          >
            {selectedRole ? (
              <div className="flex flex-col pt-5 pb-5">
                {selectedRole && (
                  <div className="relative">
                    {showEmptyState ? (
                      <div className="flex flex-col items-center justify-center py-12 text-center">
                        <Shield className="size-12 text-muted-foreground mb-4" />
                        <p className="text-muted-foreground"> {t("pages.rolesManagement.dialog.noAttributes", "No available permissions")} </p>
                      </div>
                    ) : (
                      <>
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
                                            canManageRoles && !isSubmitting && !showSkeletonView ? "cursor-pointer hover:bg-accent" : "cursor-default"
                                          )}
                                          htmlFor={groupCheckboxId}
                                          onClick={(e) => e.stopPropagation()}
                                          onKeyDown={(e) => e.stopPropagation()}
                                        >
                                          {showSkeletonView ? (
                                            <Skeleton className="h-5 w-12 rounded-2xs" />
                                          ) : (
                                            <>
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
                                            </>
                                          )}
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
                                            {cat.attributes.map((attr, idx) => {
                                              const isEnabled = !!attributes?.[attr.name];
                                              return showSkeletonView ? (
                                                <Skeleton key={`${attr.name}-${idx}`} className="h-9 w-28 rounded-md" />
                                              ) : (
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
                                                      ? "bg-primary/10 border-primary/50 text-primary hover:text-primary hover:border-primary/75 hover:bg-primary/15 disabled:opacity-100"
                                                      : "bg-background border-border text-muted-foreground disabled:opacity-70",
                                                    (!canManageRoles || isSubmitting) && "pointer-events-none"
                                                  )}
                                                >
                                                  {isEnabled ? <CheckCircle2 className="size-4" /> : <Circle className="size-4 text-muted-foreground/50" />}
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
                                      <h4 className="text-lg font-semibold text-primary">{t("pages.rolesManagement.categories.other", "Other")}</h4>
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
                                                ? "bg-primary/10 border-primary/50 text-primary hover:text-primary hover:border-primary/50 hover:bg-primary/10 disabled:opacity-100"
                                                : "bg-background border-border text-foreground hover:text-foreground hover:bg-accent/40 disabled:opacity-70",
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
                                </div>
                              );
                            })()}
                        </div>

                      </>
                    )}
                  </div>
                )}
              </div>
            ) : isLoadingRoles || rawIsLoadingAttrs ? (
              <div className="flex items-center justify-center min-h-[400px]">
                <Spinner className="size-6" />
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
    </>
  );
}

export default RolePermissionsDesktop;