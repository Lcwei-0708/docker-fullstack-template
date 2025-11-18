import React, { useMemo, useRef, useCallback, useEffect } from 'react';
import { useAuth as useAuthContext } from '@/contexts/authContext';
import authService from '@/services/auth.service';
import accountService from '@/services/account.service';
import rolesService from '@/services/roles.service';
import i18n from '@/i18n';

export const useAuth = () => {
  const context = useAuthContext();
  const {
    setUser,
    setToken,
    setLoading,
    setError,
    clearError,
    clearAuth,
    loginSuccess,
    getTokenRef,
    logoutRef,
    profileInitRef,
    ...state
  } = context;

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

  const login = useCallback(async (credentials) => {
    try {
      setLoading(true);
      clearError();

      const result = await authService.login(credentials);
      
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
      let errorMessage = error.response?.data?.message || error.message || 'Login failed';
      
      const status = error.response?.status;
      const is401Error = status === 401 || 
                        error.message?.includes('401') || 
                        (error.code === 'ERR_BAD_REQUEST' && error.message?.includes('Unauthorized'));
      
      if (is401Error) {
        errorMessage = i18n.t('auth.login.messages.invalidCredentials', { 
          defaultValue: 'Invalid email or password' 
        });
      }
      
      setError(errorMessage);
      setLoading(false);
      return { success: false, error: errorMessage };
    }
  }, [setLoading, clearError, loginSuccess, fetchAndUpdateProfile, setError]);

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
        setToken(access_token);
        profileInitRef.current = true;
        
        if (!skipProfile) {
          await new Promise(resolve => setTimeout(resolve, 50));
          await fetchAndUpdateProfile({ showSuccessToast: false });
        }
        
        setLoading(false);
        return { success: true, token: access_token };
      }
      
      setLoading(false);
      
      if (!isInit) {
        clearAuth();
      }
      
      return { success: false, error: 'Unable to get token' };
    } catch (error) {
      setLoading(false);
      
      if (!isInit) {
        clearAuth();
      }
      
      return { success: false, error: error.message };
    }
  }, [setLoading, setToken, fetchAndUpdateProfile, clearAuth]);

  const resetPassword = useCallback(async (newPassword, resetToken) => {
    try {
      setLoading(true);
      clearError();

      const result = await authService.resetPassword(newPassword, resetToken);
      
      if (result?.user && result?.access_token) {
        const { user, access_token: token } = result;
        
        loginSuccess(user, token);
        await new Promise(resolve => setTimeout(resolve, 50));
        await fetchAndUpdateProfile({ showSuccessToast: false });
      }
      
      setLoading(false);
      return { success: true, data: result };
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Password reset failed';
      setError(errorMessage);
      setLoading(false);
      return { success: false, error: errorMessage };
    }
  }, [setLoading, clearError, loginSuccess, fetchAndUpdateProfile, setError]);

  const validateResetToken = useCallback(async (resetToken) => {
    try {
      const result = await authService.validateResetToken(resetToken);
      return { success: true, data: result };
    } catch (error) {
      const errorMessage = error.response?.data?.message || error.message || 'Token validation failed';
      return { success: false, error: errorMessage };
    }
  }, []);

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

  const stateRef = useRef(state);
  
  useEffect(() => {
    stateRef.current = state;
  }, [state]);
  
  useEffect(() => {
    if (profileInitRef.current || state.isLoading || !state.token || state.user) {
      return;
    }

    profileInitRef.current = true;
    
    const initProfile = async () => {
      await new Promise(resolve => setTimeout(resolve, 50));
      
      const currentState = stateRef.current;
      if (currentState.token && !currentState.user) {
        try {
          await fetchAndUpdateProfile({ showSuccessToast: false });
        } catch (error) {
          profileInitRef.current = false;
          console.error('Failed to fetch profile during initialization:', error);
        }
      }
    };

    initProfile();
  }, [state.token, state.user, state.isLoading, fetchAndUpdateProfile, profileInitRef]);

  useEffect(() => {
    getTokenRef.current = getToken;
    logoutRef.current = logout;
  }, [getToken, logout]);

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
  }), [
    state,
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
};

export const useAuthStatus = () => {
  const { user, isAuthenticated } = useAuth();
  const permissionCacheRef = useRef({});
  
  const checkPermissions = useCallback(async (attributes) => {
    if (!isAuthenticated) {
      return {};
    }
    
    try {
      const cacheKey = JSON.stringify(attributes.sort());
      if (permissionCacheRef.current[cacheKey]) {
        return permissionCacheRef.current[cacheKey];
      }
      
      const result = await rolesService.checkPermissions(attributes);
      permissionCacheRef.current[cacheKey] = result?.permissions || result;
      
      return result?.permissions || result;
    } catch (error) {
      return {};
    }
  }, [isAuthenticated]);
  
  const hasPermission = useCallback(async (permission) => {
    const permissions = await checkPermissions([permission]);
    return permissions[permission] === true;
  }, [checkPermissions]);
  
  const hasAllPermissions = useCallback(async (permissions) => {
    const result = await checkPermissions(permissions);
    return permissions.every(perm => result[perm] === true);
  }, [checkPermissions]);
  
  return useMemo(() => ({
    isLoggedIn: isAuthenticated,
    isAuthenticated,
    checkPermissions,
    hasPermission,
    hasAllPermissions,
    userId: user?.id,
    userName: user?.name || user?.username || `${user?.first_name} ${user?.last_name}`.trim(),
    userEmail: user?.email,
    user,
  }), [user, isAuthenticated, checkPermissions, hasPermission, hasAllPermissions]);
};

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

export const useAuthInit = () => {
  const { isLoading } = useAuth();
  return { isLoading };
};

export default useAuth;
