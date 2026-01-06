import React, { useRef, useEffect } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Spinner } from '@/components/ui/spinner';
import Error from '@/pages/Error';
import { debugError } from '@/lib/utils';

/**
 * ProtectedRoute - Protects routes by checking authentication and permissions
 */
export const ProtectedRoute = ({ children, requireAuth = true, permissions = null }) => {
  const { isAuthenticated, isLoading, isLoadingPermissions, checkPermissions, logout, isResettingPasswordRef } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const isInitialLoadRef = useRef(true);
  const wasAuthenticatedRef = useRef(isAuthenticated);
  
  // Track initial load state
  useEffect(() => {
    if (!isLoading && isInitialLoadRef.current) {
      isInitialLoadRef.current = false;
    }
  }, [isLoading]);

  // Handle reset password page - logout authenticated users
  const isResetPasswordPage = location.pathname === '/reset-password';
  
  // Auto logout authenticated users visiting reset password page (except during password reset)
  useEffect(() => {
    if (isResetPasswordPage && isAuthenticated && !isLoading && !isResettingPasswordRef?.current) {
      logout(true);
    }
  }, [isResetPasswordPage, isAuthenticated, isLoading, logout, isResettingPasswordRef]);

  // Redirect to login when user becomes unauthenticated
  useEffect(() => {
    if (wasAuthenticatedRef.current && !isAuthenticated && location.pathname !== '/login' && !isResetPasswordPage) {
      navigate('/login', { state: { from: location }, replace: true });
    }
    wasAuthenticatedRef.current = isAuthenticated;
  }, [isAuthenticated, location, navigate, isResetPasswordPage]);

  // Check if user has required permissions
  const hasPermission = React.useMemo(() => {
    if (!permissions || permissions.length === 0) {
      return true;
    }
    
    if (!isAuthenticated || !checkPermissions) {
      return false;
    }
    
    try {
      return checkPermissions(permissions);
    } catch (error) {
      debugError('Failed to check permissions:', error);
      return false;
    }
  }, [permissions, isAuthenticated, checkPermissions]);

  // Show loading on initial load
  if (isLoading && isInitialLoadRef.current) {
    return (
      <div className="flex items-center justify-center min-h-[100dvh]">
        <Spinner className="size-8" />
      </div>
    );
  }

  // Show loading while checking permissions
  if (isLoadingPermissions && isAuthenticated && permissions && permissions.length > 0) {
    return (
      <div className="flex items-center justify-center min-h-[100dvh]">
        <Spinner className="size-8" />
      </div>
    );
  }

  // Redirect to login if authentication required
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Redirect authenticated users away from login/register pages
  if (!requireAuth && isAuthenticated && (location.pathname === "/login" || location.pathname === "/register")) {
    const from = location.state?.from?.pathname;
    return <Navigate to={from || "/"} replace />;
  }

  // Show error page if user lacks required permissions
  if (permissions && permissions.length > 0 && !hasPermission) {
    return React.Children.map(children, (child) => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child, {
          children: <Error errorCode="403" />
        });
      }
      return child;
    });
  }

  return children;
};

export default ProtectedRoute;