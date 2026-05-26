import apiService from './api.service';
import i18n from '@/i18n';
import { getCsrfTokenFromCookie } from '@/lib/cookies';

const BASE_AUTH = '/auth';

export const authService = {
  // Register new user account
  register: (registerData, config = {}) => 
    apiService.post(`${BASE_AUTH}/register`, registerData, { 
      noToken: true,
      retryOn401: false,
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
      retryOn401: false,
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

  // Get CSRF token (session cookie required)
  getCsrfToken: (config = {}) =>
    apiService.post(`${BASE_AUTH}/csrf-token`, {}, {
      noToken: true,
      retryOn401: false,
      showErrorToast: false,
      showSuccessToast: false,
      ...config,
    }),

  // Get token (requires session_id cookie and X-CSRF-Token header)
  getToken: (config = {}) => {
    const { csrfToken, ...restConfig } = config;
    const headers = {
      ...(restConfig.headers || {}),
      'X-CSRF-Token': csrfToken ?? getCsrfTokenFromCookie() ?? '',
    };

    return apiService.post(`${BASE_AUTH}/token`, {}, {
      noToken: true,
      retryOn401: false,
      showErrorToast: false,
      showSuccessToast: false,
      messageMap: {
        401: i18n.t('pages.auth.login.messages.invalidCredentials', 'Invalid email or password'),
        ...restConfig.messageMap,
      },
      headers,
      ...restConfig,
    });
  },

  // Reset password
  resetPassword: (newPassword, resetToken, config = {}) => 
    apiService.post(`${BASE_AUTH}/reset-password`, { new_password: newPassword }, {
      headers: { Authorization: `Bearer ${resetToken}` },
      noToken: true,
      retryOn401: false,
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.auth.resetPassword.messages.success', 'Password reset successful'),
        401: i18n.t('pages.auth.resetPassword.messages.invalidToken', 'The reset password link has expired or is invalid. Please request a new one.'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Validate password reset token
  validateResetToken: (resetToken, config = {}) => 
    apiService.get(`${BASE_AUTH}/validate-reset-token`, {}, {
      headers: { Authorization: `Bearer ${resetToken}` },
      noToken: true,
      retryOn401: false,
      showErrorToast: false,
      showSuccessToast: false,
      messageMap: {
        success: i18n.t('pages.auth.validateResetToken.messages.success', 'Reset token is valid'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Forgot password - send reset email
  forgotPassword: (email, config = {}) => 
    apiService.post(`${BASE_AUTH}/forgot-password`, { email }, {
      noToken: true,
      retryOn401: false,
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.auth.forgotPassword.messages.success', 'Password reset email sent'),
        400: i18n.t('pages.auth.forgotPassword.messages.cooldown', 'Please wait before requesting another password reset email'),
        403: i18n.t('pages.auth.forgotPassword.messages.accountDisabled', 'Account is disabled'),
        404: i18n.t('pages.auth.forgotPassword.messages.emailNotRegistered', 'This email is not registered'),
        503: i18n.t('pages.auth.forgotPassword.messages.smtpDisabled', 'SMTP is disabled'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Get password reset cooldown status
  getPasswordResetCooldown: (email, config = {}) => 
    apiService.get(`${BASE_AUTH}/forgot-password/cooldown`, { email }, {
      noToken: true,
      retryOn401: false,
      showErrorToast: false,
      showSuccessToast: false,
      returnStatus: true,
      ...config,
    }),

  // Verify email address
  verifyEmail: (verificationToken, config = {}) => 
    apiService.get(`${BASE_AUTH}/verify-email`, {}, {
      headers: { Authorization: `Bearer ${verificationToken}` },
      noToken: true,
      retryOn401: false,
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.auth.verifyEmail.messages.success', 'Email verified successfully'),
        401: i18n.t('pages.auth.verifyEmail.messages.invalidToken', 'The verification link has expired or is invalid. Please request a new one.'),
        404: i18n.t('pages.auth.verifyEmail.messages.userNotFound', 'User not found'),
        409: i18n.t('pages.auth.verifyEmail.messages.emailExists', 'Email already exists'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Resend verification email
  resendVerification: (email, config = {}) => 
    apiService.post(`${BASE_AUTH}/resend-verification`, { email }, {
      noToken: true,
      retryOn401: false,
      showErrorToast: true,
      showSuccessToast: true,
      messageMap: {
        success: i18n.t('pages.auth.verifyEmail.messages.emailSent', 'Verification email sent'),
        400: i18n.t('pages.auth.verifyEmail.messages.cooldown', 'Please wait before requesting another verification email'),
        403: i18n.t('pages.auth.verifyEmail.messages.accountDisabled', 'Account is disabled'),
        404: i18n.t('pages.auth.verifyEmail.messages.emailNotRegistered', 'This email is not registered'),
        503: i18n.t('pages.auth.verifyEmail.messages.smtpDisabled', 'SMTP is disabled'),
        ...config.messageMap,
      },
      ...config,
    }),

  // Get email verification cooldown status
  getEmailVerificationCooldown: (email, config = {}) => 
    apiService.get(`${BASE_AUTH}/resend-verification/cooldown`, { email }, {
      noToken: true,
      retryOn401: false,
      showErrorToast: false,
      showSuccessToast: false,
      returnStatus: true,
      ...config,
    }),
};

export default authService;