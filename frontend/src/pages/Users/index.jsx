import React from 'react';
import { cn } from '@/lib/utils';
import { useTranslation } from 'react-i18next';
import { useIsMobile } from '@/hooks/useMobile';
import { useAuthStatus } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import { Plus } from 'lucide-react';
import { UsersTable } from '@/components/users/users-table';
import { UsersCardList } from '@/components/users/users-card-list';

export default function Users() {
  const { t } = useTranslation();
  const isMobile = useIsMobile();
  const { hasPermission } = useAuthStatus();
  const canManageUsers = hasPermission("manage-users");
  const usersCardListRef = React.useRef(null);

  const handleCreate = React.useCallback(() => {
    if (usersCardListRef.current?.handleAdd) {
      usersCardListRef.current.handleAdd();
    }
  }, []);

  return (
    <div className={cn("p-6 space-y-4", isMobile && "p-0 space-y-2")}>
      <div className={cn("px-0", isMobile && "flex items-center justify-between gap-4 px-6")}>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold">
            {t('pages.usersManagement.title', 'Users List')}
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t('pages.usersManagement.description', 'Manage user accounts')}
          </p>
        </div>
        {isMobile && canManageUsers && (
          <Button
            variant="default"
            onClick={handleCreate}
            className="px-3 gap-1 h-12"
          >
            <Plus className="size-5" />
            <span className="text-base font-medium whitespace-nowrap">{t("common.actions.create", "Create")}</span>
            <span className="sr-only">{t("common.actions.create", "Create")}</span>
          </Button>
        )}
      </div>
      {isMobile ? <UsersCardList ref={usersCardListRef} /> : <UsersTable />}
    </div>
  );
}