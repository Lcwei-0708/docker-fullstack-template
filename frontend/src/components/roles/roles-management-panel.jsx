import * as React from "react";
import { rolesService } from "@/services/roles.service";
import { RolesList } from "./roles-list";
import { RoleDetails } from "./role-details";

export function RolesManagementPanel({ canManageRoles = false }) {
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
  const [editedRoleData, setEditedRoleData] = React.useState({
    name: "",
    description: "",
  });
  const initialAttributesRef = React.useRef({});
  const selectedRoleIdRef = React.useRef(null);
  const roleAttributesCacheRef = React.useRef(new Map());

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
      if (rolesList.length > 0 && !selectedRole) {
        setSelectedRole(rolesList[0]);
      }
    } else {
      setRoles([]);
      setFilteredRoles([]);
    }
    setIsLoading(false);
  }, [selectedRole, parseRolesList]);

  React.useEffect(() => {
    fetchRoles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
    const hasCached = roleAttributesCacheRef.current.has(roleId);
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
      roleAttributesCacheRef.current.set(roleId, { groups, attributes: flat });
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
      roleAttributesCacheRef.current.set(roleId, { groups: [], attributes: attrs });
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
      if (!hasCached) {
        setAttributes({});
        setAttributeGroups([]);
        initialAttributesRef.current = {};
        setHasChanges(false);
      }
      setIsLoadingAttributes(false);
    }
  }, []);

  // Load role details when selection changes.
  React.useEffect(() => {
    if (selectedRole?.id) {
      const cached = roleAttributesCacheRef.current.get(selectedRole.id);
      if (cached) {
        setAttributeGroups(cached.groups || []);
        setAttributes(cached.attributes || {});
        initialAttributesRef.current = { ...(cached.attributes || {}) };
        setHasChanges(false);
      }
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

  // Create a new role (legacy flow).
  const handleCreateRole = React.useCallback(async () => {
    if (!editedRoleData.name.trim()) return;

    const roleNameToSelect = editedRoleData.name;

    setIsSubmitting(true);
    const createResult = await rolesService.createRole(editedRoleData, { returnStatus: true });
    const createdPayload = createResult?.data || null;
    const newRole = createdPayload?.id ? createdPayload : null;

    const rolesResult = await rolesService.getAllRoles({ returnStatus: true });
    const rolesList = rolesResult.status === "success" ? parseRolesList(rolesResult.data) : [];

    setRoles(rolesList);
    setFilteredRoles(rolesList);

    if (newRole?.id) {
      setSelectedRole(newRole);
    } else {
      const foundRole = rolesList.find((r) => r.name === roleNameToSelect);
      if (foundRole) setSelectedRole(foundRole);
      else if (rolesList.length > 0) setSelectedRole(rolesList[0]);
    }

    setEditedRoleData({ name: "", description: "" });
    setIsEditingRole(false);
    setIsSubmitting(false);
  }, [editedRoleData, parseRolesList]);

  // Update the selected role (legacy flow).
  const handleUpdateRole = React.useCallback(async () => {
    if (!editedRoleData.name.trim()) return;

    if (!selectedRole?.id) {
      return;
    }

    setIsSubmitting(true);
    const result = await rolesService.updateRole(selectedRole.id, editedRoleData, { returnStatus: true });
    if (result.status === "success") {
      await fetchRoles();
      const updatedRole = roles.find((r) => r.id === selectedRole.id);
      if (updatedRole) setSelectedRole({ ...updatedRole, ...editedRoleData });
      setIsEditingRole(false);
    }
    setIsSubmitting(false);
  }, [selectedRole, editedRoleData, roles, fetchRoles]);

  // Save role (legacy flow).
  const handleSaveRole = React.useCallback(() => {
    if (selectedRole) {
      handleUpdateRole();
    } else {
      handleCreateRole();
    }
  }, [selectedRole, handleUpdateRole, handleCreateRole]);

  // Sync form data from the dialog.
  const handleRoleDataChangeFromDialog = React.useCallback((newData) => {
    setEditedRoleData(newData);
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

  return (
    <div className="flex h-auto gap-4 p-6 py-0">
      <RolesList
        roles={roles}
        filteredRoles={filteredRoles}
        selectedRole={selectedRole}
        isLoading={isLoading}
        searchKeyword={searchKeyword}
        canManageRoles={canManageRoles}
        onRoleSelect={setSelectedRole}
        onSearchChange={setSearchKeyword}
        onCreateClick={() => {
          setEditedRoleData({ name: "", description: "" });
          setIsEditingRole(true);
        }}
      />

      <RoleDetails
        selectedRole={selectedRole}
        isEditingRole={isEditingRole}
        editedRoleData={editedRoleData}
        attributes={attributes}
        attributeGroups={attributeGroups}
        isLoadingAttributes={isLoadingAttributes}
        hasChanges={hasChanges}
        isSubmitting={isSubmitting}
        canManageRoles={canManageRoles}
        onEditClick={() => {}}
        onDeleteClick={handleDeleteRole}
        onRoleDataChange={handleRoleDataChangeFromDialog}
        onAttributeToggle={handleAttributeToggle}
        onSaveRole={handleSaveRole}
        onSaveRoleFromDialog={handleSaveRoleFromDialog}
        onSaveAttributes={handleSaveAttributes}
        onResetAttributes={handleResetAttributes}
        onCancelEdit={handleCancelEdit}
      />
    </div>
  );
}

export default RolesManagementPanel;