import React, { useMemo, useCallback, useEffect } from 'react';
import { useAuth as useAuthContext } from '@/contexts/authContext';
import authService from '@/services/auth.service';
import accountService from '@/services/account.service';
import rolesService from '@/services/roles.service';
import { debugError } from '@/lib/utils';
import { getCsrfTokenFromCookie } from '@/lib/cookies';
import {
  getApiErrorMessage,
  isCsrfInvalidError,
  isSessionInvalidError,
} from '@/lib/authErrors';

function parseAccessToken(result) {
  if (!result) {
    return null;
  }
  if (typeof result === 'string') {
    return result;
  }
  if (result.access_token) {
    return result.access_token;
  }
  if (result.data?.access_token) {
    return result.data.access_token;
  }
  if (result.data && typeof result.data === 'string') {
    return result.data;
  }
  return null;
}

export const useAuth = () => {
  const context = useAuthContext();
  const {
    setUser,
    setToken,
    setPermissions,
    setLoadingPermissions,
    setLoading,
    setError,
    clearError,
    clearAuth,
    loginSuccess,
    checkPermissions,
    getTokenRef,
    logoutRef,
    profileInitRef,
    permissionsLoadRef,
    initRef,
    isInitializingRef,
    isResettingPasswordRef,
    ...state
  } = context;

  // Fetch and update user profile
  const fetchAndUpdateProfile = useCallback(async ({ showSuccessToast = false } = {}) => {
    const profileResult = await accountService.getProfile({
      returnStatus: true,
      showSuccessToast,
    });
    
    if (profileResult.status === 'success' && profileResult.data) {
      setUser(profileResult.data);
    }
    
    return profileResult;
  }, [setUser]);

  // Auto-load user profile when authenticated
  const loadProfile = useCallback(async () => {
    if (!state.token || !state.isAuthenticated) {
      return;
    }

    if (profileInitRef.current) {
      return;
    }

    profileInitRef.current = true;
    try {
      const result = await accountService.getProfile({ showErrorToast: false });
      if (result) {
        setUser(result);
      }
    } catch (error) {
      debugError('Failed to load user profile:', error);
      profileInitRef.current = false;
    }
  }, [state.token, state.isAuthenticated, setUser]);

  // Auto-load user permissions when authenticated
  const loadPermissions = useCallback(async () => {
    if (!state.token || !state.isAuthenticated) {
      setPermissions(null);
      permissionsLoadRef.current = false;
      return;
    }

    if (permissionsLoadRef.current && state.isLoadingPermissions) {
      return;
    }

    setLoadingPermissions(true);
    try {
      const result = await rolesService.getAllUserPermissions({ showErrorToast: false });
      const permissions = result?.permissions || {};
      setPermissions(permissions);
    } catch (error) {
      debugError('Failed to load user permissions:', error);
      setPermissions({});
      permissionsLoadRef.current = false;
    } finally {
      setLoadingPermissions(false);
    }
  }, [state.token, state.isAuthenticated, state.isLoadingPermissions, setPermissions, setLoadingPermissions]);

  // Login user with email and password
  const login = useCallback(async (credentials) => {
    try {
      setLoading(true);
      clearError();

      const result = await authService.login(credentials);
      
      // Check if response indicates action is required (202 status)
      if (result?._statusCode === 202) {
        const actionData = result;
        const actionType = actionData?.action_type;
        const resetToken = actionData?.token || actionData?.reset_token;
        
        setLoading(false);
        
        if (!actionType) {          
          if (resetToken) {
            return { 
              success: false, 
              requiresPasswordReset: true,
              resetToken: resetToken,
              data: result 
            };
          } else {
            return { 
              success: false, 
              requiresEmailVerification: true,
              data: result 
            };
          }
        }
        
        if (actionType === 'password_reset' || resetToken) {
          return { 
            success: false, 
            requiresPasswordReset: true,
            resetToken: resetToken,
            data: result 
          };
        } else if (actionType === 'email_verification') {
          return { 
            success: false, 
            requiresEmailVerification: true,
            data: result 
          };
        }
        
        // Fallback for unknown action types
        return { 
          success: false, 
          requiresAction: true,
          actionType: actionType,
          data: result 
        };
      }
      
      if (result?.user && result?.access_token) {
        const { user, access_token: token } = result;
        
        loginSuccess(user, token);
        await new Promise(resolve => setTimeout(resolve, 50));
        await fetchAndUpdateProfile();
        
        setLoading(false);
        return { success: true, data: result };
      } else {
        throw new Error('Invalid login response format');
      }
    } catch (error) {
      // Check if error response indicates action is required (202 status)
      if (error.response?.status === 202) {
        // For 202 status, data is in error.response.data.data
        const actionData = error.response?.data?.data || error.response?.data;
        const actionType = actionData?.action_type;
        const resetToken = actionData?.token || actionData?.reset_token;
        
        setLoading(false);
        
        if (actionType === 'password_reset' || resetToken) {
          return { 
            success: false, 
            requiresPasswordReset: true,
            resetToken: resetToken,
            data: error.response?.data 
          };
        } else if (actionType === 'email_verification') {
          return { 
            success: false, 
            requiresEmailVerification: true,
            data: error.response?.data 
          };
        }
        
        return { 
          success: false, 
          requiresAction: true,
          actionType: actionType,
          data: error.response?.data 
        };
      }
      
      // Get error message from response or use default
      const errorMessage = error.response?.data?.message || error.message || 'Login failed';
      
      setError(errorMessage);
      setLoading(false);
      return { success: false, error: errorMessage };
    }
  }, [setLoading, clearError, loginSuccess, fetchAndUpdateProfile, setError]);

  // Register new user account
  const register = useCallback(async (userData) => {
    try {
      setLoading(true);
      clearError();

      const result = await authService.register(userData);
      
      // Check if response indicates action is required (202 status)
      if (result?._statusCode === 202) {
        // For 202 status, email verification is required
        setLoading(false);
        return { 
          success: false, 
          requiresEmailVerification: true,
          data: result 
        };
      }
      
      if (result?.user && result?.access_token) {
        const { user, access_token: token } = result;
        
        loginSuccess(user, token);
        await new Promise(resolve => setTimeout(resolve, 50));
        await fetchAndUpdateProfile({ showSuccessToast: false });
      }
      
      setLoading(false);
      return { success: true, data: result };
    } catch (error) {
      // Check if error response indicates action is required (202 status)
      if (error.response?.status === 202) {
        // For 202 status, email verification is required
        setLoading(false);
        return { 
          success: false, 
          requiresEmailVerification: true,
          data: error.response?.data 
        };
      }
      
      const errorMessage = error.response?.data?.message || error.message || 'Registration failed';
      setError(errorMessage);
      setLoading(false);
      return { success: false, error: errorMessage };
    }
  }, [setLoading, clearError, loginSuccess, fetchAndUpdateProfile, setError]);

  // Logout current user
  const logout = useCallback(async (skipApi = false) => {
    try {
      if (!skipApi) {
        await authService.logout();
      }
    } catch (error) {
      // Ignore logout errors
    } finally {
      clearAuth();
    }
  }, [clearAuth]);

  // Get authentication token from server (with CSRF validation and retry)
  const getToken = useCallback(async (isInit = false, _skipProfile = false) => {
    const applyAccessToken = (accessToken) => {
      if (state.user) {
        loginSuccess(state.user, accessToken);
      } else {
        setToken(accessToken);
      }
    };

    const attemptRefresh = async (csrfToken) => {
      const result = await authService.getToken({
        showErrorToast: false,
        csrfToken: csrfToken ?? getCsrfTokenFromCookie() ?? '',
      });
      const accessToken = parseAccessToken(result);
      if (!accessToken) {
        throw new Error('Unable to get token');
      }
      applyAccessToken(accessToken);
      return { success: true, token: accessToken };
    };

    const invalidateSession = async () => {
      await logout(true);
    };

    try {
      setLoading(true);

      try {
        const success = await attemptRefresh();
        setLoading(false);
        return success;
      } catch (error) {
        if (isCsrfInvalidError(error)) {
          try {
            const csrfResult = await authService.getCsrfToken({ showErrorToast: false });
            const newCsrf = csrfResult?.csrf_token ?? getCsrfTokenFromCookie();
            if (!newCsrf) {
              throw error;
            }
            const success = await attemptRefresh(newCsrf);
            setLoading(false);
            return success;
          } catch (retryError) {
            if (isCsrfInvalidError(retryError) || isSessionInvalidError(retryError)) {
              await invalidateSession();
              setLoading(false);
              return { success: false, error: getApiErrorMessage(retryError) };
            }
            throw retryError;
          }
        }

        if (isSessionInvalidError(error)) {
          await invalidateSession();
          setLoading(false);
          return { success: false, error: getApiErrorMessage(error) };
        }

        setLoading(false);
        if (!isInit && !state.token) {
          clearAuth();
        }
        return { success: false, error: getApiErrorMessage(error) };
      }
    } catch (error) {
      setLoading(false);
      if (!isInit && !state.token) {
        clearAuth();
      }
      return { success: false, error: getApiErrorMessage(error) };
    }
  }, [setLoading, setToken, clearAuth, state.token, state.user, loginSuccess, logout]);

  // Reset password and auto-login user
  const resetPassword = useCallback(async (newPassword, resetToken) => {
    try {
      setLoading(true);
      clearError();

      const result = await authService.resetPassword(newPassword, resetToken);
      
      const access_token = result?.access_token || result?.data?.access_token;
      const user = result?.user || result?.data?.user;
      
      if (user && access_token) {
        // Prevent auto-loading permissions during reset flow
        isResettingPasswordRef.current = true;
        
        // Update auth state and wait for state to sync
        loginSuccess(user, access_token);
        await new Promise(resolve => {
          requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              setTimeout(resolve, 100);
            });
          });
        });
        
        // Fetch profile with new token
        await fetchAndUpdateProfile();
        
        // Reset permissions load ref to allow fresh load
        permissionsLoadRef.current = false;
        
        // Allow permissions to load and actively load them
        await loadPermissions();
        
        setLoading(false);
        return { success: true, data: result };
      } else {
        debugError('Reset password response missing user or token:', result);
        setLoading(false);
        return { success: false, error: 'Invalid reset password response' };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Password reset failed';
      const status = error.response?.status;
      setError(errorMessage);
      setLoading(false);
      return { success: false, error: errorMessage, status };
    }
  }, [setLoading, clearError, loginSuccess, fetchAndUpdateProfile, setError, loadPermissions]);

  // Validate password reset token
  const validateResetToken = useCallback(async (resetToken) => {
    try {
      const result = await authService.validateResetToken(resetToken);
      return { success: true, data: result };
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Token validation failed';
      return { success: false, error: errorMessage };
    }
  }, []);

  // Get current user profile
  const getUserProfile = useCallback(async () => {
    const profileResult = await fetchAndUpdateProfile({ showSuccessToast: false });
    
    if (profileResult.status === 'success') {
      return { success: true, data: profileResult.data };
    } else {
      return { 
        success: false, 
        error: profileResult.error?.message || 'Failed to get user profile' 
      };
    }
  }, [fetchAndUpdateProfile]);

  // Update user profile information
  const updateUserProfile = useCallback(async (userData, config = {}) => {
    try {
      clearError();

      const { returnStatus, ...restConfig } = config || {};
      const result = await accountService.updateProfile(userData, { ...restConfig, returnStatus });
      const responseData = returnStatus ? result?.data : result;

      if (returnStatus && result?.status === 'error') {
        const errorMessage = result?.error?.message || 'Failed to update user profile';
        setError(errorMessage);
        return {
          ...result,
          success: false,
          error: result?.error || { message: errorMessage },
        };
      }

      if (responseData?._statusCode === 202) {
        const { _statusCode: _ignored, ...profileData } = responseData;
        const pendingEmail = profileData?.pending_email || userData?.email || null;
        const nextProfile = {
          ...profileData,
          pending_email: pendingEmail,
        };
        if (nextProfile) {
          setUser(nextProfile);
        }
        const baseResult = {
          success: false,
          requiresEmailVerification: true,
          data: nextProfile,
          email: pendingEmail,
        };
        return returnStatus
          ? { ...result, ...baseResult, status: 'accepted', data: nextProfile }
          : baseResult;
      }

      if (responseData) {
        setUser(responseData);
      }

      return returnStatus
        ? { ...result, success: true, data: responseData }
        : { success: true, data: responseData };
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to update user profile';
      setError(errorMessage);
      return config?.returnStatus
        ? { data: null, status: 'error', error: { message: errorMessage }, success: false }
        : { success: false, error: errorMessage };
    }
  }, [clearError, setUser, setError]);

  // Change user password
  const changePassword = useCallback(async (passwordData, config = {}) => {
    try {
      clearError();

      const result = await accountService.changePassword(passwordData, { ...config });
      
      return { success: true, data: result };
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Password change failed';
      setError(errorMessage);
      return { success: false, error: errorMessage };
    }
  }, [clearError, setError]);


  useEffect(() => {
    getTokenRef.current = getToken;
    logoutRef.current = logout;
  }, [getToken, logout]);

  // Check for existing token on mount
  useEffect(() => {
    if (initRef.current || isInitializingRef.current) {
      return;
    }

    initRef.current = true;
    isInitializingRef.current = true;

    const init = async () => {
      try {
        await getToken(true);
      } finally {
        isInitializingRef.current = false;
      }
    };

    init();
  }, [getToken]);

  // Auto-load profile and permissions when authenticated
  useEffect(() => {
    if (!state.isAuthenticated) {
      permissionsLoadRef.current = false;
      profileInitRef.current = false;
      return;
    }
    
    // Load profile if missing
    if (state.isAuthenticated && state.token && !state.user && !profileInitRef.current) {
      loadProfile();
    }
    
    // Load permissions if missing and not during password reset
    if (state.isAuthenticated && state.token && !state.permissions && !state.isLoadingPermissions && !permissionsLoadRef.current && !isResettingPasswordRef.current) {
      permissionsLoadRef.current = true;
      loadPermissions();
    }
  }, [state.isAuthenticated, state.token, state.user, state.permissions, state.isLoadingPermissions, loadProfile, loadPermissions]);

  return useMemo(() => ({
    ...state,
    login,
    register,
    logout,
    getToken,
    resetPassword,
    validateResetToken,
    getUserProfile,
    updateUserProfile,
    changePassword,
    clearError,
    checkPermissions,
    loadProfile,
    loadPermissions,
    isResettingPasswordRef,
  }), [
    state.user,
    state.token,
    state.isAuthenticated,
    state.isLoading,
    state.error,
    state.permissions,
    state.isLoadingPermissions,
    login,
    register,
    logout,
    getToken,
    resetPassword,
    validateResetToken,
    getUserProfile,
    updateUserProfile,
    changePassword,
    clearError,
    checkPermissions,
    loadProfile,
    loadPermissions,
  ]);
};

