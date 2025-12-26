import { useState, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { Edit, Lock, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/useAuth';
import { useIsMobile } from '@/hooks/useMobile';
import { Spinner } from '@/components/ui/spinner';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { ProfileInfo } from '@/components/profile/profile-info';
import { UpdateProfileForm } from '@/components/profile/update-profile-form';
import { ChangePasswordForm } from '@/components/profile/change-password-form';

export function Profile() {
  const { t } = useTranslation();
  const isMobile = useIsMobile();
  const { user, isLoading, loadProfile } = useAuth();

  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [isEditingSecurity, setIsEditingSecurity] = useState(false);
  const [isSubmittingProfile, setIsSubmittingProfile] = useState(false);
  const [isSubmittingPassword, setIsSubmittingPassword] = useState(false);

  const handleProfileUpdate = useCallback(async (updatedUser) => {
    setIsEditingProfile(false);
    await loadProfile();
  }, [t, loadProfile]);

  const handlePasswordChange = useCallback(async () => {
    setIsEditingSecurity(false);
    await loadProfile();
  }, [t, loadProfile]);

  const startProfileEdit = () => {
    if (isEditingSecurity) {
      setIsEditingSecurity(false);
    }
    setIsEditingProfile(true);
  };

  const cancelProfileEdit = () => {
    setIsEditingProfile(false);
  };

  const startPasswordChange = () => {
    if (isEditingProfile) {
      setIsEditingProfile(false);
    }
    setIsEditingSecurity(true);
  };

  const cancelPasswordChange = () => {
    setIsEditingSecurity(false);
  };

  if (isLoading || !user) {
    return (
      <div className="flex items-center justify-center min-h-[100dvh]">
        <Spinner className="size-10" />
      </div>
    );
  }

  return (
    <div className={cn('p-5', isMobile && 'py-1 px-3')}>
      {isMobile ? (
        // Mobile: Tabs layout
        <Tabs defaultValue="profile" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-1">
            <TabsTrigger value="profile" className="gap-2 text-base">
              {t('pages.profile.profile.title')}
            </TabsTrigger>
            <TabsTrigger value="security" className="gap-2 text-base">
              {t('pages.profile.security.title')}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card className="p-4 border-border">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold text-foreground">
                    {t('pages.profile.profile.title')}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {t('pages.profile.profile.description')}
                  </p>
                </div>
                {!isEditingProfile && (
                  <Button
                    variant="default"
                    onClick={startProfileEdit}
                    className="flex items-center text-sm"
                  >
                    <Edit className="size-4" />
                  </Button>
                )}
              </div>

              {!isEditingProfile ? (
                <ProfileInfo user={user} />
              ) : (
                <UpdateProfileForm
                  user={user}
                  onSuccess={handleProfileUpdate}
                  onClose={cancelProfileEdit}
                  onSubmittingChange={setIsSubmittingProfile}
                />
              )}
            </Card>
          </TabsContent>

          <TabsContent value="security">
            <Card className="p-4 border-border">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold text-foreground">
                    {t('pages.profile.security.title')}
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {t('pages.profile.security.description')}
                  </p>
                </div>
                {!isEditingSecurity && (
                  <Button
                    variant="default"
                    onClick={startPasswordChange}
                    className="flex items-center text-sm"
                  >
                    <Edit className="size-4" />
                  </Button>
                )}
              </div>

              {!isEditingSecurity ? (
                <div className="space-y-4 text-sm">
                  <div className="p-4 border border-border rounded-lg bg-background">
                    <h3 className="font-medium flex items-center gap-2 mb-3 text-base text-foreground">
                      {t('pages.profile.security.securityTips.title')}
                    </h3>
                    <ul className="space-y-3">
                      <li className="flex items-start gap-2 text-sm text-foreground">
                        <AlertTriangle className="text-warning mt-0.5 size-4 shrink-0" />
                        {t('pages.profile.security.securityTips.tips.regularChange')}
                      </li>
                      <li className="flex items-start gap-2 text-sm text-foreground">
                        <AlertTriangle className="text-warning mt-0.5 size-4 shrink-0" />
                        {t('pages.profile.security.securityTips.tips.uniquePassword')}
                      </li>
                    </ul>
                  </div>
                </div>
              ) : (
                <ChangePasswordForm
                  onSuccess={handlePasswordChange}
                  onClose={cancelPasswordChange}
                  onSubmittingChange={setIsSubmittingPassword}
                />
              )}
            </Card>
          </TabsContent>
        </Tabs>
      ) : (
        // Desktop: Two cards layout
        <div className="flex flex-col gap-3 md:gap-5">
          {/* Profile information */}
          <Card className="p-4 md:p-6 border-border">
            <div className="flex justify-between items-start mb-1 md:mb-2">
              <div>
                <h3 className="text-lg font-semibold text-foreground">
                  {t('pages.profile.profile.title')}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {t('pages.profile.profile.description')}
                </p>
              </div>
              {!isEditingProfile && (
                <Button
                  variant="default"
                  onClick={startProfileEdit}
                  className="flex items-center gap-1.5 md:gap-2 text-sm"
                >
                  <Edit className="size-4" />
                  {t('pages.profile.actions.edit')}
                </Button>
              )}
            </div>

            {!isEditingProfile ? (
              <ProfileInfo user={user} />
            ) : (
              <UpdateProfileForm
                user={user}
                onSuccess={handleProfileUpdate}
                onClose={cancelProfileEdit}
                onSubmittingChange={setIsSubmittingProfile}
              />
            )}
          </Card>

          {/* Security settings */}
          <Card className="p-4 md:p-6 border-border">
            <div className="flex justify-between items-start mb-1 md:mb-2">
              <div>
                <h3 className="text-lg font-semibold text-foreground">
                  {t('pages.profile.security.title')}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {t('pages.profile.security.description')}
                </p>
              </div>
              {!isEditingSecurity && (
                <Button
                  variant="default"
                  onClick={startPasswordChange}
                  className="flex items-center gap-1.5 md:gap-2 text-sm"
                >
                  <Lock className="size-4" />
                  {t('pages.profile.actions.changePassword')}
                </Button>
              )}
            </div>

            {!isEditingSecurity ? (
              <div className="space-y-4 md:space-y-6 text-sm">
                <div className="p-4 border border-border rounded-lg bg-background">
                  <h3 className="font-medium flex items-center gap-2 mb-3 md:mb-4 text-base text-foreground">
                    {t('pages.profile.security.securityTips.title')}
                  </h3>
                  <ul className="space-y-3">
                    <li className="flex items-start gap-2 text-sm text-foreground">
                      <AlertTriangle className="text-warning mt-0.5 size-4 shrink-0" />
                      {t('pages.profile.security.securityTips.tips.regularChange')}
                    </li>
                    <li className="flex items-start gap-2 text-sm text-foreground">
                      <AlertTriangle className="text-warning mt-0.5 size-4 shrink-0" />
                      {t('pages.profile.security.securityTips.tips.uniquePassword')}
                    </li>
                  </ul>
                </div>
              </div>
            ) : (
              <ChangePasswordForm
                onSuccess={handlePasswordChange}
                onClose={cancelPasswordChange}
                onSubmittingChange={setIsSubmittingPassword}
              />
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

export default Profile;