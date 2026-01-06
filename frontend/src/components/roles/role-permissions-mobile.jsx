import * as React from "react"
import { cn } from "@/lib/utils"
import { useTranslation } from "react-i18next"
import { Checkbox } from "@/components/ui/checkbox"
import { Switch } from "@/components/ui/switch"
import { Spinner } from "@/components/ui/spinner"
import { Skeleton } from "@/components/ui/skeleton"
import { Scroller } from "@/components/ui/scroller"
import { Separator } from "@/components/ui/separator"
import { Shield } from "lucide-react"
import { X, SaveIcon } from "lucide-react"
import { ActionBar, ActionBarGroup, ActionBarItem, ActionBarSelection } from "@/components/ui/action-bar"

const toCamelKey = (input) => {
  if (!input || typeof input !== "string") return ""
  const parts = input.split(/[-_\s]+/).filter(Boolean)
  if (parts.length === 0) return ""
  return parts
    .map((p, idx) => {
      const s = String(p)
      if (idx === 0) return s.charAt(0).toLowerCase() + s.slice(1)
      return s.charAt(0).toUpperCase() + s.slice(1)
    })
    .join("")
}

const normalizeGroupsForDisplay = (groups, attributesFlat = {}) => {
  if (!Array.isArray(groups)) return []

  return groups
    .filter((g) => !!g && typeof g === "object")
    .map((g) => {
      const groupName = g.group || "default"
      const categoriesObj = g.categories && typeof g.categories === "object" ? g.categories : {}
      const categories = Object.entries(categoriesObj).map(([categoryName, list]) => {
        const attrs = (Array.isArray(list) ? list : [])
          .filter((a) => a?.name)
          .map((a) => ({
            name: a.name,
            value: typeof attributesFlat?.[a.name] === "boolean" ? attributesFlat[a.name] : !!a.value,
          }))

        return { name: categoryName, attributes: attrs }
      })

      return { group: groupName, categories }
    })
}

const normalizeLegacyAttributesForDisplay = (attributesFlat = {}) => {
  return Object.entries(attributesFlat).map(([name, value]) => ({ name, value: !!value }))
}

