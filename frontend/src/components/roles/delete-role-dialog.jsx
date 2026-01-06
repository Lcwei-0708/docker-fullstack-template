import * as React from "react";
import { useTranslation } from "react-i18next";
import { Spinner } from "@/components/ui/spinner";
import {
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export function DeleteRoleDialog({
  roleName = "",
  isSubmitting = false,
  onConfirm,
}) {
  const { t } = useTranslation();

  return (
    <AlertDialogContent
      onCloseAutoFocus={(e) => e.preventDefault()}
    >
      <AlertDialogHeader>
        <AlertDialogTitle>
          {t("pages.rolesManagement.dialog.deleteTitle", "Delete role")}
        </AlertDialogTitle>
        <AlertDialogDescription>
          {t(
            "pages.rolesManagement.dialog.deleteMessage",
            'Are you sure you want to delete role "{{name}}"?',
            { name: roleName || "" }
          )}
        </AlertDialogDescription>
      </AlertDialogHeader>
      <AlertDialogFooter>
        <AlertDialogCancel disabled={isSubmitting}>
          {t("common.actions.cancel", "Cancel")}
        </AlertDialogCancel>
        <AlertDialogAction
          onClick={() => onConfirm?.()}
          disabled={isSubmitting}
          variant="destructive"
          aria-label={t("common.actions.delete", "Delete")}
        >
          {isSubmitting ? <Spinner className="size-4" /> : t("common.actions.delete", "Delete")}
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  );
}

export default DeleteRoleDialog;