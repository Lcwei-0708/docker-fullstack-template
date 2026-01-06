import React from "react"
import { cn } from "@/lib/utils"
import { useTranslation } from "react-i18next"
import { useIsMobile } from "@/hooks/useMobile"
import { useAuthStatus } from "@/hooks/useAuth"
import { RolesManagementPanel } from "@/components/roles/roles-management-panel"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

export default function Roles() {
  const { t } = useTranslation();
  const isMobile = useIsMobile();
  const { hasPermission } = useAuthStatus();
  const canManageRoles = hasPermission("manage-roles");
  const rolesPanelRef = React.useRef(null);

  const handleCreate = React.useCallback(() => {
    rolesPanelRef.current?.handleCreate?.();
  }, []);

  return (
    <div className={cn("h-full flex flex-col p-6 space-y-4", isMobile && "flex-col p-0 space-y-2")}>
      <div
        className={cn(
          "w-full", isMobile ? "flex items-center justify-between gap-4 px-6" : ""
        )}
      >
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold">
            {t("pages.rolesManagement.title", "Roles Management")}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t("pages.rolesManagement.description", "Manage system roles and permissions")}
          </p>
        </div>
        {isMobile && canManageRoles && (
          <Button
            variant="default"
            onClick={handleCreate}
            className="px-3 gap-1 h-12"
          >
            <Plus className="size-5" />
            <span className="text-base font-medium whitespace-nowrap">{t("common.actions.create", "Create")}</span>
            <span className="sr-only">{t("common.actions.create", "Create")}</span>
          </Button>
        )}
      </div>
      <RolesManagementPanel ref={rolesPanelRef} canManageRoles={canManageRoles} />
    </div>
  );
}
