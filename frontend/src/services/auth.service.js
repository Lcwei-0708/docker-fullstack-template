import apiService from './api.service';
import i18n from '@/i18n';

const BASE_AUTH = '/auth';

export const authService = {
  // Register new user account
  register: (registerData, config = {}) => 
    apiService.post(`${BASE_AUTH}/register`, registerData, { 
      noToken: true, 
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.auth.register.messages.success', 'Registration successful'),
        409: i18n.t('pages.auth.register.messages.emailAlreadyExists', 'Email already exists'),
        ...config.messageMap,
      },
      ...config 
    }),

  // Login user
  login: (loginData, config = {}) => 
    apiService.post(`${BASE_AUTH}/login`, loginData, { 
      noToken: true, 
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.auth.login.messages.success', 'Sign in successful'),
        401: i18n.t('pages.auth.login.messages.invalidCredentials', 'Invalid email or password'),
        ...config.messageMap,
      },
      ...config 
    }),

  // Logout user
  logout: (logoutData = { logout_all: false }, config = {}) => 
    apiService.post(`${BASE_AUTH}/logout`, logoutData, {
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.auth.logout.messages.success', 'Signed out successfully'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Get token
  getToken: (config = {}) => 
    apiService.post(`${BASE_AUTH}/token`, {}, { 
      noToken: true, 
      showErrorToast: false,
      showSuccessToast: false,
      messageMap: {
        401: i18n.t('pages.auth.login.messages.invalidCredentials', 'Invalid email or password'),
        ...config.messageMap,
      },
      ...config 
    }),

  // Reset password
  resetPassword: (newPassword, resetToken, config = {}) => 
    apiService.post(`${BASE_AUTH}/reset-password`, { new_password: newPassword }, {
      headers: { Authorization: `Bearer ${resetToken}` },
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.auth.resetPassword.messages.success', 'Password reset successful'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Validate password reset token
  validateResetToken: (resetToken, config = {}) => 
    apiService.get(`${BASE_AUTH}/validate-reset-token`, {}, {
      headers: { Authorization: `Bearer ${resetToken}` },
      noToken: true,
      showErrorToast: false,
      showSuccessToast: false,
      messageMap: {
        success: i18n.t('pages.auth.validateResetToken.messages.success', 'Reset token is valid'),
        ...config.messageMap,
      },
      ...config,
    }),
};

export default authService;