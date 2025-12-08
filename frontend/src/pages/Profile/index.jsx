import { useState, useCallback } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';
import { Spinner } from '@/components/ui/spinner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ProfileInfo } from '@/components/profile/profile-info';
import { UpdateProfileForm } from '@/components/profile/update-profile-form';
import { ChangePasswordForm } from '@/components/profile/change-password-form';

export function Profile() {
  const { user, isLoading } = useAuth();
  const { t } = useTranslation();
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [isSubmittingProfile, setIsSubmittingProfile] = useState(false);
  const [isSubmittingPassword, setIsSubmittingPassword] = useState(false);

  const handleProfileUpdate = useCallback(async (updatedUser) => {
    setShowEditDialog(false);
  }, []);

  const handlePasswordChange = useCallback(() => {
    setShowPasswordDialog(false);
  }, []);

  if (isLoading || !user) {
    return (
      <div className="flex items-center justify-center min-h-[100dvh]">
        <Spinner className="size-10" />
      </div>
    );
  }

  return (
    <div className={cn("min-h-[100dvh] p-4 md:p-8", "bg-background text-foreground")}>
      <div className="max-w-4xl mx-auto mt-18">
        {/* Profile Info */}
        <ProfileInfo 
          user={user} 
          onEditClick={() => setShowEditDialog(true)}
          onChangePasswordClick={() => setShowPasswordDialog(true)}
        />

        {/* Edit Profile Dialog */}
        <Dialog 
          open={showEditDialog} 
          onOpenChange={(open) => {
            if (!open && isSubmittingProfile) {
              return;
            }
            setShowEditDialog(open);
          }}
        >
          <DialogContent 
            showCloseButton={false}
            className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {t('profile.updateProfile.title')}
              </DialogTitle>
              <DialogDescription>
                {t('profile.updateProfile.description')}
              </DialogDescription>
            </DialogHeader>
            <UpdateProfileForm 
              user={user} 
              onSuccess={handleProfileUpdate}
              onClose={() => {
                if (!isSubmittingProfile) {
                  setShowEditDialog(false);
                }
              }}
              onSubmittingChange={setIsSubmittingProfile}
            />
          </DialogContent>
        </Dialog>

        {/* Change Password Dialog */}
        <Dialog 
          open={showPasswordDialog}
          onOpenChange={(open) => {
            if (!open && isSubmittingPassword) {
              return;
            }
            setShowPasswordDialog(open);
          }}
          showCloseButton={false}
        >
          <DialogContent 
            showCloseButton={false}
            className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {t('profile.changePassword.title')}
              </DialogTitle>
              <DialogDescription>
                {t('profile.changePassword.description')}
              </DialogDescription>
            </DialogHeader>
            <ChangePasswordForm 
              onSuccess={handlePasswordChange}
              onClose={() => {
                if (!isSubmittingPassword) {
                  setShowPasswordDialog(false);
                }
              }}
              onSubmittingChange={setIsSubmittingPassword}
            />
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default Profile;