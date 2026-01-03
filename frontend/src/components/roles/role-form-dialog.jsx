import * as React from "react"
import { useTranslation } from "react-i18next"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Spinner } from "@/components/ui/spinner"
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle
} from "@/components/ui/dialog"

export function RoleFormDialog({
  open,
  mode = "edit", // "create" | "edit"
  isSubmitting = false,
  onOpenChange,
  onCancel,
  onSubmit,
  initialData,
}) {
  const { t } = useTranslation();
  const isCreate = mode === "create";
  const [formData, setFormData] = React.useState({ name: "", description: "" });

  React.useEffect(() => {
    if (!open) return;
    setFormData({
      name: initialData?.name ?? "",
      description: initialData?.description ?? "",
    });
  }, [open, initialData?.name, initialData?.description]);

  const handleOpenChange = React.useCallback(
    (nextOpen) => {
      onOpenChange?.(nextOpen);
      // Treat close as cancel.
      if (!nextOpen) {
        onCancel?.();
      }
    },
    [onOpenChange, onCancel]
  );

  const handleSubmit = React.useCallback(() => {
    if (!formData?.name?.trim()) return;
    onSubmit?.(formData);
  }, [formData, onSubmit]);

  const handleInputEnterSubmit = React.useCallback(
    (e) => {
      if (e.key !== "Enter") return;
      // Do not submit while IME is composing.
      if (e.nativeEvent?.isComposing) return;
      e.preventDefault();
      e.stopPropagation();
      if (isSubmitting || !formData?.name?.trim()) return;
      onSubmit?.(formData);
    },
    [formData, onSubmit, isSubmitting]
  );

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent showCloseButton={false} className="max-w-lg">
        <DialogHeader>
          <DialogTitle>
            {isCreate 
            ? t("pages.rolesManagement.dialog.createTitle", "Create role") 
            : t("pages.rolesManagement.dialog.editTitle", "Edit role")}
          </DialogTitle>
          <DialogDescription>
            {isCreate 
            ? t("pages.rolesManagement.dialog.createDescription", "Create a new role") 
            : t("pages.rolesManagement.dialog.editDescription", "Update role info")}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5">
          <div>
            <label className="text-sm font-medium mb-2 block">
              {t("pages.rolesManagement.fields.name.label", "Role name")}
              <span className="text-destructive ml-1">*</span>
            </label>
            <Input
              value={formData?.name ?? ""}
              onKeyDown={handleInputEnterSubmit}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...(prev || {}),
                  name: e.target.value,
                }))
              }
              placeholder={t("pages.rolesManagement.fields.name.placeholder", "Enter role name")}
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-2 block">
              {t("pages.rolesManagement.fields.description.label", "Description")}
              <span className="text-destructive ml-1">*</span>
            </label>
            <Input
              value={formData?.description ?? ""}
              onKeyDown={handleInputEnterSubmit}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...(prev || {}),
                  description: e.target.value,
                }))
              }
              placeholder={t("pages.rolesManagement.fields.description.placeholder", "Enter description")}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel} disabled={isSubmitting}>
            {t("common.actions.cancel", "Cancel")}
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting || !formData?.name?.trim()} className="bg-primary hover:bg-primary/90">
            {isSubmitting ? (
              <span className="inline-flex items-center gap-2">
                <Spinner className="size-4" />
              </span>
            ) : (
              <>{isCreate ? t("common.actions.create", "Create") : t("common.actions.save", "Save")}</>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default RoleFormDialog;