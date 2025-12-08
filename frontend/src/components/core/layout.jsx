import { Dock } from '@/components/core/dock';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useMobile } from '@/hooks/useMobile';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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

export const Layout = ({ 
  children, 
  showDock = true,
  dockPosition = 'top-right'
}) => {
  const { user, isAuthenticated, logout } = useAuth();
  const { t } = useTranslation();
  const isMobile = useMobile();
  const navigate = useNavigate();
  const location = useLocation();
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [shouldDelayLoginButton, setShouldDelayLoginButton] = useState(false);
  const prevIsAuthenticatedRef = useRef(isAuthenticated);
  
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
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
      setDropdownOpen(false);
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
      setShowLogoutDialog(false);
      setDropdownOpen(false);
    }
  };

  const handleLoginClick = () => {
    navigate('/login');
  };

  const handleProfileClick = () => {
    navigate('/profile');
    setDropdownOpen(false);
  };

  const userInitials = user?.first_name?.[0]?.toUpperCase() + user?.last_name?.[0]?.toUpperCase() || 'U';
  const userName = user ? `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email || 'User' : 'User';

  useEffect(() => {
    if (!isAuthenticated) {
      setShowLogoutDialog(false);
      setDropdownOpen(false);
    }
  }, [isAuthenticated]);

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

  return (
    <div className="max-h-[100dvh] relative">
      <div className={cn(
        isMobile && "max-h-[100dvh] overflow-y-auto"
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
              {isAuthenticated ? (
                <>
                  <DropdownMenu open={dropdownOpen} onOpenChange={setDropdownOpen}>
                    <DropdownMenuTrigger asChild>
                      <button className="outline-none focus:outline-none">
                        <Avatar className="h-12 w-12 cursor-pointer">
                          <AvatarFallback className="text-sm font-medium bg-primary text-primary-foreground">
                            {userInitials}
                          </AvatarFallback>
                        </Avatar>
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-auto flex flex-col gap-1 mt-1">
                      <DropdownMenuItem onClick={handleProfileClick}>
                        <span>{t("profile.title", { defaultValue: "User Profile" })}</span>
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        variant="destructive"
                        onClick={() => {
                          setDropdownOpen(false);
                          setShowLogoutDialog(true);
                        }}
                      >
                        <span>{t("auth.logout.title", { defaultValue: "Sign out" })}</span>
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                  <AlertDialog open={showLogoutDialog} onOpenChange={setShowLogoutDialog}>
                    <AlertDialogContent>
                      <AlertDialogHeader className={cn(
                        "flex flex-col",
                        isMobile ? "gap-2" : "gap-0"
                      )}>
                        <AlertDialogTitle>{t("auth.logout.title")}</AlertDialogTitle>
                        <AlertDialogDescription>
                          {t("auth.logout.confirmMessage")}
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
                </>
              ) : shouldDelayLoginButton ? (
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
                    <span className="text-sm">{t("auth.login.title", { defaultValue: "Sign in" })}</span>
                  </Button>
                </motion.div>
              ) : (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-12 px-5 rounded-xl hover:bg-accent hover:text-accent-foreground"
                  onClick={handleLoginClick}
                >
                  <span className="text-sm">{t("auth.login.title", { defaultValue: "Sign in" })}</span>
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