// Hook for checking user authentication status and permissions
export const useAuthStatus = () => {
  const { 
    user, 
    isAuthenticated, 
    permissions, 
    isLoadingPermissions,
    checkPermissions: checkPermissionsFromContext 
  } = useAuth();
  
  // Check if user has a specific permission
  const hasPermission = useCallback((permission) => {
    if (!isAuthenticated || !permissions) {
      return false;
    }
    return permissions[permission] === true;
  }, [isAuthenticated, permissions]);
  
  // Check if user has all required permissions
  const hasAllPermissions = useCallback((requiredPermissions) => {
    if (!requiredPermissions || requiredPermissions.length === 0) {
      return true;
    }
    return checkPermissionsFromContext(requiredPermissions);
  }, [checkPermissionsFromContext]);
  
  // Get all user permissions
  const getAllPermissions = useCallback(() => {
    return permissions || {};
  }, [permissions]);
  
  // Check permissions and return status object
  const checkPermissions = useCallback((attributes) => {
    if (!isAuthenticated || !permissions) {
      return {};
    }
    
    if (!attributes || attributes.length === 0) {
      return permissions;
    }
    
    const result = {};
    for (const attr of attributes) {
      result[attr] = permissions[attr] === true;
    }
    
    return result;
  }, [isAuthenticated, permissions]);
  
  return useMemo(() => ({
    isLoggedIn: isAuthenticated,
    isAuthenticated,
    checkPermissions,
    hasPermission,
    hasAllPermissions,
    getAllPermissions,
    isLoadingPermissions,
    userId: user?.id,
    userName: user?.name || user?.username || `${user?.first_name} ${user?.last_name}`.trim(),
    userEmail: user?.email,
    user,
  }), [user, isAuthenticated, permissions, isLoadingPermissions, checkPermissions, hasPermission, hasAllPermissions, getAllPermissions]);
};

