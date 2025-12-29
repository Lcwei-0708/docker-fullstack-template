import React, { createContext, useContext, useReducer, useEffect, useCallback, useMemo, useRef } from 'react';
import { setTokenGetter } from '@/services/api.service';

const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
  permissions: null,
  isLoadingPermissions: false,
};

const AUTH_ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_USER: 'SET_USER',
  SET_TOKEN: 'SET_TOKEN',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGOUT: 'LOGOUT',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  SET_PERMISSIONS: 'SET_PERMISSIONS',
  SET_LOADING_PERMISSIONS: 'SET_LOADING_PERMISSIONS',
};

// Reducer for auth state
const authReducer = (state, action) => {
  switch (action.type) {
    case AUTH_ACTIONS.SET_LOADING:
      return { ...state, isLoading: action.payload };
    
    case AUTH_ACTIONS.SET_USER:
      return { ...state, user: action.payload };
    
    case AUTH_ACTIONS.SET_TOKEN:
      const setTokenState = { ...state, token: action.payload, isAuthenticated: !!action.payload };
      // If token is null, clear user as well
      if (!action.payload && state.user) {
        setTokenState.user = null;
      }
      return setTokenState;
    
    case AUTH_ACTIONS.LOGIN_SUCCESS:
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    
    case AUTH_ACTIONS.LOGOUT:
      return {
        ...state,
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
        permissions: null,
        isLoadingPermissions: false,
      };
    
    case AUTH_ACTIONS.SET_PERMISSIONS:
      return { ...state, permissions: action.payload, isLoadingPermissions: false };
    
    case AUTH_ACTIONS.SET_LOADING_PERMISSIONS:
      return { ...state, isLoadingPermissions: action.payload };
    
    case AUTH_ACTIONS.SET_ERROR:
      return { ...state, error: action.payload, isLoading: false };
    
    case AUTH_ACTIONS.CLEAR_ERROR:
      return { ...state, error: null };
    
    default:
      return state;
  }
};

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const initRef = useRef(false);
  const isInitializingRef = useRef(false);
  const getTokenRef = useRef(null);
  const logoutRef = useRef(null);
  const profileInitRef = useRef(false);
  const permissionsLoadRef = useRef(false);
  const isResettingPasswordRef = useRef(false);

  const setUser = useCallback((user) => {
    dispatch({ type: AUTH_ACTIONS.SET_USER, payload: user });
  }, []);

  const setToken = useCallback((token) => {
    dispatch({ type: AUTH_ACTIONS.SET_TOKEN, payload: token });
  }, []);

  const setPermissions = useCallback((permissions) => {
    dispatch({ type: AUTH_ACTIONS.SET_PERMISSIONS, payload: permissions });
  }, []);

  const setLoadingPermissions = useCallback((isLoading) => {
    dispatch({ type: AUTH_ACTIONS.SET_LOADING_PERMISSIONS, payload: isLoading });
  }, []);

  const setLoading = useCallback((isLoading) => {
    dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: isLoading });
  }, []);

  const setError = useCallback((error) => {
    dispatch({ type: AUTH_ACTIONS.SET_ERROR, payload: error });
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: AUTH_ACTIONS.CLEAR_ERROR });
  }, []);

  const clearAuth = useCallback(() => {
    dispatch({ type: AUTH_ACTIONS.LOGOUT });
    profileInitRef.current = false;
    permissionsLoadRef.current = false;
  }, []);

  const loginSuccess = useCallback((user, token) => {
    dispatch({
      type: AUTH_ACTIONS.LOGIN_SUCCESS,
      payload: { user, token },
    });
  }, []);

  // Check if user has required permissions
  const checkPermissions = useCallback((requiredPermissions) => {
    if (!requiredPermissions || requiredPermissions.length === 0) {
      return true;
    }

    if (!state.permissions) {
      return false;
    }

    // user needs at least one of the required permissions
    return requiredPermissions.some(perm => state.permissions[perm] === true);
  }, [state.permissions]);

  useEffect(() => {
    setTokenGetter(
      () => state.token,
      (...args) => logoutRef.current?.(...args),
      (...args) => getTokenRef.current?.(...args)
    );
  }, [state.token]);

  const value = useMemo(() => {
    return {
      ...state,
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
    };
  }, [
    state.user,
    state.token,
    state.isAuthenticated,
    state.isLoading,
    state.error,
    state.permissions,
    state.isLoadingPermissions,
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
  ]);

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  
  return context;
};

export default AuthContext;