import React, { createContext, useContext, useReducer, useEffect, useCallback, useMemo, useRef } from 'react';
import { setTokenGetter } from '@/services/api.service';
import authService from '@/services/auth.service';

const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

const AUTH_ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_USER: 'SET_USER',
  SET_TOKEN: 'SET_TOKEN',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGOUT: 'LOGOUT',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// Reducer for auth state
const authReducer = (state, action) => {
  switch (action.type) {
    case AUTH_ACTIONS.SET_LOADING:
      return { ...state, isLoading: action.payload };
    
    case AUTH_ACTIONS.SET_USER:
      return { ...state, user: action.payload };
    
    case AUTH_ACTIONS.SET_TOKEN:
      return { ...state, token: action.payload, isAuthenticated: !!action.payload };
    
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
      };
    
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

  const setUser = useCallback((user) => {
    dispatch({ type: AUTH_ACTIONS.SET_USER, payload: user });
  }, []);

  const setToken = useCallback((token) => {
    dispatch({ type: AUTH_ACTIONS.SET_TOKEN, payload: token });
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
  }, []);

  const loginSuccess = useCallback((user, token) => {
    dispatch({
      type: AUTH_ACTIONS.LOGIN_SUCCESS,
      payload: { user, token },
    });
  }, []);

  useEffect(() => {
    setTokenGetter(
      () => state.token,
      (...args) => logoutRef.current?.(...args),
      (...args) => getTokenRef.current?.(...args)
    );
  }, [state.token]);

  useEffect(() => {
    if (initRef.current || isInitializingRef.current) {
      return;
    }

    initRef.current = true;
    isInitializingRef.current = true;

    const init = async () => {
      try {
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: true });
        
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
          dispatch({ type: AUTH_ACTIONS.SET_TOKEN, payload: access_token });
        }
        
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
      } catch (error) {
        dispatch({ type: AUTH_ACTIONS.SET_LOADING, payload: false });
      } finally {
        isInitializingRef.current = false;
      }
    };

    init();
  }, []);

  const value = useMemo(() => {
    return {
      ...state,
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
    };
  }, [
    state.user,
    state.token,
    state.isAuthenticated,
    state.isLoading,
    state.error,
    setUser,
    setToken,
    setLoading,
    setError,
    clearError,
    clearAuth,
    loginSuccess,
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