import { Dock } from '@/components/core/dock';
import { cn, debugError } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';
import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useIsMobile } from '@/hooks/useMobile';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { SidebarProvider, SidebarInset, SidebarTrigger } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/sidebar/app-sidebar';

export const Layout = ({ 
  children, 
  showDock = true,
  dockPosition = 'top-right'
}) => {
  const { user, isAuthenticated, logout } = useAuth();
  const { t } = useTranslation();
  const isMobile = useIsMobile();
  const navigate = useNavigate();
  const location = useLocation();
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const [shouldDelayLoginButton, setShouldDelayLoginButton] = useState(false);
  const prevIsAuthenticatedRef = useRef(isAuthenticated);
  
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register' || location.pathname === '/reset-password';
  const prevIsAuthPageRef = useRef(isAuthPage);

  const dockPositionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
  };

  const handleLogout = async () => {
    try {
      setShowLogoutDialog(false);
      await logout();
    } catch (error) {
      debugError('Logout failed:', error);
      setShowLogoutDialog(false);
    }
  };

  const handleLoginClick = () => {
    navigate('/login');
  };
  const userInitials = user?.first_name?.[0]?.toUpperCase() + user?.last_name?.[0]?.toUpperCase() || 'U';
  const userName = user ? `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email || 'User' : 'User';
  const userEmail = user?.email || '';

  useEffect(() => {
    let timer = null;
    
    if (prevIsAuthenticatedRef.current === true && isAuthenticated === false) {
      setShouldDelayLoginButton(true);
      timer = setTimeout(() => {
        setShouldDelayLoginButton(false);
      }, 600);
    }
    else if (prevIsAuthPageRef.current === true && isAuthPage === false && !isAuthenticated) {
      setShouldDelayLoginButton(true);
      timer = setTimeout(() => {
        setShouldDelayLoginButton(false);
      }, 600);
    }
    
    prevIsAuthenticatedRef.current = isAuthenticated;
    prevIsAuthPageRef.current = isAuthPage;
    
    return () => {
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [isAuthenticated, isAuthPage]);

  const handleSidebarLogout = () => {
    setShowLogoutDialog(true);
  };

  const sidebarUser = user ? {
    name: userName,
    email: userEmail,
    avatar: user.avatar,
    first_name: user.first_name,
    last_name: user.last_name,
  } : null;

  if (isAuthenticated && !isAuthPage) {
    return (
      <SidebarProvider>
        <AppSidebar user={sidebarUser} onLogout={handleSidebarLogout} />
        <SidebarInset className={cn("h-svh overflow-hidden")}>
          <div className={cn(
            "flex items-center gap-2 px-3 shrink-0",
            isMobile ? "border-b-0 h-15" : "border-b h-17"
          )}>
            <SidebarTrigger />
          </div>
          <div className={cn(
            "flex-1 overflow-auto min-h-0"
          )}>
            {children}
          </div>
        </SidebarInset>
        <AlertDialog open={showLogoutDialog} onOpenChange={setShowLogoutDialog}>
          <AlertDialogContent>
            <AlertDialogHeader className={cn(
              "flex flex-col",
              isMobile ? "gap-2" : "gap-0"
            )}>
              <AlertDialogTitle>{t("pages.auth.logout.title")}</AlertDialogTitle>
              <AlertDialogDescription>
                {t("pages.auth.logout.confirmMessage")}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter className="flex-row gap-5 sm:gap-0 mt-2">
              <AlertDialogCancel
                className={cn(
                  isMobile && "w-full"
                )}
              >
                {t("common.actions.cancel")}
              </AlertDialogCancel>
              <AlertDialogAction 
                onClick={handleLogout}
                className={cn(
                  "bg-destructive text-destructive-foreground hover:bg-destructive/90",
                  isMobile && "w-full"
                )}
              >
                {t("common.actions.confirm")}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </SidebarProvider>
    );
  }

  return (
    <div className="h-[100dvh] max-h-[100dvh] relative">
      <div className={cn(
        "h-full",
        isMobile && "overflow-y-auto"
      )}>
        {children}
      </div>
      {(showDock && (dockPosition === 'top-right' || dockPosition === 'bottom-right')) || !isAuthPage ? (
        <div 
          className={cn(
            "fixed z-50 flex items-center gap-3",
            dockPosition === 'top-right' || dockPosition === 'bottom-right'
              ? dockPosition === 'top-right' ? 'top-4 right-4' : 'bottom-4 right-4'
              : 'top-4 right-4'
          )}
        >
          {showDock && (dockPosition === 'top-right' || dockPosition === 'bottom-right') && (
            <Dock />
          )}
          {!isAuthPage && (
            <>
              {shouldDelayLoginButton ? (
                <motion.div
                  initial={{ opacity: 0, x: 0 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{
                    duration: 0.2,
                    delay: 0.2,
                    ease: [0.5, 0.0, 0.5, 1],
                  }}
                >
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-12 px-5 rounded-xl hover:bg-accent hover:text-accent-foreground"
                    onClick={handleLoginClick}
                  >
                    <span className="text-sm">{t("pages.auth.login.title", { defaultValue: "Sign in" })}</span>
                  </Button>
                </motion.div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-12 px-5 rounded-xl hover:bg-accent hover:text-accent-foreground"
                  onClick={handleLoginClick}
                >
                  <span className="text-sm">{t("pages.auth.login.title", { defaultValue: "Sign in" })}</span>
                </Button>
              )}
            </>
          )}
        </div>
      ) : null}
      {showDock && (dockPosition === 'top-left' || dockPosition === 'bottom-left') && (
        <div 
          className={cn(
            "fixed z-50",
            dockPositionClasses[dockPosition]
          )}
        >
          <Dock />
        </div>
      )}
    </div>
  );
};

export default Layout;