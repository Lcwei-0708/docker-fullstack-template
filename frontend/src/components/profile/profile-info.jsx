import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { User, Mail, Phone, Shield, Calendar, Edit, Lock } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { useMobile } from '@/hooks/useMobile';

export function ProfileInfo({ user, onEditClick, onChangePasswordClick }) {
  const { t } = useTranslation();
  const isMobile = useMobile();

  if (!user) {
    return null;
  }

  return (
    <Card className={cn(
      isMobile ? "p-4" : ""
    )}>
      <CardHeader className={cn(
        isMobile ? "px-0 pb-0" : "pb-4"
      )}>
        <div className={cn(
          "flex flex-row gap-4",
          isMobile ? "justify-between" : "justify-end"
        )}>
          <Button
            variant="outline"
            onClick={onEditClick}
            className={cn(
              "gap-2",
              isMobile ? "flex-1" : "w-auto"
            )}
          >
            <Edit className="h-4 w-4" />
            {t('profile.actions.edit')}
          </Button>
          <Button
            variant="outline"
            onClick={onChangePasswordClick}
            className={cn(
              "gap-2",
              isMobile ? "flex-1" : "w-auto"
            )}
          >
            <Lock className="h-4 w-4" />
            {t('profile.actions.changePassword')}
          </Button>
        </div>
      </CardHeader>
      <CardContent className={cn(
        isMobile ? "px-0" : ""
      )}>
        <div className="grid gap-6 md:grid-cols-2">
          {/* First Name */}
          <div className="flex items-start gap-3">
            <User className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm text-muted-foreground">{t('profile.updateProfile.fields.firstName.label')}</p>
              <p className="font-medium">{user.first_name || t('profile.fields.status.values.notSet')}</p>
            </div>
          </div>

          {/* Last Name */}
          <div className="flex items-start gap-3">
            <User className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm text-muted-foreground">{t('profile.updateProfile.fields.lastName.label')}</p>
              <p className="font-medium">{user.last_name || t('profile.fields.status.values.notSet')}</p>
            </div>
          </div>

          {/* Email */}
          <div className="flex items-start gap-3">
            <Mail className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm text-muted-foreground">{t('profile.updateProfile.fields.email.label')}</p>
              <p className="font-medium">{user.email || t('profile.fields.status.values.notSet')}</p>
            </div>
          </div>

          {/* Phone */}
          <div className="flex items-start gap-3">
            <Phone className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm text-muted-foreground">{t('profile.updateProfile.fields.phone.label')}</p>
              <p className="font-medium">{user.phone || t('profile.fields.status.values.notSet')}</p>
            </div>
          </div>

          {/* Status */}
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm text-muted-foreground">{t('profile.fields.status.label')}</p>
              <p className="font-medium">
                <span className={cn(
                  "px-2 py-1 rounded-full text-xs",
                  user.status === true 
                    ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                    : "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200"
                )}>
                  {user.status === true 
                    ? t('profile.fields.status.values.active')
                    : t('profile.fields.status.values.inactive')}
                </span>
              </p>
            </div>
          </div>

          {/* User ID */}
          <div className="flex items-start gap-3">
            <User className="h-5 w-5 text-muted-foreground mt-0.5" />
            <div>
              <p className="text-sm text-muted-foreground">{t('profile.fields.userId.label')}</p>
              <p className="font-medium font-mono text-sm">{user.id}</p>
            </div>
          </div>

          {/* Created At */}
          {user.created_at && (
            <div className="flex items-start gap-3 md:col-span-2">
              <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
              <div>
                <p className="text-sm text-muted-foreground">{t('profile.fields.createdAt.label')}</p>
                <p className="font-medium text-sm">
                  {new Date(user.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default ProfileInfo;