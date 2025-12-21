import apiService from './api.service';
import i18n from '@/i18n';

const USERS_BASE = '/users';

export const usersService = {
  // Get all users with pagination and filters
  getAllUsers: (params = {}, config = {}) => 
    apiService.get(USERS_BASE, params, {
      showErrorToast: true,
      showSuccessToast: false,
      messageMap: {
        success: i18n.t('pages.admin.users.messages.getAllUsers.success', 'Users retrieved successfully'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Create user
  createUser: (userData, config = {}) => 
    apiService.post(USERS_BASE, userData, {
      showErrorToast: true,
      messageMap: {
        success: i18n.t('pages.admin.users.messages.createUser.success', 'User created successfully'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Update user
  updateUser: (userId, userData, config = {}) => 
    apiService.put(`${USERS_BASE}/${userId}`, userData, {
      showErrorToast: true,
      messageMap: {
        success: i18n.t('pages.admin.users.messages.updateUser.success', 'User updated successfully'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Delete users (batch)
  deleteUsers: (userIds, config = {}) => 
    apiService.delete(USERS_BASE, {
      showErrorToast: true,
      messageMap: {
        success: i18n.t('pages.admin.users.messages.deleteUsers.success', 'Users deleted successfully'),
        ...config.messageMap,
      },
      data: { user_ids: userIds },
      ...config,
    }),

  // Reset user password
  resetUserPassword: (userId, newPassword, config = {}) => 
    apiService.post(
      `${USERS_BASE}/${userId}/reset-password`,
      { new_password: newPassword },
      {
        showErrorToast: true,
        messageMap: {
          success: i18n.t('pages.admin.users.messages.resetUserPassword.success', 'User password reset successfully'),
          ...config.messageMap,
        },
        ...config,
      }
    ),
};

export default usersService;