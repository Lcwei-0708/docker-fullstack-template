import apiService from './api.service';
import i18n from '@/i18n';

// API endpoints for account
const BASE_ACCOUNT = '/account';

export const accountService = {
  // Get user profile
  getProfile: (config = {}) => 
    apiService.get(`${BASE_ACCOUNT}/profile`, {}, {
      showErrorToast: false,
      showSuccessToast: false,
      messageMap: {
        success: i18n.t('profile.messages.getProfile.success'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Update user profile
  updateProfile: (profileData, config = {}) => 
    apiService.put(`${BASE_ACCOUNT}/profile`, profileData, {
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('profile.updateProfile.messages.success'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Change password
  changePassword: (passwordData, config = {}) => 
    apiService.put(`${BASE_ACCOUNT}/password`, passwordData, {
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('profile.changePassword.messages.success'),
        incorrect: i18n.t('profile.changePassword.messages.incorrect'),
        ...config.messageMap,
      },
      ...config,
    }),
};

export default accountService;