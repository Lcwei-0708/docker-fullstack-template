import * as React from "react"
import { useTranslation } from "react-i18next"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import {
  ArrowDown10,
  ArrowDownAZ,
  ArrowUp01,
  ArrowUpAZ,
  Check,
  Edit,
  MoreVertical,
  Plus,
  Search,
  Shield,
  Trash2,
  X,
} from "lucide-react"
import { Scroller } from "@/components/ui/scroller"

export function RolesList({ 
  filteredRoles = [], 
  selectedRole,
  isLoading = false,
  loadingDelayMs = 0,
  searchKeyword = "",
  canManageRoles = false,
  actorLevel = 0,
  actorRoleId = null,
  isSubmitting = false,
  sortBy = "level",
  sortDir = "desc",
  className,
  onRoleSelect,
  onSearchChange,
  onSortChange,
  onCreateClick,
  onEditClick,
  onDeleteClick,
}) {
  const { t } = useTranslation();
  const scrollerRef = React.useRef(null);
  const [scrollbarWidth, setScrollbarWidth] = React.useState(0);
  const [delayedLoading, setDelayedLoading] = React.useState(false);
  const [sortOpen, setSortOpen] = React.useState(false);

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

  const handleSortByChange = React.useCallback(
    (nextSortBy) => {
      if (!onSortChange) return;
      onSortChange(nextSortBy, sortDir);
    },
    [onSortChange, sortDir]
  );

  const handleSortDirChange = React.useCallback(
    (nextSortDir) => {
      if (!onSortChange) return;
      onSortChange(sortBy, nextSortDir);
    },
    [onSortChange, sortBy]
  );

  const baseXPaddingPx = 20;
  const scrollerPaddingRightPx = Math.max(0, baseXPaddingPx - scrollbarWidth - 2);
  const canEditOrDelete = canManageRoles && !rawIsLoading && !isSubmitting;

  const showLoading = delayedLoading;
  const SortIcon = React.useMemo(() => {
    if (sortBy === "name") {
      return sortDir === "asc" ? ArrowDownAZ : ArrowUpAZ;
    }
    // Level: low→high vs high→low use different arrow directions
    return sortDir === "asc" ? ArrowUp01 : ArrowDown10;
  }, [sortBy, sortDir]);

  const sortTrigger = (
    <Popover open={sortOpen} onOpenChange={setSortOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="secondary"
          size="icon"
          className="h-10 w-10 shrink-0"
          disabled={rawIsLoading || isSubmitting}
          aria-label={t("common.actions.sort", "Sort")}
        >
          <SortIcon className="size-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-52 p-2" align="end">
        <div className="space-y-2">
          <div className="px-2 pt-1 text-xs font-semibold text-muted-foreground select-none">
            {t("common.actions.sortBy", "Sort By")}
          </div>
          <div className="space-y-1">
            <Button
              type="button"
              variant="ghost"
              onClick={() => handleSortByChange("name")}
              className={cn(
                "w-full h-9 flex items-center justify-between px-2 text-sm rounded-xs font-normal",
                sortBy === "name" && "bg-accent font-medium"
              )}
            >
              <span>{t("pages.rolesManagement.sortByName", "By name")}</span>
              {sortBy === "name" && <Check className="size-4" />}
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => handleSortByChange("level")}
              className={cn(
                "w-full h-9 flex items-center justify-between px-2 text-sm rounded-xs font-normal",
                sortBy === "level" && "bg-accent font-medium"
              )}
            >
              <span>{t("pages.rolesManagement.sortByLevel", "By level")}</span>
              {sortBy === "level" && <Check className="size-4" />}
            </Button>
          </div>

          <Separator className="my-2" />

          <div className="px-2 pt-1 text-xs font-semibold text-muted-foreground select-none">
            {t("common.actions.sortOrder", "Sort Order")}
          </div>
          <div className="space-y-1">
            <Button
              type="button"
              variant="ghost"
              onClick={() => handleSortDirChange("asc")}
              className={cn(
                "w-full h-9 flex items-center justify-between px-2 text-sm rounded-xs font-normal",
                sortDir === "asc" && "bg-accent font-medium"
              )}
            >
              <span>{t("pages.rolesManagement.sortAsc", "Low to high")}</span>
              {sortDir === "asc" && <Check className="size-4" />}
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => handleSortDirChange("desc")}
              className={cn(
                "w-full h-9 flex items-center justify-between px-2 text-sm rounded-xs font-normal",
                sortDir === "desc" && "bg-accent font-medium"
              )}
            >
              <span>{t("pages.rolesManagement.sortDesc", "High to low")}</span>
              {sortDir === "desc" && <Check className="size-4" />}
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );

  return (
    <Card className={cn("flex flex-col h-full min-h-0 py-0", className)}>
      <CardContent className="flex flex-col gap-4 flex-1 min-h-0 p-0">
        {/* Search and Create */}
        <div className="space-y-4 flex-shrink-0 px-5 pt-5">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Input
                id="role-list-panel-search"
                name="role-list-panel-search"
                placeholder={t("pages.rolesManagement.searchPlaceholder", "Search roles")}
                value={searchKeyword}
                onChange={(e) => onSearchChange?.(e.target.value)}
                startIcon={<Search />}
                className={cn("w-full h-10 rounded-md", searchKeyword?.trim() && "pr-10")}
              />
              {!!searchKeyword?.trim() && (
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="absolute right-2 top-1/2 z-10 -translate-y-1/2 h-7 w-7" 
                  aria-label={t("common.actions.clear", "Clear")}
                  onClick={() => onSearchChange?.("")}
                >
                  <X className="size-4" />
                </Button>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {canManageRoles ? (
              <Button 
                type="button"
                onClick={onCreateClick}
                disabled={isSubmitting}
                className="flex-1 bg-primary hover:bg-primary/90"
              >
                <Plus className="size-4" />
                {t("common.actions.create", "Create role")}
              </Button>
            ) : null}
            {sortTrigger}
          </div>
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
                        <div className="flex items-center gap-2 min-w-0">
                          <div className="text-sm font-semibold truncate">{role.name}</div>
                          {role.level != null && (
                            <Badge
                              variant="outline"
                              className="shrink-0 rounded-sm px-1.5 py-0 text-[10px] font-semibold leading-4 border-primary/40 bg-primary/10 text-primary"
                            >
                              Lv.{role.level}
                            </Badge>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1 line-clamp-2">{role.description || "-"}</div>
                      </div>

                      {canEditOrDelete &&
                        Number(role.level ?? 0) <= Number(actorLevel ?? 0) &&
                        role.id !== actorRoleId && (
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