// Hook for authentication actions with error handling
export const useAuthActions = () => {
  const {
    login,
    register,
    logout,
    getToken,
    resetPassword,
    validateResetToken,
    getUserProfile,
    updateUserProfile,
    changePassword,
    clearError,
    isLoading,
    error,
  } = useAuth();
  
  const actions = useMemo(() => {
    return {
      handleLogin: async (credentials) => {
        clearError();
        return await login(credentials);
      },
      
      handleRegister: async (userData) => {
        clearError();
        return await register(userData);
      },
      
      handleLogout: async () => {
        clearError();
        return await logout();
      },
      
      handleGetToken: async () => {
        clearError();
        return await getToken();
      },
      
      handleResetPassword: async (newPassword, resetToken) => {
        clearError();
        return await resetPassword(newPassword, resetToken);
      },
      
      handleValidateResetToken: async (token) => {
        clearError();
        return await validateResetToken(token);
      },
      
      handleChangePassword: async (passwordData) => {
        clearError();
        return await changePassword(passwordData);
      },
      
      handleGetUserProfile: async () => {
        clearError();
        return await getUserProfile();
      },
      
      handleUpdateUserProfile: async (userData) => {
        clearError();
        return await updateUserProfile(userData);
      },
      
      handleClearError: clearError,
    };
  }, [
    login,
    register,
    logout,
    getToken,
    resetPassword,
    validateResetToken,
    getUserProfile,
    updateUserProfile,
    changePassword,
    clearError,
  ]);
  
  return useMemo(() => ({
    ...actions,
    isProcessing: isLoading,
    hasError: !!error,
    errorMessage: error,
  }), [actions, isLoading, error]);
};

