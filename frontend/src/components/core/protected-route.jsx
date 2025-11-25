import React, { useRef, useEffect } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { Spinner } from '@/components/ui/spinner';

/**
 * ProtectedRoute - Route protection component
 * Checks if user is logged in, sends to login page if not
 * 
 * @param {ReactNode} children - Components to protect
 * @param {boolean} requireAuth - Need login or not (default: true)
 * @param {string[]} permissions - Permission list (optional, for later use)
 * @returns {ReactNode} - Shows children if logged in, else goes to login page
 */
export const ProtectedRoute = ({ children, requireAuth = true, permissions = null }) => {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const isInitialLoadRef = useRef(true);
  const wasAuthenticatedRef = useRef(isAuthenticated);
  
  useEffect(() => {
    if (!isLoading && isInitialLoadRef.current) {
      isInitialLoadRef.current = false;
    }
  }, [isLoading]);

  // Check authentication status change and redirect to login page if user becomes unauthenticated
  useEffect(() => {
    if (wasAuthenticatedRef.current && !isAuthenticated && location.pathname !== '/login') {
      navigate('/login', { state: { from: location }, replace: true });
    }
    wasAuthenticatedRef.current = isAuthenticated;
  }, [isAuthenticated, location, navigate]);

  // Show loading spinner only on initial load to prevent unmounting child components during authentication
  if (isLoading && isInitialLoadRef.current) {
    return (
      <div className="flex items-center justify-center min-h-[100dvh]">
        <Spinner className="size-8" />
      </div>
    );
  }

  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!requireAuth && isAuthenticated && location.pathname === "/login") {
    const from = location.state?.from?.pathname;
    return <Navigate to={from || "/"} replace />;
  }

  return children;
};

export default ProtectedRoute;