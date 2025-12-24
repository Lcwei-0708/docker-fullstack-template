import React from 'react';
import { useTranslation } from 'react-i18next';
import { UsersTable } from '@/components/users/users-table';

export default function Users() {
  const { t } = useTranslation();

  return (
    <div className="p-4 md:p-6 space-y-4 md:space-y-6">
      <div>
        <h1 className="text-2xl md:text-3xl font-bold">
          {t('pages.usersManagement.title', 'Users List')}
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          {t('pages.usersManagement.description', 'Manage user accounts')}
        </p>
      </div>
      <UsersTable />
    </div>
  );
}