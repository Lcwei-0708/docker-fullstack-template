import * as React from "react"
import { cn } from "@/lib/utils"
import { useTranslation } from "react-i18next"
import { Button } from "@/components/ui/button"
import { Spinner } from "@/components/ui/spinner"
import { Check, ChevronsUpDown, Edit, Trash2 } from "lucide-react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { 
  Command, 
  CommandEmpty, 
  CommandGroup, 
  CommandInput, 
  CommandItem, 
  CommandList,
} from "@/components/ui/command"

export function RoleSelector({
  filteredRoles = [],
  selectedRole,
  isLoading = false,
  searchKeyword = "",
  disabled = false,
  canManageRoles = false,
  isSubmitting = false,
  onRoleSelect,
  onSearchChange,
  onEditClick,
  onDeleteClick,
}) {
  const { t } = useTranslation()
  const [open, setOpen] = React.useState(false)

  const selectedLabel = selectedRole?.name || t("pages.rolesManagement.selectRole", "Select a role")
  const rawIsLoading = !!isLoading
  const hasKeyword = !!searchKeyword?.trim()
  const canEditOrDelete = !!selectedRole && canManageRoles && !rawIsLoading && !disabled && !isSubmitting

  return (
    <div className="flex flex-col gap-2 px-6">
      <div className="flex items-center gap-2">
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <Button
              type="button"
              variant="outline"
              role="combobox"
              aria-expanded={open}
              aria-label={t("pages.rolesManagement.selectRole", "Select a role")}
              className="w-full justify-between h-12 px-3 bg-popover text-base"
              disabled={rawIsLoading || disabled}
            >
              <span className="truncate">{selectedLabel}</span>
              <ChevronsUpDown className="size-4 opacity-70 shrink-0" />
            </Button>
          </PopoverTrigger>
          <PopoverContent
            className="w-[calc(100dvw-3rem)] max-w-[calc(100dvw-3rem)] p-0"
            align="start"
            onOpenAutoFocus={(e) => {
              // Mobile UX: do not auto-focus the search input when opening.
              e.preventDefault()
            }}
          >
            <Command>
              <CommandInput
                id="role-selector-search"
                name="role-selector-search"
                placeholder={t("pages.rolesManagement.searchPlaceholder", "Search roles")}
                value={searchKeyword}
                onValueChange={(value) => onSearchChange?.(value)}
                className="!h-12 text-base"
              />
              <CommandList>
                {rawIsLoading ? (
                  <div className="flex items-center justify-center py-10">
                    <Spinner className="size-6" />
                  </div>
                ) : (
                  <>
                    <CommandEmpty className="text-sm text-center text-muted-foreground py-6">
                      {hasKeyword
                        ? t("pages.rolesManagement.noRolesFound", "No matching roles")
                        : t("pages.rolesManagement.noRoles", "No roles yet")}
                    </CommandEmpty>
                    <CommandGroup>
                      {filteredRoles.map((role) => (
                        (() => {
                          const isSelected = selectedRole?.id === role.id
                          return (
                        <CommandItem
                          key={role.id}
                          value={`${role.name || ""} ${role.description || ""}`.trim()}
                          onSelect={() => {
                            onRoleSelect?.(role)
                            onSearchChange?.("")
                            setOpen(false)
                          }}
                          className={cn(
                            "flex items-center justify-between gap-2 py-2 px-3 rounded-md",
                            "data-[selected=true]:bg-transparent aria-selected:bg-transparent",
                            isSelected && "!bg-primary/15 border border-primary/20"
                          )}
                        >
                          <div className="min-w-0">
                            <div className="text-base font-medium truncate">{role.name}</div>
                            <div className="text-sm text-muted-foreground line-clamp-2">{role.description || "-"}</div>
                          </div>
                          <Check
                            className={cn("size-5 shrink-0 text-primary", isSelected ? "opacity-100" : "opacity-0")}
                          />
                        </CommandItem>
                          )
                        })()
                      ))}
                    </CommandGroup>
                  </>
                )}
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>

        {canManageRoles && (
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="secondary"
              size="icon"
              className="h-12 w-12 shrink-0"
              disabled={!canEditOrDelete}
              aria-label={t("common.actions.edit", "Edit")}
              onClick={() => onEditClick?.()}
            >
              <Edit className="size-5" />
            </Button>

            <Button
              type="button"
              variant="destructive"
              size="icon"
              className="h-12 w-12 shrink-0"
              disabled={!canEditOrDelete}
              aria-label={t("common.actions.delete", "Delete")}
              onClick={() => onDeleteClick?.()}
            >
              <Trash2 className="size-5" />
            </Button>
          </div>
        )}
      </div>

      <div className="text-sm text-muted-foreground line-clamp-2 px-3">
        {selectedRole?.description || ""}
      </div>
    </div>
  )
}

export default RoleSelector