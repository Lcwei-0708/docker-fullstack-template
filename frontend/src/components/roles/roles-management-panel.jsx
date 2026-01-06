import * as React from "react";
import { rolesService } from "@/services/roles.service";
import { useIsMobile } from "@/hooks/useMobile";
import { RolesList } from "./roles-list";
import { RolePermissionsDesktop } from "./role-permissions-desktop";
import { RoleSelector } from "./role-selector";
import { RoleFormDialog } from "@/components/roles/role-form-dialog";
import { RolePermissionsMobile } from "./role-permissions-mobile";
import { AlertDialog } from "@/components/ui/alert-dialog";
import { DeleteRoleDialog } from "@/components/roles/delete-role-dialog";

export const RolesManagementPanel = React.forwardRef(function RolesManagementPanel({ canManageRoles = false }, ref) {
  const isMobile = useIsMobile();
  const [roles, setRoles] = React.useState([]);
  const [filteredRoles, setFilteredRoles] = React.useState([]);
  const [selectedRole, setSelectedRole] = React.useState(null);
  const [attributes, setAttributes] = React.useState({});
  const [attributeGroups, setAttributeGroups] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [isLoadingAttributes, setIsLoadingAttributes] = React.useState(false);
  const [searchKeyword, setSearchKeyword] = React.useState("");
  const [hasChanges, setHasChanges] = React.useState(false);
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [isEditingRole, setIsEditingRole] = React.useState(false);
  const [isRoleDialogOpen, setIsRoleDialogOpen] = React.useState(false);
  const [isRoleEditDialogOpen, setIsRoleEditDialogOpen] = React.useState(false);
  const [isRoleDeleteDialogOpen, setIsRoleDeleteDialogOpen] = React.useState(false);
  const [editedRoleData, setEditedRoleData] = React.useState({
    name: "",
    description: "",
  });
  const initialAttributesRef = React.useRef({});
  const hasFetchedRolesRef = React.useRef(false);
  const selectedRoleIdRef = React.useRef(null);

  React.useImperativeHandle(
    ref,
    () => ({
      handleCreate: () => {
        setSelectedRole(null);
        setEditedRoleData({ name: "", description: "" });
        setIsEditingRole(true);
        setIsRoleDialogOpen(true);
      },
    }),
    []
  );

  React.useEffect(() => {
    selectedRoleIdRef.current = selectedRole?.id ?? null;
  }, [selectedRole?.id]);

  const parseRolesList = React.useCallback((response) => {
    if (!response) return [];
    if (Array.isArray(response)) return response;
    if (response.roles && Array.isArray(response.roles)) return response.roles;
    if (response.data) {
      if (Array.isArray(response.data)) return response.data;
      if (response.data.roles && Array.isArray(response.data.roles)) return response.data.roles;
    }
    return [];
  }, []);

  // Load roles list.
  const fetchRoles = React.useCallback(async () => {
    setIsLoading(true);
    const result = await rolesService.getAllRoles({ returnStatus: true });
    let rolesList = [];
    if (result.status === "success") {
      rolesList = parseRolesList(result.data);
      setRoles(rolesList);
      setFilteredRoles(rolesList);

      // Pick a default role for the details panel.
      if (rolesList.length > 0 && !selectedRoleIdRef.current) {
        setSelectedRole(rolesList[0]);
      }
    } else {
      setRoles([]);
      setFilteredRoles([]);
    }
    setIsLoading(false);
  }, [parseRolesList]);

  React.useEffect(() => {
    if (hasFetchedRolesRef.current) return;
    hasFetchedRolesRef.current = true;
    fetchRoles();
  }, [fetchRoles]);

  // Filter roles by keyword.
  React.useEffect(() => {
    if (!searchKeyword.trim()) {
      setFilteredRoles(roles);
    } else {
      const keyword = searchKeyword.toLowerCase();
      const filtered = roles.filter((role) => role.name?.toLowerCase().includes(keyword) || role.description?.toLowerCase().includes(keyword));
      setFilteredRoles(filtered);
    }
  }, [searchKeyword, roles]);

  const fetchRoleAttributes = React.useCallback(async (roleId) => {
    if (!roleId) return;
    setIsLoadingAttributes(true);
    const result = await rolesService.getRoleAttributes(roleId, { returnStatus: true });
    const payload = result?.data || {};
    const groups = payload?.groups || [];

    // Support grouped permissions from the new API.
    if (result.status === "success" && Array.isArray(groups) && groups.length > 0) {
      const flat = {};
      groups.forEach((g) => {
        const categories = g?.categories || {};
        Object.keys(categories).forEach((categoryName) => {
          const list = categories?.[categoryName] || [];
          if (!Array.isArray(list)) return;
          list.forEach((attr) => {
            if (!attr?.name) return;
            flat[attr.name] = !!attr.value;
          });
        });
      });
      if (selectedRoleIdRef.current === roleId) {
        setAttributeGroups(groups);
        setAttributes(flat);
        initialAttributesRef.current = { ...flat };
        setHasChanges(false);
        setIsLoadingAttributes(false);
      }
      return;
    }

    if (result.status === "success") {
      // Support flat permissions from the legacy API.
      const attrs = payload?.attributes || {};
      if (selectedRoleIdRef.current === roleId) {
        setAttributeGroups([]);
        setAttributes(attrs);
        initialAttributesRef.current = { ...attrs };
        setHasChanges(false);
        setIsLoadingAttributes(false);
      }
      return;
    }

    // Reset on error.
    if (selectedRoleIdRef.current === roleId) {
      setAttributes({});
      setAttributeGroups([]);
      initialAttributesRef.current = {};
      setHasChanges(false);
      setIsLoadingAttributes(false);
    }
  }, []);

  // Load role details when selection changes.
  React.useEffect(() => {
    if (selectedRole?.id) {
      setIsLoadingAttributes(true);
      fetchRoleAttributes(selectedRole.id);
      setEditedRoleData({
        name: selectedRole.name || "",
        description: selectedRole.description || "",
      });
      setIsEditingRole(false);
    } else {
      setAttributes({});
      setAttributeGroups([]);
      initialAttributesRef.current = {};
      setHasChanges(false);
      setEditedRoleData({ name: "", description: "" });
    }
  }, [selectedRole?.id, selectedRole?.name, selectedRole?.description, fetchRoleAttributes]);

  React.useEffect(() => {
    if (!canManageRoles) return;
    if (isMobile && isEditingRole) setIsRoleDialogOpen(true);
  }, [isMobile, isEditingRole, canManageRoles]);

  React.useEffect(() => {
    if (!isMobile) return;
    setIsRoleEditDialogOpen(false);
    setIsRoleDeleteDialogOpen(false);
  }, [isMobile, selectedRole?.id]);

  // Toggle a single permission.
  const handleAttributeToggle = React.useCallback((attributeName) => {
    setAttributes((prev) => {
      const newAttributes = {
        ...prev,
        [attributeName]: !prev[attributeName],
      };
      const hasChanged = JSON.stringify(newAttributes) !== JSON.stringify(initialAttributesRef.current);
      setHasChanges(hasChanged);
      return newAttributes;
    });
  }, []);

  // Save permissions.
  const handleSaveAttributes = React.useCallback(async () => {
    if (!selectedRole?.id) return;
    setIsSubmitting(true);
    const result = await rolesService.updateRoleAttributes(selectedRole.id, { attributes }, { returnStatus: true });
    if (result.status === "success") {
      initialAttributesRef.current = { ...attributes };
      setHasChanges(false);
    }
    setIsSubmitting(false);
  }, [selectedRole?.id, attributes]);

  // Reset permissions to the last snapshot.
  const handleResetAttributes = React.useCallback(() => {
    const snapshot = initialAttributesRef.current || {};
    setAttributes({ ...snapshot });
    setHasChanges(false);
  }, []);

  // Save role from the dialog (create or edit).
  const handleSaveRoleFromDialog = React.useCallback(
    async (roleId, roleData) => {
      if (!roleData?.name?.trim()) return;

      setIsSubmitting(true);
      try {
        let createdOrUpdatedRoleId = roleId || null;
        if (createdOrUpdatedRoleId) {
          const updateResult = await rolesService.updateRole(createdOrUpdatedRoleId, roleData, { returnStatus: true });
          if (updateResult.status !== "success") {
            return false;
          }
        } else {
          const createResult = await rolesService.createRole(roleData, { returnStatus: true });
          const createdRole = createResult?.data?.id ? createResult.data : null;
          createdOrUpdatedRoleId = createdRole?.id || null;
          if (createResult.status !== "success") {
            return false;
          }
        }

        const rolesResult = await rolesService.getAllRoles({ returnStatus: true });
        const rolesList = rolesResult.status === "success" ? parseRolesList(rolesResult.data) : [];
        setRoles(rolesList);
        setFilteredRoles(rolesList);

        if (createdOrUpdatedRoleId) {
          const found = rolesList.find((r) => r.id === createdOrUpdatedRoleId);
          if (found) setSelectedRole(found);
        } else {
          const found = rolesList.find((r) => r.name === roleData.name);
          if (found) setSelectedRole(found);
        }

        if (!roleId) {
          setIsEditingRole(false);
          setEditedRoleData({ name: "", description: "" });
        }

        return true;
      } finally {
        setIsSubmitting(false);
      }
    },
    [parseRolesList]
  );

  // Delete the selected role.
  const handleDeleteRole = React.useCallback(async () => {
    if (!selectedRole?.name || !selectedRole?.id) {
      return;
    }

    setIsSubmitting(true);
    const result = await rolesService.deleteRole(selectedRole.id, { returnStatus: true });
    if (result.status === "success") {
      setSelectedRole(null);
      await fetchRoles();
    }
    setIsSubmitting(false);
  }, [selectedRole, fetchRoles]);

  // Exit create/edit mode.
  const handleCancelEdit = React.useCallback(() => {
    setIsEditingRole(false);
    if (selectedRole) {
      setEditedRoleData({
        name: selectedRole.name || "",
        description: selectedRole.description || "",
      });
    } else {
      setEditedRoleData({ name: "", description: "" });
    }
  }, [selectedRole]);

  const handleRoleSelect = React.useCallback(
    (role) => {
      setSelectedRole(role);
    },
    []
  );

  if (isMobile) {
    return (
      <div className="flex h-full flex-col gap-3">
        <RoleSelector
          filteredRoles={filteredRoles}
          selectedRole={selectedRole}
          isLoading={isLoading}
          searchKeyword={searchKeyword}
          disabled={isSubmitting}
          canManageRoles={canManageRoles}
          isSubmitting={isSubmitting}
          onRoleSelect={handleRoleSelect}
          onSearchChange={setSearchKeyword}
          onEditClick={() => {
            if (!selectedRole?.id) return;
            setIsRoleEditDialogOpen(true);
          }}
          onDeleteClick={() => {
            if (!selectedRole?.id) return;
            setIsRoleDeleteDialogOpen(true);
          }}
        />

        <RolePermissionsMobile
          selectedRole={selectedRole}
          attributes={attributes}
          attributeGroups={attributeGroups}
          isLoadingAttributes={isLoadingAttributes}
          hasChanges={hasChanges}
          isSubmitting={isSubmitting}
          canManageRoles={canManageRoles}
          onAttributeToggle={handleAttributeToggle}
          onSaveAttributes={handleSaveAttributes}
          onResetAttributes={handleResetAttributes}
        />

        {/* Mobile role dialog (create) */}
        <RoleFormDialog
          open={isRoleDialogOpen}
          mode="create"
          isSubmitting={isSubmitting}
          onOpenChange={(open) => {
            setIsRoleDialogOpen(open);
            if (!open) handleCancelEdit();
          }}
          initialData={{
            name: editedRoleData?.name || "",
            description: editedRoleData?.description || "",
          }}
          onCancel={() => {
            handleCancelEdit();
            setIsRoleDialogOpen(false);
          }}
          onSubmit={async (data) => {
            if (!data?.name?.trim()) return;
            const ok = await handleSaveRoleFromDialog(null, data);
            if (ok !== false) {
              handleCancelEdit();
              setIsRoleDialogOpen(false);
            }
          }}
        />

        <RoleFormDialog
          open={isRoleEditDialogOpen}
          mode="edit"
          isSubmitting={isSubmitting}
          onOpenChange={setIsRoleEditDialogOpen}
          initialData={{
            name: selectedRole?.name || "",
            description: selectedRole?.description || "",
          }}
          onCancel={() => setIsRoleEditDialogOpen(false)}
          onSubmit={async (data) => {
            if (!selectedRole?.id) return;
            if (!data?.name?.trim()) return;
            const ok = await handleSaveRoleFromDialog(selectedRole.id, data);
            if (ok !== false) setIsRoleEditDialogOpen(false);
          }}
        />

        <AlertDialog open={isRoleDeleteDialogOpen} onOpenChange={setIsRoleDeleteDialogOpen}>
          <DeleteRoleDialog
            roleName={selectedRole?.name || ""}
            isSubmitting={isSubmitting}
            onConfirm={async () => {
              await handleDeleteRole();
              setIsRoleDeleteDialogOpen(false);
            }}
          />
        </AlertDialog>
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 gap-4 items-stretch">
      <RolesList
        roles={roles}
        filteredRoles={filteredRoles}
        selectedRole={selectedRole}
        isLoading={isLoading}
        searchKeyword={searchKeyword}
        canManageRoles={canManageRoles}
        isSubmitting={isSubmitting}
        className="w-1/3 h-full"
        onRoleSelect={handleRoleSelect}
        onSearchChange={setSearchKeyword}
        onCreateClick={() => {
          if (!canManageRoles) return;
          setSelectedRole(null);
          setEditedRoleData({ name: "", description: "" });
          setIsEditingRole(true);
          setIsRoleDialogOpen(true);
        }}
        onEditClick={(role) => {
          if (!canManageRoles || isSubmitting) return;
          if (!role?.id) return;
          setSelectedRole(role);
          setIsRoleEditDialogOpen(true);
        }}
        onDeleteClick={(role) => {
          if (!canManageRoles || isSubmitting) return;
          if (!role?.id) return;
          setSelectedRole(role);
          setIsRoleDeleteDialogOpen(true);
        }}
      />

      <RolePermissionsDesktop
        selectedRole={selectedRole}
        attributes={attributes}
        attributeGroups={attributeGroups}
        isLoadingAttributes={isLoadingAttributes}
        isLoadingRoles={isLoading}
        hasChanges={hasChanges}
        isSubmitting={isSubmitting}
        canManageRoles={canManageRoles}
        onAttributeToggle={handleAttributeToggle}
        onSaveAttributes={handleSaveAttributes}
        onResetAttributes={handleResetAttributes}
      />
      <RoleFormDialog
        open={isRoleDialogOpen}
        mode="create"
        isSubmitting={isSubmitting}
        onOpenChange={(open) => {
          setIsRoleDialogOpen(open);
          if (!open) handleCancelEdit();
        }}
        initialData={{
          name: editedRoleData?.name || "",
          description: editedRoleData?.description || "",
        }}
        onCancel={() => {
          handleCancelEdit();
          setIsRoleDialogOpen(false);
        }}
        onSubmit={async (data) => {
          if (!data?.name?.trim()) return;
          const ok = await handleSaveRoleFromDialog(null, data);
          if (ok !== false) {
            handleCancelEdit();
            setIsRoleDialogOpen(false);
          }
        }}
      />

      <RoleFormDialog
        open={isRoleEditDialogOpen}
        mode="edit"
        isSubmitting={isSubmitting}
        onOpenChange={setIsRoleEditDialogOpen}
        initialData={{
          name: selectedRole?.name || "",
          description: selectedRole?.description || "",
        }}
        onCancel={() => setIsRoleEditDialogOpen(false)}
        onSubmit={async (data) => {
          if (!selectedRole?.id) return;
          if (!data?.name?.trim()) return;
          const ok = await handleSaveRoleFromDialog(selectedRole.id, data);
          if (ok !== false) setIsRoleEditDialogOpen(false);
        }}
      />

      <AlertDialog open={isRoleDeleteDialogOpen} onOpenChange={setIsRoleDeleteDialogOpen}>
        <DeleteRoleDialog
          roleName={selectedRole?.name || ""}
          isSubmitting={isSubmitting}
          onConfirm={async () => {
            await handleDeleteRole();
            setIsRoleDeleteDialogOpen(false);
          }}
        />
      </AlertDialog>
    </div>
  );
});

export default RolesManagementPanel;