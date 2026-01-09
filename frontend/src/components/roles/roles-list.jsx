import * as React from "react"
import { useTranslation } from "react-i18next"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { Card, CardContent } from "@/components/ui/card"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Edit, MoreVertical, Plus, Search, Shield, Trash2, X } from "lucide-react"
import { Scroller } from "@/components/ui/scroller"

export function RolesList({ 
  filteredRoles = [], 
  selectedRole,
  isLoading = false,
  loadingDelayMs = 0,
  searchKeyword = "",
  canManageRoles = false,
  isSubmitting = false,
  className,
  onRoleSelect,
  onSearchChange,
  onCreateClick,
  onEditClick,
  onDeleteClick,
}) {
  const { t } = useTranslation();
  const scrollerRef = React.useRef(null);
  const [scrollbarWidth, setScrollbarWidth] = React.useState(0);
  const [delayedLoading, setDelayedLoading] = React.useState(false);

  const rawIsLoading = !!isLoading;
  const effectiveDelayMs = Number(loadingDelayMs ?? 0);

  // Delay showing the loading spinner to avoid flash on quick responses
  React.useEffect(() => {
    if (!rawIsLoading) {
      setDelayedLoading(false);
      return undefined;
    }

    if (!effectiveDelayMs || effectiveDelayMs <= 0) {
      setDelayedLoading(true);
      return undefined;
    }

    const timer = window.setTimeout(() => {
      setDelayedLoading(true);
    }, effectiveDelayMs);

    return () => {
      window.clearTimeout(timer);
    };
  }, [rawIsLoading, effectiveDelayMs]);

  const recomputeScrollbar = React.useCallback(() => {
    const el = scrollerRef.current;
    if (!el) return;
    const width = Math.max(0, el.offsetWidth - el.clientWidth);
    setScrollbarWidth(width);
  }, []);

  React.useLayoutEffect(() => {
    // Recompute after layout.
    const raf = window.requestAnimationFrame(recomputeScrollbar);
    return () => window.cancelAnimationFrame(raf);
  }, [recomputeScrollbar, filteredRoles.length, isLoading]);

  React.useEffect(() => {
    window.addEventListener("resize", recomputeScrollbar);
    return () => window.removeEventListener("resize", recomputeScrollbar);
  }, [recomputeScrollbar]);

  const baseXPaddingPx = 20;
  const scrollerPaddingRightPx = Math.max(0, baseXPaddingPx - scrollbarWidth - 2);
  const canEditOrDelete = canManageRoles && !rawIsLoading && !isSubmitting;

  const showLoading = delayedLoading;

  return (
    <Card className={cn("flex flex-col h-full min-h-0 py-0", className)}>
      <CardContent className="flex flex-col gap-4 flex-1 min-h-0 p-0">
        {/* Search and Create */}
        <div className="space-y-4 flex-shrink-0 px-5 pt-5">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
              <Input
                id="role-list-panel-search"
                name="role-list-panel-search"
                placeholder={t("pages.rolesManagement.searchPlaceholder", "Search roles")}
                value={searchKeyword}
                onChange={(e) => onSearchChange?.(e.target.value)}
                className={cn("w-full px-9 h-10 rounded-md", searchKeyword?.trim() && "pr-10")}
              />
              {!!searchKeyword?.trim() && (
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7" 
                  aria-label={t("common.actions.clear", "Clear")}
                  onClick={() => onSearchChange?.("")}
                >
                  <X className="size-4" />
                </Button>
              )}
            </div>
          </div>
          {canManageRoles && (
            <Button 
              type="button"
              onClick={onCreateClick}
              disabled={isSubmitting}
              className="w-full bg-primary hover:bg-primary/90"
            >
              <Plus className="size-4" />
              {t("common.actions.create", "Create role")}
            </Button>
          )}
        </div>

        {/* Role List */}
        <Scroller
          ref={scrollerRef}
          hideScrollbar="hover"
          className="flex-1 mb-5 mr-[2px]"
          style={{
            paddingTop: 0,
            paddingBottom: 0,
            paddingLeft: baseXPaddingPx,
            paddingRight: scrollerPaddingRightPx,
            scrollbarGutter: "stable",
          }}
        >
          {showLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner className="size-6" />
            </div>
          ) : filteredRoles.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center px-4">
              <Shield className="size-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                {searchKeyword 
                ? t("pages.rolesManagement.noRolesFound", "No matching roles") 
                : t("pages.rolesManagement.noRoles", "No roles yet")}
              </p>
            </div>
          ) : (
            <div className="w-full space-y-2">
              {filteredRoles.map((role) => (
                (() => {
                  const isSelected = selectedRole?.id === role.id;
                  return (
                    <div
                      key={role.id}
                      onClick={() => onRoleSelect?.(role)}
                      className={cn(
                        "group relative w-full py-4 px-5 rounded-lg cursor-pointer select-none outline-none",
                        isSelected
                          ? "bg-primary/15 before:content-[''] before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2 before:h-[55%] before:w-1 before:bg-primary before:rounded-r-full"
                          : "bg-accent/40 hover:bg-accent"
                      )}
                    >
                      <div className={cn("pr-16", !canEditOrDelete && "pr-0")}>
                        <div className="text-sm font-semibold">{role.name}</div>
                        <div className="text-xs text-muted-foreground mt-1 line-clamp-2">{role.description || "-"}</div>
                      </div>

                      {canEditOrDelete && (
                        <div
                          className={cn(
                            "absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1",
                            "opacity-80 group-hover:opacity-100",
                            isSelected && "opacity-100"
                          )}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                className="h-9 w-9 hover:bg-foreground/10"
                                aria-label={t("common.actions.more", "More actions")}
                                disabled={isSubmitting}
                              >
                                <MoreVertical className="size-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" sideOffset={4} className="w-28">
                              <DropdownMenuItem
                                onSelect={() => onEditClick?.(role)}
                                className="justify-between gap-2"
                                disabled={isSubmitting}
                              >
                                {t("common.actions.edit", "Edit")}
                                <Edit className="size-4" />
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onSelect={() => onDeleteClick?.(role)}
                                className="justify-between gap-2 text-destructive focus:text-destructive hover:!bg-destructive/10"
                                disabled={isSubmitting}
                              >
                                {t("common.actions.delete", "Delete")}
                                <Trash2 className="size-4" />
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      )}
                    </div>
                  );
                })()
              ))}
            </div>
          )}
        </Scroller>
      </CardContent>
    </Card>
  );
}

export default RolesList;