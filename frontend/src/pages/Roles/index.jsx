import React from "react"
import { cn } from "@/lib/utils"
import { useTranslation } from "react-i18next"
import { useIsMobile } from "@/hooks/useMobile"
import { useAuthStatus } from "@/hooks/useAuth"
import { RolesManagementPanel } from "@/components/roles/roles-management-panel"

export default function Roles() {
  const { t } = useTranslation();
  const isMobile = useIsMobile();
  const { hasPermission } = useAuthStatus();
  const canManageRoles = hasPermission("manage-roles");

  return (
    <div className={cn("h-full flex flex-col", isMobile && "flex-col")}>
      <div className={cn("p-6 pb-4", isMobile && "p-4 pb-2")}>
        <h1 className="text-xl font-bold">{t("pages.rolesManagement.title", "Roles Management")}</h1>
        <p className="text-sm text-muted-foreground mt-1">{t("pages.rolesManagement.description", "Manage system roles and permissions")}</p>
      </div>
      <div className="flex-1 overflow-hidden">
        <RolesManagementPanel canManageRoles={canManageRoles} />
      </div>
    </div>
  );
}
