import * as React from 'react';
import { useTranslation } from 'react-i18next';
import { AlertTriangle } from 'lucide-react';
import { Alert, AlertDescription, AlertIcon } from '@/components/ui/alert';
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

// Alert dialog for confirming user deletion (single or multiple)
export function DeleteUserDialog({
  open,
  onOpenChange,
  user,
  count,
  selectedUserIds,
  currentUserId,
  onConfirm,
  isDeleting = false,
}) {
  const { t } = useTranslation();

  const isMultiple = count !== undefined && count !== null;

  // Check if the current user is included in the deletion list
  const includesCurrentUser = React.useMemo(() => {
    if (!currentUserId) return false;
    
    const normalizeId = (id) => {
      if (id === null || id === undefined) return null;
      const str = String(id).trim();
      const num = Number(str);
      return isNaN(num) ? str : num;
    };
    
    const currentId = normalizeId(currentUserId);
    
    if (isMultiple && selectedUserIds && Array.isArray(selectedUserIds) && selectedUserIds.length > 0) {
      return selectedUserIds.some(id => {
        const normalizedId = normalizeId(id);
        return normalizedId === currentId || 
               String(normalizedId) === String(currentId) ||
               (typeof normalizedId === 'number' && typeof currentId === 'number' && normalizedId === currentId);
      });
    }
    
    if (!isMultiple && user && user.id !== undefined && user.id !== null) {
      const userId = normalizeId(user.id);
      return userId === currentId || 
             String(userId) === String(currentId) ||
             (typeof userId === 'number' && typeof currentId === 'number' && userId === currentId);
    }
    
    return false;
  }, [currentUserId, isMultiple, selectedUserIds, user]);

  // Handle delete confirmation and filter out current user if needed
  const handleConfirm = React.useCallback(() => {
    if (!onConfirm) return;
    
    if (isMultiple) {
      if (includesCurrentUser && selectedUserIds && Array.isArray(selectedUserIds)) {
        const currentUserIdStr = String(currentUserId).trim();
        const filteredIds = selectedUserIds.filter(id => String(id).trim() !== currentUserIdStr);
        onConfirm(filteredIds);
      } else {
        onConfirm();
      }
    } else if (user && !includesCurrentUser) {
      onConfirm(user);
    }
  }, [onConfirm, isMultiple, user, includesCurrentUser, selectedUserIds, currentUserId]);

  // Get user display name
  const userDisplayName = React.useMemo(() => {
    if (!user) return '';
    if (user.first_name || user.last_name) {
      return `${user.first_name || ''} ${user.last_name || ''}`.trim();
    }
    return user.email || '';
  }, [user]);

  // Get dialog title
  const dialogTitle = React.useMemo(() => {
    if (isMultiple) {
      return t('pages.usersManagement.dialog.deleteSelectedTitle', 'Delete Selected Users');
    }
    return t('pages.usersManagement.dialog.deleteTitle', 'Delete User');
  }, [isMultiple, t]);

  // Get main confirmation message
  const dialogDescription = React.useMemo(() => {
    if (isMultiple) {
      const otherCount = includesCurrentUser ? count - 1 : count;
      return t(
        'pages.usersManagement.dialog.deleteSelectedMessage',
        'Are you sure you want to delete {{count}} selected user(s)?',
        { count: otherCount }
      );
    }
    if (includesCurrentUser) {
      return t(
        'pages.usersManagement.dialog.deleteCurrentUserOnlyMessage',
        'You cannot delete your own account.'
      );
    }
    return t(
      'pages.usersManagement.dialog.deleteMessage',
      'Are you sure you want to delete {{name}}?',
      { name: userDisplayName }
    );
  }, [isMultiple, count, userDisplayName, includesCurrentUser, t]);

  // Get detailed warning message for alert
  const alertWarningMessage = React.useMemo(() => {
    if (!includesCurrentUser) return null;
    
    if (isMultiple) {
      const otherCount = count - 1;
      return t(
        'pages.usersManagement.dialog.deleteSelectedWithCurrentUserWarning',
        'You have selected your own account along with {{count}} other user(s). Your account will be automatically excluded from deletion, and only {{count}} other user(s) will be deleted.',
        { count: otherCount }
      );
    }
    return t(
      'pages.usersManagement.dialog.deleteCurrentUserError',
      'You cannot delete your own account.'
    );
  }, [isMultiple, count, includesCurrentUser, t]);

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{dialogTitle}</AlertDialogTitle>
          <AlertDialogDescription>{dialogDescription}</AlertDialogDescription>
        </AlertDialogHeader>
        {includesCurrentUser && (
          <Alert 
            variant="warning"
            appearance="light" 
            size="md"
          >
            <AlertIcon>
              <AlertTriangle className="size-5" />
            </AlertIcon>
            <AlertDescription>
              {alertWarningMessage}
            </AlertDescription>
          </Alert>
        )}
        <AlertDialogFooter>
          {!isMultiple && includesCurrentUser ? (
            <AlertDialogAction
              onClick={() => onOpenChange(false)}
              variant="default"
            >
              {t('common.actions.ok', 'OK')}
            </AlertDialogAction>
          ) : (
            <>
              <AlertDialogCancel disabled={isDeleting}>
                {t('common.actions.cancel', 'Cancel')}
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={handleConfirm}
                disabled={isDeleting}
                variant="destructive"
              >
                {isDeleting
                  ? t('common.actions.deleting', 'Deleting...')
                  : t('common.actions.delete', 'Delete')}
              </AlertDialogAction>
            </>
          )}
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export default DeleteUserDialog;