// Hook for authentication form handling
export const useAuthForm = (initialValues = {}) => {
  const { handleLogin, handleRegister, isProcessing } = useAuthActions();
  const [values, setValues] = React.useState(initialValues);
  const [errors, setErrors] = React.useState({});
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setValues(prev => ({
      ...prev,
      [name]: value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };
  
  const validateForm = (values) => {
    const newErrors = {};
    
    if (!values.email) {
      newErrors.email = 'Please enter email';
    } else if (!/\S+@\S+\.\S+/.test(values.email)) {
      newErrors.email = 'Please enter a valid email format';
    }
    
    if (!values.password) {
      newErrors.password = 'Please enter password';
    } else if (values.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    return newErrors;
  };
  
  const handleSubmit = (action) => async (e) => {
    e.preventDefault();
    
    const formErrors = validateForm(values);
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      return;
    }
    
    setErrors({});
    return await action(values);
  };
  
  return {
    values,
    errors,
    handleChange,
    handleSubmit,
    isSubmitting: isProcessing,
    handleLogin: handleSubmit(handleLogin),
    handleRegister: handleSubmit(handleRegister),
  };
};

// Hook for checking authentication initialization status
export const useAuthInit = () => {
  const { isLoading } = useAuth();
  return { isLoading };
};

export default useAuth;