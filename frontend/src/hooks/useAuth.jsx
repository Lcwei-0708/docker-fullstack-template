import React, { useMemo, useCallback, useEffect } from 'react';
import { useAuth as useAuthContext } from '@/contexts/authContext';
import authService from '@/services/auth.service';
import accountService from '@/services/account.service';
import rolesService from '@/services/roles.service';
import i18n from '@/i18n';
import { debugError } from '@/lib/utils';

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
      
      // Check if response indicates password reset is required (202 status)
      if (result?._statusCode === 202 || result?.reset_token) {
        const resetToken = result?.reset_token || result?.data?.reset_token;
        
        setLoading(false);
        return { 
          success: false, 
          requiresPasswordReset: true,
          resetToken: resetToken,
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
      // Check if error response indicates password reset is required (202 status)
      if (error.response?.status === 202) {
        const resetToken = error.response?.data?.data?.reset_token || error.response?.data?.reset_token;
        setLoading(false);
        return { 
          success: false, 
          requiresPasswordReset: true,
          resetToken: resetToken,
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
      
      if (result?.user && result?.access_token) {
        const { user, access_token: token } = result;
        
        loginSuccess(user, token);
        await new Promise(resolve => setTimeout(resolve, 50));
        await fetchAndUpdateProfile({ showSuccessToast: false });
      }
      
      setLoading(false);
      return { success: true, data: result };
    } catch (error) {
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

  // Get authentication token from server
  const getToken = useCallback(async (isInit = false, skipProfile = false) => {
    try {
      setLoading(true);
      
      const result = await authService.getToken({ showErrorToast: false });
      
      let access_token;
      if (typeof result === 'string') {
        access_token = result;
      } else if (result?.data) {
        access_token = result.data.access_token || result.data;
      } else if (result?.access_token) {
        access_token = result.access_token;
      }
      
      if (access_token) {
        // Preserve user if exists, otherwise just set token
        if (state.user) {
          loginSuccess(state.user, access_token);
        } else {
          setToken(access_token);
        }
        setLoading(false);
        return { success: true, token: access_token };
      }
      
      setLoading(false);
      
      // Only clear auth if not initializing and no token exists
      if (!isInit && !state.token) {
        clearAuth();
      }
      
      return { success: false, error: 'Unable to get token' };
    } catch (error) {
      setLoading(false);
      
      // Only clear auth if not initializing and no token exists
      if (!isInit && !state.token) {
        clearAuth();
      }
      
      return { success: false, error: error.message };
    }
  }, [setLoading, setToken, clearAuth, state.token, state.user, loginSuccess]);

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
        
        // Allow permissions to load
        isResettingPasswordRef.current = false;
        
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
  }, [setLoading, clearError, loginSuccess, fetchAndUpdateProfile, setError]);

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

      const result = await accountService.updateProfile(userData, { ...config });
      setUser(result);
      
      return { success: true, data: result };
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Failed to update user profile';
      setError(errorMessage);
      return { success: false, error: errorMessage };
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
        setLoading(true);
        
        let result;
        try {
          result = await authService.getToken();
        } catch (tokenError) {
          result = null;
        }
        
        let access_token;
        if (result) {
          if (typeof result === 'string') {
            access_token = result;
          } else if (result?.data) {
            access_token = result.data.access_token || result.data;
          } else if (result?.access_token) {
            access_token = result.access_token;
          }
        }
        
        if (access_token) {
          setToken(access_token);
        }
        
        setLoading(false);
      } catch (error) {
        setLoading(false);
      } finally {
        isInitializingRef.current = false;
      }
    };

    init();
  }, [setLoading, setToken]);

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