export function RolePermissionsMobile({
  selectedRole,
  attributes = {},
  attributeGroups = [],
  isLoadingAttributes = false,
  hasChanges = false,
  isSubmitting = false,
  canManageRoles = false,
  onAttributeToggle,
  onSaveAttributes,
  onResetAttributes,
}) {
  const { t } = useTranslation()
  const [delayedLoadingAttrs, setDelayedLoadingAttrs] = React.useState(false)

  const rawIsLoadingAttrs = !!isLoadingAttributes
  const loadingDelayMs = 100

  React.useEffect(() => {
    if (!rawIsLoadingAttrs) {
      setDelayedLoadingAttrs(false)
      return undefined
    }
    const timer = window.setTimeout(() => setDelayedLoadingAttrs(true), loadingDelayMs)
    return () => window.clearTimeout(timer)
  }, [rawIsLoadingAttrs, loadingDelayMs])

  const organizedGroups = React.useMemo(() => {
    if (Array.isArray(attributeGroups) && attributeGroups.length > 0) {
      return normalizeGroupsForDisplay(attributeGroups, attributes)
    }
    return []
  }, [attributeGroups, attributes])

  const legacyAttributes = React.useMemo(() => {
    if (organizedGroups.length > 0) return []
    if (Object.keys(attributes).length === 0) return []
    return normalizeLegacyAttributesForDisplay(attributes)
  }, [attributes, organizedGroups.length])

  const hasPermissionsData = organizedGroups.length > 0 || legacyAttributes.length > 0
  const showEmptyState = !rawIsLoadingAttrs && !hasPermissionsData
  const showSkeletonView = rawIsLoadingAttrs && delayedLoadingAttrs

  const getGroupLabel = (name) => t(`pages.rolesManagement.groups.${toCamelKey(name)}`, name)
  const getCategoryLabel = (name) => t(`pages.rolesManagement.categories.${toCamelKey(name)}`, name)
  const getAttributeLabel = (name) => t(`pages.rolesManagement.attributes.${toCamelKey(name)}`, name)

  const getGroupAttributeNames = React.useCallback((groupObj) => {
    return (groupObj?.categories || [])
      .flatMap((cat) => (cat?.attributes || []).map((a) => a?.name).filter(Boolean))
      .filter(Boolean)
  }, [])

  const handleSelectAllGroup = React.useCallback(
    (groupObj) => {
      const allAttrNames = getGroupAttributeNames(groupObj)
      const allSelected = allAttrNames.length > 0 && allAttrNames.every((name) => !!attributes?.[name])
      allAttrNames.forEach((name) => {
        if (allSelected) {
          if (attributes?.[name]) onAttributeToggle?.(name)
        } else {
          if (!attributes?.[name]) onAttributeToggle?.(name)
        }
      })
    },
    [attributes, onAttributeToggle, getGroupAttributeNames]
  )

  const isGroupAllSelected = React.useCallback(
    (groupObj) => {
      const allAttrNames = getGroupAttributeNames(groupObj)
      if (allAttrNames.length === 0) return false
      return allAttrNames.every((name) => !!attributes?.[name])
    },
    [attributes, getGroupAttributeNames]
  )

  const handleSelectAllLegacy = React.useCallback(() => {
    const names = legacyAttributes.map((a) => a.name)
    const allSelected = names.length > 0 && names.every((n) => !!attributes?.[n])
    names.forEach((n) => {
      if (allSelected) {
        if (attributes?.[n]) onAttributeToggle?.(n)
      } else {
        if (!attributes?.[n]) onAttributeToggle?.(n)
      }
    })
  }, [legacyAttributes, attributes, onAttributeToggle])

  const renderSettingRow = React.useCallback(
    ({ label, checked, disabled, onToggle, showDivider = true, isSkeleton = false }) => {
      const handleActivate = () => {
        if (disabled) return
        onToggle?.()
      }

      const handleKeyDown = (e) => {
        if (disabled) return
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault()
          onToggle?.()
        }
      }

      return (
        <>
          <div
            role="button"
            tabIndex={disabled ? -1 : 0}
            className={cn(
              "w-full h-14 flex items-center justify-between gap-4 p-4 text-left rounded-none bg-transparent border-none hover:bg-transparent",
              disabled && "cursor-not-allowed opacity-70"
            )}
            aria-label={label}
            aria-pressed={!!checked}
            onClick={handleActivate}
            onKeyDown={handleKeyDown}
          >
            {isSkeleton ? (
              <Skeleton className="h-4 w-40 rounded-md" />
            ) : (
              <span className="text-base font-normal text-foreground truncate">{label}</span>
            )}
            {isSkeleton ? (
              <Skeleton className="h-6 w-11 rounded-full" />
            ) : (
              <Switch
                className="data-[state=checked]:bg-success/80"
                checked={!!checked}
                disabled={disabled}
                aria-label={label}
                onClick={(e) => e.stopPropagation()}
                onCheckedChange={() => onToggle?.()}
              />
            )}
          </div>
          {showDivider && <Separator />}
        </>
      )
    },
    []
  )

  if (!selectedRole) {
    return (
      <div className="flex items-center justify-center py-20 text-center">
        <div>
          <Shield className="size-12 text-muted-foreground mx-auto mb-3" />
          <div className="text-base text-muted-foreground">
            {t("pages.rolesManagement.selectRole", "Select a role")}
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="flex flex-col">
        <Scroller 
          hideScrollbar={false} 
          className="flex-1 max-h-[calc(100dvh-210px)]" 
          style={{ 
            paddingLeft: 0, 
            paddingRight: 0, 
            paddingTop: 12, 
            paddingBottom: 80,
            scrollbarGutter: "stable",
          }}
        >
          <div className="space-y-7 px-6">
          {showEmptyState ? (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <Shield className="size-12 text-muted-foreground mb-3" />
              <p className="text-base text-muted-foreground">
                {t("pages.rolesManagement.dialog.noAttributes", "No available permissions")}
              </p>
            </div>
          ) : (
            <>
              {organizedGroups.length > 0 &&
                organizedGroups.map((g) => {
                  const groupAttrNames = getGroupAttributeNames(g)
                  const groupTotal = groupAttrNames.length
                  const groupSelectedCount = groupAttrNames.reduce((acc, name) => acc + (attributes?.[name] ? 1 : 0), 0)
                  const groupAllSelected = isGroupAllSelected(g)
                  const groupCheckedState =
                    groupTotal > 0 && groupSelectedCount === groupTotal
                      ? true
                      : groupTotal > 0 && groupSelectedCount > 0
                        ? "indeterminate"
                        : false
                  const groupCheckboxId = `role-perms-mobile-${selectedRole?.id ?? "new"}-${toCamelKey(g.group) || "group"}`

                  return (
                    <div key={g.group} className="space-y-1">
                      <div className="flex items-center justify-between gap-3 px-1">
                        <div>
                          <div className="text-sm font-semibold text-muted-foreground tracking-wide uppercase truncate">
                            {getGroupLabel(g.group)}
                          </div>
                        </div>
                        <label
                          className={cn(
                            "flex items-center gap-2 rounded-md px-2 py-1 select-none",
                            canManageRoles && groupTotal > 0 && !isSubmitting && !showSkeletonView
                              ? "cursor-pointer hover:bg-accent/40"
                              : "cursor-default opacity-80"
                          )}
                          htmlFor={canManageRoles && groupTotal > 0 ? groupCheckboxId : undefined}
                          onClick={(e) => e.stopPropagation()}
                        >
                          {showSkeletonView ? (
                            <div className="flex items-center gap-2">
                              <Skeleton className="h-5.5 w-15 rounded-xs" />
                            </div>
                          ) : (
                            <>
                              {canManageRoles && groupTotal > 0 && (
                                <>
                                  <span className="sr-only">
                                    {groupAllSelected
                                      ? t("pages.rolesManagement.actions.deselectAll", "Deselect all")
                                      : t("pages.rolesManagement.actions.selectAll", "Select all")}
                                  </span>
                                  <Checkbox
                                    id={groupCheckboxId}
                                    className="rounded-2xs size-5.5 shrink-0"
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
                      </div>

                      <div className="rounded-xl border bg-popover overflow-hidden">
                        {g.categories.map((cat, catIdx) => {
                          const hasAttrs = (cat?.attributes || []).length > 0
                          return (
                            <div key={cat.name}>
                              <div className="px-4 py-2.5 text-sm font-semibold text-muted-foreground bg-muted/50">
                                {getCategoryLabel(cat.name)}
                              </div>
                              <Separator />

                              {hasAttrs ? (
                                cat.attributes.map((attr, idx) => {
                                  const isEnabled = !!attributes?.[attr.name]
                                  const isLastRow = catIdx === g.categories.length - 1 && idx === cat.attributes.length - 1
                                  const key = attr?.name || `${cat.name}-${idx}`
                                  return (
                                    <React.Fragment key={key}>
                                      {renderSettingRow({
                                        label: getAttributeLabel(attr.name),
                                        checked: isEnabled,
                                        disabled: !canManageRoles || isSubmitting || showSkeletonView,
                                        onToggle: () => onAttributeToggle?.(attr.name),
                                        showDivider: !isLastRow,
                                        isSkeleton: showSkeletonView,
                                      })}
                                    </React.Fragment>
                                  )
                                })
                              ) : (
                                <div className="px-4 py-3 text-sm text-muted-foreground">-</div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}

              {organizedGroups.length === 0 &&
                legacyAttributes.length > 0 && (() => {
                  const allSelected = legacyAttributes.every((a) => !!attributes?.[a.name])
                  const total = legacyAttributes.length
                  const selectedCount = legacyAttributes.reduce((acc, a) => acc + (attributes?.[a.name] ? 1 : 0), 0)
                  const checkedState =
                    total > 0 && selectedCount === total ? true : total > 0 && selectedCount > 0 ? "indeterminate" : false
                  const legacyCheckboxId = `role-perms-mobile-${selectedRole?.id ?? "new"}-legacy`
                  return (
                    <div key="legacy-attributes" className="space-y-2">
                      <div className="flex items-center justify-between gap-3 px-1">
                        <div className="min-w-0">
                          <div className="text-sm font-semibold text-muted-foreground tracking-wide uppercase truncate">
                            {t("pages.rolesManagement.categories.other", "Other")}
                          </div>
                        </div>
                        <label
                          className={cn(
                            "flex items-center gap-2 rounded-md px-2 py-1 select-none",
                            canManageRoles && total > 0 && !isSubmitting && !showSkeletonView
                              ? "cursor-pointer hover:bg-accent/40"
                              : "cursor-default opacity-80"
                          )}
                          htmlFor={canManageRoles && total > 0 ? legacyCheckboxId : undefined}
                          onClick={(e) => e.stopPropagation()}
                        >
                          {canManageRoles && total > 0 && (
                            <>
                              <span className="sr-only">
                                {allSelected
                                  ? t("pages.rolesManagement.actions.deselectAll", "Deselect all")
                                  : t("pages.rolesManagement.actions.selectAll", "Select all")}
                              </span>
                              <Checkbox
                                id={legacyCheckboxId}
                                className="rounded-2xs size-5.5 shrink-0"
                                checked={checkedState}
                                disabled={isSubmitting || showSkeletonView}
                                aria-label={
                                  allSelected
                                    ? t("pages.rolesManagement.actions.deselectAll", "Deselect all")
                                    : t("pages.rolesManagement.actions.selectAll", "Select all")
                                }
                                onCheckedChange={handleSelectAllLegacy}
                              />
                            </>
                          )}
                          <span className="text-sm text-muted-foreground tabular-nums font-medium">
                            {selectedCount}/{total}
                          </span>
                        </label>
                      </div>

                      <div className="rounded-xl border bg-background overflow-hidden">
                        {legacyAttributes.map((attr, idx) => {
                          const isEnabled = !!attributes?.[attr.name]
                          const isLastRow = idx === legacyAttributes.length - 1
                          const key = attr?.name || `legacy-${idx}`
                          return (
                            <React.Fragment key={key}>
                              {renderSettingRow({
                                label: getAttributeLabel(attr.name),
                                checked: isEnabled,
                                disabled: !canManageRoles || isSubmitting || showSkeletonView,
                                onToggle: () => onAttributeToggle?.(attr.name),
                                showDivider: !isLastRow,
                                isSkeleton: showSkeletonView,
                              })}
                            </React.Fragment>
                          )
                        })}
                      </div>
                    </div>
                  )
                })()}
            </>
          )}
          </div>
        </Scroller>
      </div>

      {/* Unsaved changes action bar */}
      {hasChanges && canManageRoles && (
        <ActionBar
          open={true}
          onOpenChange={(open) => {
            if (!open) onResetAttributes?.()
          }}
          onEscapeKeyDown={() => {
            onResetAttributes?.()
          }}
          className="w-auto max-w-xs"
        >
          <ActionBarSelection className="bg-transparent text-foreground border-none">
            <span className="text-sm font-medium whitespace-nowrap">
              {t("pages.rolesManagement.dialog.hasChanges", "Unsaved changes")}
            </span>
          </ActionBarSelection>
          <ActionBarGroup>
            <ActionBarItem
              onSelect={(e) => {
                e.preventDefault()
                onResetAttributes?.()
              }}
              disabled={isSubmitting}
              className="size-10 p-0 flex items-center justify-center"
            >
              <X className="size-5" />
              <span className="sr-only">{t("common.actions.cancel", "Cancel")}</span>
            </ActionBarItem>
            <ActionBarItem
              onSelect={(e) => {
                e.preventDefault()
                onSaveAttributes?.()
              }}
              disabled={isSubmitting}
              className={cn(
                "size-10 p-0 flex items-center justify-center",
                "bg-primary text-primary-foreground border-primary border hover:bg-primary/90"
              )}
            >
              {isSubmitting ? <Spinner className="size-5" /> : <SaveIcon className="size-5" />}
              <span className="sr-only">{t("common.actions.save", "Save")}</span>
            </ActionBarItem>
          </ActionBarGroup>
        </ActionBar>
      )}
    </>
  )
}

export default RolePermissionsMobile