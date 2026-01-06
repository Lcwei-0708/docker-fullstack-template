import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Spinner } from '@/components/ui/spinner';
import { useTranslation } from 'react-i18next';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { z } from 'zod';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';

// Dialog for resetting user password
export function ResetPasswordDialog({
  open,
  onOpenChange,
  user,
  onConfirm,
  isResetting = false,
}) {
  const { t } = useTranslation();

  // Form schema
  const formSchema = React.useMemo(() => {
    return z.object({
      new_password: z
        .string()
        .min(1, t('pages.usersManagement.dialog.resetPassword.fields.newPassword.validation.required', 'New password is required'))
        .min(6, t('pages.usersManagement.dialog.resetPassword.fields.newPassword.validation.minLength', 'Password must be at least 6 characters')),
    });
  }, [t]);

  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: {
      new_password: '',
    },
  });

  // Reset form when dialog opens/closes
  React.useEffect(() => {
    if (!open) {
      form.reset();
    }
  }, [open, form]);

  // Handle form submission
  const handleSubmit = React.useCallback((values) => {
    if (onConfirm && user) {
      onConfirm(user, values.new_password);
    }
  }, [onConfirm, user]);

  // Get user display name
  const userDisplayName = React.useMemo(() => {
    if (!user) return '';
    if (user.first_name || user.last_name) {
      return `${user.first_name || ''} ${user.last_name || ''}`.trim();
    }
    return user.email || '';
  }, [user]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent showCloseButton={false} className="max-w-md">
        <DialogHeader>
          <DialogTitle>
            {t('pages.usersManagement.dialog.resetPassword.title', 'Reset Password')}
          </DialogTitle>
          <DialogDescription>
            {t(
              'pages.usersManagement.dialog.resetPassword.description',
              'Reset password for {{name}}',
              { name: userDisplayName }
            )}
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel
                    htmlFor="new_password"
                    className={cn(
                      'flex items-center gap-1',
                      form.formState.errors.new_password && 'text-destructive'
                    )}
                  >
                    {t('pages.usersManagement.dialog.resetPassword.fields.newPassword.label', 'New Password')}
                    <span className="text-destructive">*</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      id="new_password"
                      type="password"
                      showPasswordToggle={true}
                      autoComplete="new-password"
                      {...field}
                      disabled={isResetting}
                      className={cn(
                        form.formState.errors.new_password &&
                          'ring-2 ring-destructive focus-visible:ring-destructive'
                      )}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={isResetting}
              >
                {t('common.actions.cancel', 'Cancel')}
              </Button>
              <Button
                type="submit"
                disabled={isResetting}
              >
                {isResetting
                  ? <Spinner className="size-4" />
                  : t('common.actions.reset', 'Reset')}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

export default ResetPasswordDialog;