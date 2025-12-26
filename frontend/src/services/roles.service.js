import apiService from './api.service';
import i18n from '@/i18n';

const ROLES_BASE = '/roles';

export const rolesService = {
  // Get all roles
  getAllRoles: (config = {}) => 
    apiService.get(`${ROLES_BASE}/`, {}, {
      showErrorToast: true,
      showSuccessToast: false,
      messageMap: {
        success: i18n.t('pages.rolesManagement.messages.getAllRoles.success', 'Roles retrieved successfully'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Create role
  createRole: (roleData, config = {}) => 
    apiService.post(`${ROLES_BASE}/`, roleData, {
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.rolesManagement.messages.createRole.success', 'Role created successfully'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Update role
  updateRole: (roleId, roleData, config = {}) => 
    apiService.put(`${ROLES_BASE}/${roleId}`, roleData, {
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.rolesManagement.messages.updateRole.success', 'Role updated successfully'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Delete role
  deleteRole: (roleId, config = {}) => 
    apiService.delete(`${ROLES_BASE}/${roleId}`, {
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.rolesManagement.messages.deleteRole.success', 'Role deleted successfully'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Get role attributes
  getRoleAttributes: (roleId, config = {}) => 
    apiService.get(`${ROLES_BASE}/${roleId}/attributes`, {
      showErrorToast: true,
      showSuccessToast: false,
      messageMap: {
        success: i18n.t('pages.rolesManagement.messages.getRoleAttributes.success', 'Role attributes retrieved successfully'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Update role attributes
  updateRoleAttributes: (roleId, attributesData, config = {}) => 
    apiService.put(`${ROLES_BASE}/${roleId}/attributes`, attributesData, {
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.rolesManagement.messages.updateRoleAttributes.success', 'Role attributes updated successfully'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Get all user permissions (based on token)
  getAllUserPermissions: (config = {}) => 
    apiService.get(`${ROLES_BASE}/permissions`, {}, {
      showErrorToast: true,
      showSuccessToast: false,
      messageMap: {
        success: i18n.t('pages.rolesManagement.messages.getAllUserPermissions.success', 'User permissions retrieved successfully'),
        ...config.messageMap,
      },
      ...config,
    }, config),
};

export default rolesService;