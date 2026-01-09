import * as React from "react";
import { useTranslation } from "react-i18next";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
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
  const [isActionsDrawerOpen, setIsActionsDrawerOpen] = React.useState(false);
  const longPressTimerRef = React.useRef(null);
  const isLongPressRef = React.useRef(false);

  React.useEffect(() => {
    return () => {
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current);
      }
    };
  }, []);

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
  const handlePointerDown = () => {
    if (!canManageUsers || isSelectionMode) return;
    
    isLongPressRef.current = false;
    longPressTimerRef.current = setTimeout(() => {
      isLongPressRef.current = true;
      onLongPress?.();
    }, 500); // 500ms for long press
  };

  const handlePointerUp = () => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  };

  const handlePointerCancel = () => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
    isLongPressRef.current = false;
  };

  const handleCardClick = (e) => {
    // Prevent opening drawer when clicking on action button
    if (e.target.closest('[data-action-button]')) {
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

  const handleActionClick = (action) => {
    setIsActionsDrawerOpen(false);
    if (action === 'edit') {
      onEdit?.(user);
    } else if (action === 'resetPassword') {
      onResetPassword?.(user);
    } else if (action === 'delete') {
      onDelete?.(user);
    }
  };


  return (
    <>
      <Card 
        className={cn(
          "shadow-none border-y-0 border-x-5 border-transparent rounded-none py-2 cursor-pointer bg-background hover:bg-accent select-none",
          isSelectionMode && isSelected && "bg-primary/10 border-l-primary"
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
                  <Button
                    variant="ghost"
                    className="h-6 w-6 p-4 rounded-xs"
                    data-action-button
                    onClick={(e) => {
                      e.stopPropagation();
                      setIsActionsDrawerOpen(true);
                    }}
                  >
                    <MoreHorizontal className="size-5" />
                    <span className="sr-only">
                      {t("common.actions.openMenu", "Open menu")}
                    </span>
                  </Button>
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

      {/* Actions Drawer */}
      <Drawer open={isActionsDrawerOpen} onOpenChange={setIsActionsDrawerOpen}>
        <DrawerContent>
          <DrawerHeader>
            <DrawerTitle className="text-xl font-semibold">
              {fullName}
            </DrawerTitle>
            <DrawerDescription>
            </DrawerDescription>
          </DrawerHeader>
          <div className="px-6 pb-10 pt-2">
            <div className="space-y-6">
              {/* General Actions Group */}
              <div className="space-y-2">
                <div className="overflow-hidden rounded-lg border divide-y divide-border">
                  <Button
                    variant="default"
                    className="w-full justify-between gap-3 h-auto py-4 px-4 rounded-none bg-input text-card-foreground hover:bg-accent"
                    onClick={() => handleActionClick('edit')}
                  >
                    <span className="flex-1 text-left">
                      {t("common.actions.edit", "Edit")}
                    </span>
                    <Edit className="size-5 shrink-0" />
                  </Button>
                  <Button
                    variant="default"
                    className="w-full justify-between gap-3 h-auto py-4 px-4 rounded-none bg-input text-card-foreground hover:bg-accent"
                    onClick={() => handleActionClick('resetPassword')}
                  >
                    <span className="flex-1 text-left">
                      {t("common.actions.resetPassword", "Reset Password")}
                    </span>
                    <Key className="size-5 shrink-0" />
                  </Button>
                </div>
              </div>

              {/* Dangerous Actions Group */}
              <div className="space-y-2">
                <div className="overflow-hidden rounded-lg border border-destructive/20">
                  <Button
                    variant="destructive"
                    className="w-full justify-between gap-3 h-auto py-4 px-4 bg-destructive/15 text-destructive hover:bg-accent"
                    onClick={() => handleActionClick('delete')}
                  >
                    <span className="flex-1 text-left">
                      {t("common.actions.delete", "Delete")}
                    </span>
                    <Trash2 className="size-5 shrink-0" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </DrawerContent>
      </Drawer>
    </>
  );
}