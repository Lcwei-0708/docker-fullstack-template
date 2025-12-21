import { useTranslation } from 'react-i18next';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

export function ProfileInfo({ user }) {
  const { t } = useTranslation();

  if (!user) {
    return null;
  }

  return (
    <div className="space-y-5 md:space-y-4 text-sm">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-4">
        <div className="space-y-1.5 md:space-y-2">
          <Label htmlFor="first_name">
            {t('pages.profile.profile.fields.firstName.label')}
          </Label>
          <Input
            id="first_name"
            value={user.first_name || ''}
            disabled
            className="text-muted-foreground"
          />
        </div>
        <div className="space-y-1.5 md:space-y-2">
          <Label htmlFor="last_name">
            {t('pages.profile.profile.fields.lastName.label')}
          </Label>
          <Input
            id="last_name"
            value={user.last_name || ''}
            disabled
            className="text-muted-foreground"
          />
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-4">
        <div className="space-y-1.5 md:space-y-2">
          <Label htmlFor="email">
            {t('pages.profile.profile.fields.email.label')}
          </Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            value={user.email || ''}
            disabled
            className="text-muted-foreground"
          />
        </div>
        <div className="space-y-1.5 md:space-y-2">
          <Label htmlFor="phone">
            {t('pages.profile.profile.fields.phone.label')}
          </Label>
          <Input
            id="phone"
            type="tel"
            autoComplete="tel"
            value={user.phone || ''}
            disabled
            className="text-muted-foreground"
          />
        </div>
      </div>
    </div>
  );
}

export default ProfileInfo;