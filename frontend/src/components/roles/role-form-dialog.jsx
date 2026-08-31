import * as React from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export function RoleFormDialog({
  open,
  mode = "edit", // "create" | "edit"
  isSubmitting = false,
  onOpenChange,
  onCancel,
  onSubmit,
  initialData,
  maxLevel = 99,
}) {
  const { t } = useTranslation();
  const isCreate = mode === "create";
  const maxAssignableLevel = Math.max(0, Number(maxLevel));
  const defaultLevel = Math.min(1, maxAssignableLevel);
  const [formData, setFormData] = React.useState({
    name: "",
    description: "",
    level: defaultLevel,
  });
  const [levelError, setLevelError] = React.useState("");

  React.useEffect(() => {
    if (!open) return;
    const nextDefaultLevel = Math.min(1, Math.max(0, Number(maxLevel)));
    setFormData({
      name: initialData?.name ?? "",
      description: initialData?.description ?? "",
      level:
        initialData?.level !== undefined && initialData?.level !== null
          ? Number(initialData.level)
          : nextDefaultLevel,
    });
    setLevelError("");
  }, [open, initialData?.name, initialData?.description, initialData?.level, maxLevel]);

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

  const validateAndSubmit = React.useCallback(() => {
    if (!formData?.name?.trim()) return;
    const level = Number(formData.level);
    if (!Number.isInteger(level) || level < 1) {
      setLevelError(
        t("pages.rolesManagement.fields.level.validation.min", "Level must be at least 1")
      );
      return;
    }
    if (level > maxAssignableLevel) {
      setLevelError(
        t(
          "pages.rolesManagement.fields.level.validation.max",
          "Level cannot exceed your own (max {{max}})",
          { max: maxAssignableLevel }
        )
      );
      return;
    }
    setLevelError("");
    onSubmit?.({
      ...formData,
      name: formData.name.trim(),
      description: formData.description?.trim() || "",
      level,
    });
  }, [formData, onSubmit, maxAssignableLevel, t]);

  const handleSubmit = React.useCallback(() => {
    validateAndSubmit();
  }, [validateAndSubmit]);

  const handleInputEnterSubmit = React.useCallback(
    (e) => {
      if (e.key !== "Enter") return;
      // Do not submit while IME is composing.
      if (e.nativeEvent?.isComposing) return;
      e.preventDefault();
      e.stopPropagation();
      if (isSubmitting || !formData?.name?.trim()) return;
      validateAndSubmit();
    },
    [formData, isSubmitting, validateAndSubmit]
  );

  const canSubmit = !isSubmitting && !!formData?.name?.trim() && maxAssignableLevel >= 1;

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
            <label htmlFor="role-name" className="text-sm font-medium mb-2 block">
              {t("pages.rolesManagement.fields.name.label", "Role name")}
              <span className="text-destructive ml-1">*</span>
            </label>
            <Input
              id="role-name"
              name="role-name"
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
            <label htmlFor="role-description" className="text-sm font-medium mb-2 block">
              {t("pages.rolesManagement.fields.description.label", "Description")}
              <span className="text-destructive ml-1">*</span>
            </label>
            <Input
              id="role-description"
              name="role-description"
              value={formData?.description ?? ""}
              onKeyDown={handleInputEnterSubmit}
              onChange={(e) =>
                setFormData((prev) => ({
                  ...(prev || {}),
                  description: e.target.value,
                }))
              }
              placeholder={t(
                "pages.rolesManagement.fields.description.placeholder",
                "Enter description"
              )}
            />
          </div>

          <div>
            <label htmlFor="role-level" className="text-sm font-medium mb-2 block">
              {t("pages.rolesManagement.fields.level.label", "Level")}
              <span className="text-destructive ml-1">*</span>
            </label>
            <Input
              id="role-level"
              name="role-level"
              type="number"
              min={1}
              max={maxAssignableLevel}
              value={formData?.level ?? ""}
              onKeyDown={handleInputEnterSubmit}
              onChange={(e) => {
                setLevelError("");
                setFormData((prev) => ({
                  ...(prev || {}),
                  level: e.target.value === "" ? "" : Number(e.target.value),
                }));
              }}
              placeholder={t("pages.rolesManagement.fields.level.placeholder", "Enter level")}
            />
            <p className="text-xs text-muted-foreground mt-1.5">
              {t(
                "pages.rolesManagement.fields.level.hint",
                "Higher number means higher privilege. Max allowed: {{max}}",
                { max: maxAssignableLevel }
              )}
            </p>
            {levelError ? <p className="text-xs text-destructive mt-1">{levelError}</p> : null}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel} disabled={isSubmitting}>
            {t("common.actions.cancel", "Cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="bg-primary hover:bg-primary/90"
          >
            {isSubmitting ? (
              <span className="inline-flex items-center gap-2">
                <Spinner className="size-4" />
              </span>
            ) : (
              <>
                {isCreate ? t("common.actions.create", "Create") : t("common.actions.save", "Save")}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default RoleFormDialog;
