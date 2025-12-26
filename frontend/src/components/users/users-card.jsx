import * as React from "react";
import { useTranslation } from "react-i18next";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
} from "@/components/ui/drawer";
import {
  Mail,
  MoreHorizontal,
  Edit,
  Trash2,
  Key,
  Phone,
  Calendar,
  Shield,
  CheckCircle2,
  XCircle,
  Check,
} from "lucide-react";

/**
 * User Card component for mobile view
 * @param {Object} props
 * @param {Object} props.user - User object to display
 * @param {Function} props.onEdit - Edit handler function
 * @param {Function} props.onDelete - Delete handler function
 * @param {Function} props.onResetPassword - Reset password handler function
 * @param {boolean} props.canManageUsers - Whether user has manage-users permission
 */
export function UserCard({
  user,
  onEdit,
  onDelete,
  onResetPassword,
  canManageUsers = false,
  isSelectionMode = false,
  isSelected = false,
  onSelect,
  onLongPress,
}) {
  const { t } = useTranslation();
  const [isDrawerOpen, setIsDrawerOpen] = React.useState(false);
  const longPressTimerRef = React.useRef(null);
  const isLongPressRef = React.useRef(false);

  if (!user) return null;

  const fullName = `${user.first_name || ""} ${user.last_name || ""}`.trim() || "-";

  const formatDate = (dateString) => {
    if (!dateString) return "-";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateString;
    }
  };

  // Handle long press to enter selection mode
  const handlePointerDown = (e) => {
    if (!canManageUsers || isSelectionMode) return;
    
    isLongPressRef.current = false;
    longPressTimerRef.current = setTimeout(() => {
      isLongPressRef.current = true;
      onLongPress?.();
    }, 500); // 500ms for long press
  };

  const handlePointerUp = (e) => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  };

  const handlePointerCancel = (e) => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
    isLongPressRef.current = false;
  };

  const handleCardClick = (e) => {
    // Prevent opening drawer when clicking on dropdown menu
    if (e.target.closest('[data-slot="dropdown-menu-trigger"]') || 
        e.target.closest('[data-slot="dropdown-menu-content"]')) {
      return;
    }

    // In selection mode, toggle selection instead of opening drawer
    if (isSelectionMode) {
      e.preventDefault();
      e.stopPropagation();
      onSelect?.(user);
      return;
    }

    // Only open drawer if it wasn't a long press
    if (!isLongPressRef.current) {
      setIsDrawerOpen(true);
    }
    isLongPressRef.current = false;
  };

  // Cleanup on unmount
  React.useEffect(() => {
    return () => {
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current);
      }
    };
  }, []);


  return (
    <>
      <Card 
        className={cn(
          "shadow-xs border-y-0 border-x-5 border-transparent rounded-none py-2 cursor-pointer bg-background hover:bg-accent/50 select-none",
          isSelectionMode && isSelected && "bg-primary/1 border-l-primary"
        )}
        onClick={handleCardClick}
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerCancel}
        onPointerLeave={handlePointerCancel}
      >
        <CardContent className="py-2 px-6">
          <div className="flex items-center justify-between gap-3">
            {/* Left side: Name and Email (vertical layout) */}
            <div className="flex-1 min-w-0 space-y-1">
              <div className="flex items-center gap-2">
                <CardTitle className="text-base font-semibold leading-tight flex items-center gap-2">
                  <span className="truncate">{fullName}</span>
                  <Badge
                    variant="outline"
                    className={cn(
                      "shrink-0 px-2 py-0.5 text-xs",
                      user.status
                        ? "bg-success/20 text-success border-success/35"
                        : "bg-destructive/20 text-destructive border-destructive/30"
                    )}
                  >
                    {user.status
                      ? t("pages.usersManagement.fields.status.values.active", "Active")
                      : t("pages.usersManagement.fields.status.values.inactive", "Inactive")}
                  </Badge>
                </CardTitle>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span className="truncate">{user.email || "-"}</span>
              </div>
            </div>
            
            {/* Right side: Action button or Selection check */}
            {canManageUsers && (
              <div className="flex items-center shrink-0" onClick={(e) => e.stopPropagation()}>
                {isSelectionMode ? (
                  <Button
                    variant="ghost"
                    size="icon"
                    className={cn(
                      "size-5 rounded-2xs",
                      isSelected && "bg-primary text-primary-foreground"
                    )}
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelect?.(user);
                    }}
                  >
                    {isSelected ? (
                      <Check className="size-4" />
                    ) : (
                      <div className="size-5 rounded-2xs border-2 border-muted-foreground" />
                    )}
                    <span className="sr-only">
                      {isSelected 
                        ? t("common.actions.deselect", "Deselect")
                        : t("common.actions.select", "Select")}
                    </span>
                  </Button>
                ) : (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-9 w-9 rounded-sm"
                      >
                        <MoreHorizontal className="size-4" />
                        <span className="sr-only">
                          {t("common.actions.openMenu", "Open menu")}
                        </span>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-auto">
                      <DropdownMenuItem
                        className="flex items-center justify-between gap-8 rounded-xs"
                        onSelect={() => onEdit?.(user)}
                      >
                        {t("common.actions.edit", "Edit")}
                        <Edit className="size-4" />
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="flex items-center justify-between gap-8 rounded-xs"
                        onSelect={() => onResetPassword?.(user)}
                      >
                        {t("common.actions.resetPassword", "Reset Password")}
                        <Key className="size-4" />
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        variant="destructive"
                        className="flex items-center justify-between gap-8 rounded-xs"
                        onClick={() => onDelete?.(user)}
                      >
                        {t("common.actions.delete", "Delete")}
                        <Trash2 className="size-4" />
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <Drawer open={isDrawerOpen} onOpenChange={setIsDrawerOpen}>
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle className="text-xl font-semibold">
              {fullName}
            </DrawerTitle>
            <DrawerDescription>
            </DrawerDescription>
          </DrawerHeader>
          <div className="px-6 pb-8">
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Mail className="size-4 mt-0.5 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-muted-foreground">
                    {t("pages.usersManagement.fields.email.label", "Email")}
                  </div>
                  <div className="text-sm mt-0.5">{user.email || "-"}</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Phone className="size-4 mt-0.5 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-muted-foreground">
                    {t("pages.usersManagement.fields.phone.label", "Phone")}
                  </div>
                  <div className="text-sm mt-0.5">{user.phone || "-"}</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Shield className="size-4 mt-0.5 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-muted-foreground">
                    {t("pages.usersManagement.fields.role.label", "Role")}
                  </div>
                  <div className="text-sm mt-0.5">{user.role || "-"}</div>
                </div>
              </div>

              <div className="flex items-start gap-3">
                {user.status ? (
                  <CheckCircle2 className="size-4 mt-0.5 text-muted-foreground shrink-0" />
                ) : (
                  <XCircle className="size-4 mt-0.5 text-muted-foreground shrink-0" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-muted-foreground">
                    {t("pages.usersManagement.fields.status.label", "Status")}
                  </div>
                  <div className="text-sm mt-0.5">
                    <Badge
                      variant="outline"
                      className={cn(
                        "px-2 py-0.5 text-xs",
                        user.status
                          ? "bg-success/20 text-success border-success/35"
                          : "bg-destructive/20 text-destructive border-destructive/30"
                      )}
                    >
                      {user.status
                        ? t("pages.usersManagement.fields.status.values.active", "Active")
                        : t("pages.usersManagement.fields.status.values.inactive", "Inactive")}
                    </Badge>
                  </div>
                </div>
              </div>

              {user.created_at && (
                <div className="flex items-start gap-3">
                  <Calendar className="size-4 mt-0.5 text-muted-foreground shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-muted-foreground">
                      {t("pages.usersManagement.fields.createdAt.label", "Created At")}
                    </div>
                    <div className="text-sm mt-0.5">{formatDate(user.created_at)}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </DrawerContent>
      </Drawer>
    </>
  );
}