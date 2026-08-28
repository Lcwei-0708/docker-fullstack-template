import apiService from './api.service';
import i18n from '@/i18n';

const USERS_BASE = '/users';

const resolveUsersForbiddenMessage = (error, {
  ownRoleKey,
  ownRoleDefault,
  levelKey,
  levelDefault,
}) => {
  const backendMessage = (error?.response?.data?.message || '').toLowerCase();
  if (backendMessage.includes('own role')) {
    return i18n.t(ownRoleKey, ownRoleDefault);
  }
  return i18n.t(levelKey, levelDefault);
};

export const usersService = {
  // Get all users with pagination and filters
  getAllUsers: (params = {}, config = {}) => 
    apiService.get(`${USERS_BASE}`, params, {
      showErrorToast: true,
      showSuccessToast: false,
      messageMap: {
        success: i18n.t('pages.usersManagement.messages.getAllUsers.success', 'Users retrieved successfully'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Create user
  createUser: (userData, config = {}) => 
    apiService.post(`${USERS_BASE}`, userData, {
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.usersManagement.messages.createUser.success', 'User created successfully'),
        409: i18n.t('pages.usersManagement.messages.createUser.emailAlreadyExists', 'Email already exists'),
        403: i18n.t(
          'pages.usersManagement.messages.createUser.levelTooHigh',
          'Cannot assign a role with a higher level than your own'
        ),
        ...config.messageMap,
      },
      ...config,
    }),

  // Update user
  updateUser: (userId, userData, config = {}) => 
    apiService.put(`${USERS_BASE}/${userId}`, userData, {
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.usersManagement.messages.updateUser.success', 'User updated successfully'),
        404: i18n.t('pages.usersManagement.messages.updateUser.userNotFound', 'User not found'),
        409: i18n.t('pages.usersManagement.messages.createUser.emailAlreadyExists', 'Email already exists'),
        403: (error) =>
          resolveUsersForbiddenMessage(error, {
            ownRoleKey: 'pages.usersManagement.messages.updateUser.cannotChangeOwnRole',
            ownRoleDefault: 'Cannot change your own role',
            levelKey: 'pages.usersManagement.messages.updateUser.levelTooHigh',
            levelDefault: 'Cannot manage a user with a higher role level than your own',
          }),
        ...config.messageMap,
      },
      ...config,
    }),

  // Delete users (batch)
  deleteUsers: (userIds, config = {}) => 
    apiService.delete(`${USERS_BASE}`, {
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.usersManagement.messages.deleteUsers.success', 'Users deleted successfully'),
        404: i18n.t('pages.usersManagement.messages.deleteUsers.userNotFound', 'User not found'),
        403: i18n.t(
          'pages.usersManagement.messages.deleteUsers.levelTooHigh',
          'Cannot delete a user with a higher role level than your own'
        ),
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
        showSuccessToast: true,
        messageMap: {
          success: i18n.t('pages.usersManagement.messages.resetUserPassword.success', 'User password reset successfully'),
          404: i18n.t('pages.usersManagement.messages.resetUserPassword.userNotFound', 'User not found'),
          ...config.messageMap,
        },
        ...config,
      }
    ),
};

export default usersService;
