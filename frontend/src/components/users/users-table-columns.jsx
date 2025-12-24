import * as React from "react";
import { format } from "date-fns";
import { useTranslation } from "react-i18next";
import { DataGridColumnHeader } from "@/components/data-grid/data-grid-column-header";
import { DataGridColumnFilter } from "@/components/data-grid/data-grid-column-filter";
import { DataGridTableRowSelect, DataGridTableRowSelectAll } from "@/components/data-grid/data-grid-table";
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
  Mail,
  Phone,
  Calendar,
  CircleUser,
  CirclePower,
  MoreHorizontal,
  Edit,
  Trash2,
  ShieldUser,
  Key,
} from "lucide-react";

/**
 * Generates column definitions for the users table
 * @param {Object} params - Configuration parameters
 * @param {Function} params.t - Translation function
 * @param {Function} params.handleEdit - Edit handler function
 * @param {Function} params.handleDelete - Delete handler function
 * @param {Function} params.handleResetPassword - Reset password handler function
 * @param {boolean} params.enableSelection - Whether selection mode is enabled
 * @param {Array} params.roles - List of roles
 * @param {boolean} params.canManageUsers - Whether user has manage-users permission
 * @returns {Array} Column definitions array
 */
export function useUsersTableColumns({ t, handleEdit, handleDelete, handleResetPassword, enableSelection, roles, canManageUsers = false }) {
  const { i18n } = useTranslation();

  return React.useMemo(
    () => {
      const baseColumns = [];

      // Add select column when selection mode is enabled
      if (enableSelection && canManageUsers) {
        baseColumns.push({
          id: "select",
          header: () => <DataGridTableRowSelectAll size="sm" className="justify-center" />,
          cell: ({ row }) => <DataGridTableRowSelect row={row} size="sm" className="justify-center" />,
          enableSorting: false,
          enableColumnFilter: false,
          enableResizing: false,
          enablePinning: true,
          size: 50,
          minSize: 50,
          maxSize: 50,
          meta: {
            headerClassName: "text-center [&:has([role=checkbox])]:pe-0",
            cellClassName: "!py-1 text-center justify-center",
          },
        });
      }

      baseColumns.push(
        {
          id: "first_name",
          accessorKey: "first_name",
          header: ({ column }) => (
            <DataGridColumnHeader
              column={column}
              title={t("pages.usersManagement.fields.firstName.label", "First Name")}
            />
          ),
          cell: ({ row }) => (
            <div className="font-medium">{row.getValue("first_name") || "-"}</div>
          ),
          enableSorting: true,
          enableColumnFilter: false,
          size: 150,
          minSize: 100,
          maxSize: 200,
        },
        {
          id: "last_name",
          accessorKey: "last_name",
          header: ({ column }) => (
            <DataGridColumnHeader
              column={column}
              title={t("pages.usersManagement.fields.lastName.label", "Last Name")}
            />
          ),
          cell: ({ row }) => (
            <div>{row.getValue("last_name") || "-"}</div>
          ),
          enableSorting: true,
          enableColumnFilter: false,
          size: 150,
          minSize: 100,
          maxSize: 200,
        },
        {
          id: "email",
          accessorKey: "email",
          header: ({ column }) => (
            <DataGridColumnHeader
              column={column}
              title={t("pages.usersManagement.fields.email.label", "Email")}
            />
          ),
          cell: ({ row }) => (
            <div>{row.getValue("email") || "-"}</div>
          ),
          enableSorting: true,
          enableColumnFilter: false,
          size: 250,
          minSize: 200,
          maxSize: 350,
        },
        {
          id: "phone",
          accessorKey: "phone",
          header: ({ column }) => (
            <DataGridColumnHeader
              column={column}
              title={t("pages.usersManagement.fields.phone.label", "Phone")}
            />
          ),
          cell: ({ row }) => (
            <div>{row.getValue("phone") || "-"}</div>
          ),
          enableSorting: true,
          enableColumnFilter: false,
          size: 130,
          minSize: 100,
          maxSize: 180,
        },
        {
          id: "role",
          accessorKey: "role",
          header: ({ column }) => (
            <DataGridColumnHeader
              column={column}
              title={t("pages.usersManagement.fields.role.label", "Role")}
              filter={
                roles.length > 0 ? (
                  <DataGridColumnFilter
                    column={column}
                    title={t("pages.usersManagement.fields.role.label", "Role")}
                    options={roles.map((role) => ({
                      value: role.name || role,
                      label: role.name || role,
                    }))}
                  />
                ) : undefined
              }
            />
          ),
          cell: ({ row }) => {
            const role = row.getValue("role");
            return (
              <div>{role || "-"}</div>
            );
          },
          enableSorting: true,
          filterFn: (row, id, value) => {
            const rowValue = row.getValue(id);
            if (!value || value.length === 0) return true;
            return value.includes(String(rowValue));
          },
          size: 120,
          minSize: 120,
          maxSize: 150,
        },
        {
          id: "status",
          accessorKey: "status",
          header: ({ column }) => {
            const statusFilterOptions = column.columnDef.meta?.filterOptions || [
              { value: "true", label: t("pages.usersManagement.fields.status.values.active", "Active") },
              { value: "false", label: t("pages.usersManagement.fields.status.values.inactive", "Inactive") },
            ];

            return (
              <DataGridColumnHeader
                column={column}
                title={t("pages.usersManagement.fields.status.label", "Status")}
                filter={
                  <DataGridColumnFilter
                    column={column}
                    title={t("pages.usersManagement.fields.status.label", "Status")}
                    options={statusFilterOptions}
                  />
                }
              />
            );
          },
          cell: ({ row }) => {
            const status = row.getValue("status");
            return (
              <Badge
                variant="outline"
                className={cn(
                  "px-3 py-1",
                  status
                    ? "bg-success/20 text-success border-success/35"
                    : "bg-destructive/20 text-destructive border-destructive/30"
                )}>
                {status ? (
                  <>
                    {t("pages.usersManagement.fields.status.values.active", "Active")}
                  </>
                ) : (
                  <>
                    {t("pages.usersManagement.fields.status.values.inactive", "Inactive")}
                  </>
                )}
              </Badge>
            );
          },
          enableSorting: true,
          filterFn: (row, id, value) => {
            const rowValue = row.getValue(id);
            return value.includes(String(rowValue));
          },
          size: 120,
          minSize: 100,
          maxSize: 150,
          meta: {
            cellClassName: "!py-1",
            filterOptions: [
              { value: "true", label: t("pages.usersManagement.fields.status.values.active", "Active") },
              { value: "false", label: t("pages.usersManagement.fields.status.values.inactive", "Inactive") },
            ],
          },
        },
        {
          id: "created_at",
          accessorKey: "created_at",
          header: ({ column }) => (
            <DataGridColumnHeader
              column={column}
              title={t("pages.usersManagement.fields.createdAt.label", "Created At")}
            />
          ),
          cell: ({ row }) => {
            const date = row.getValue("created_at");
            if (!date) return "-";
            try {
              const dateObj = new Date(date);
              const formatString = t("common.dateTime.format", "yyyy-MM-dd HH:mm");
              let formatted = format(dateObj, formatString);
              // Replace AM/PM with Chinese equivalents only for Chinese language
              if (i18n.language === "zh-TW") {
                formatted = formatted.replace(/AM/g, "上午").replace(/PM/g, "下午");
              }
              return formatted;
            } catch {
              return String(date);
            }
          },
          enableSorting: true,
          enableColumnFilter: false,
          size: 180,
          minSize: 150,
          maxSize: 220,
        },
      );

      if (canManageUsers) {
        baseColumns.push({
          id: "actions",
          header: () => <div className="w-full h-full" />,
          cell: ({ row }) => {
            const user = row.original;
            return (
              <div className="flex items-center justify-center">
                <DropdownMenu>
                  <DropdownMenuTrigger
                    asChild
                    className="shrink-0 justify-center">
                    <Button variant="ghost" size="icon" className="h-8 w-8 rounded-sm shrink-0">
                      <MoreHorizontal className="size-4" />
                      <span className="sr-only">{t("common.actions.openMenu", "Open menu")}</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-auto">
                    <DropdownMenuItem
                      className="flex items-center justify-between gap-8 rounded-xs"
                      onSelect={() => handleEdit(user)}>
                      {t("common.actions.edit", "Edit")}
                      <Edit className="size-4" />
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      className="flex items-center justify-between gap-8 rounded-xs"
                      onSelect={() => handleResetPassword(user)}>
                      {t("common.actions.resetPassword", "Reset Password")}
                      <Key className="size-4" />
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      variant="destructive"
                      className="flex items-center justify-between gap-8 rounded-xs"
                      onClick={() => handleDelete(user)}>
                      {t("common.actions.delete", "Delete")}
                      <Trash2 className="size-4" />
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            );
          },
          enableSorting: false,
          enableColumnFilter: false,
          enableResizing: false,
          enablePinning: true,
          size: 50,
          minSize: 50,
          maxSize: 50,
          meta: {
            cellClassName: "!py-1",
          },
        },
        );
      }
      return baseColumns;
    },
    [t, handleEdit, handleDelete, handleResetPassword, enableSelection, roles, i18n.language, canManageUsers]
  );
}