import { useState, useCallback, useMemo, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Spinner } from '@/components/ui/spinner';
import { useAuth } from '@/hooks/useAuth';
import { useMobile } from '@/hooks/useMobile';

export function ChangePasswordForm({ onSuccess, onClose, onSubmittingChange }) {
  const { t } = useTranslation();
  const { changePassword, isLoading } = useAuth();
  const isMobile = useMobile();
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (onSubmittingChange) {
      onSubmittingChange(isSubmitting || isLoading);
    }
  }, [isSubmitting, isLoading, onSubmittingChange]);

  const formSchema = useMemo(() => {
    return z.object({
      current_password: z
        .string()
        .min(1, t('profile.changePassword.fields.currentPassword.validation.required'))
        .min(6, t('profile.changePassword.fields.currentPassword.validation.minLength')),
      new_password: z
        .string()
        .min(1, t('profile.changePassword.fields.newPassword.validation.required'))
        .min(6, t('profile.changePassword.fields.newPassword.validation.minLength')),
      confirm_password: z
        .string()
        .min(1, t('profile.changePassword.fields.confirmPassword.validation.required')),
    }).refine((data) => data.new_password === data.confirm_password, {
      message: t('profile.changePassword.fields.confirmPassword.validation.notMatch'),
      path: ['confirm_password'],
    });
  }, [t]);

  const defaultValues = useMemo(() => ({
    current_password: '',
    new_password: '',
    confirm_password: '',
  }), []);

  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues,
  });

  const handleSubmit = useCallback(async (formValues) => {
    setIsSubmitting(true);
    
    try {
      const result = await changePassword({
        current_password: formValues.current_password,
        new_password: formValues.new_password,
        logout_all_devices: true,
      });
      
      if (result.success) {
        form.reset(defaultValues);
        if (onSuccess) {
          await onSuccess();
        }
      } else {
        // Check if it's a password error (401 with password error message)
        const error = result.error;
        const errorMessage = typeof error === 'string' ? error : error?.message || '';
        const isPasswordError = errorMessage.includes('Current password is incorrect') || 
                              errorMessage.includes('password is incorrect') ||
                              errorMessage.toLowerCase().includes('incorrect password');
        
        if (isPasswordError) {
          // Set error on current_password field
          form.setError('current_password', {
            type: 'manual',
            message: t('profile.changePassword.fields.currentPassword.validation.incorrect'),
          });
        }
      }
    } catch (error) {
      console.error('Change password error:', error);
      
      if (error.isPasswordError) {
        const errorMessage = t('profile.changePassword.fields.currentPassword.validation.incorrect');
        const fieldName = error.passwordErrorField || 'current_password';
        
        form.setError(fieldName, {
          type: 'manual',
          message: errorMessage,
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [changePassword, form, defaultValues, onSuccess, t]);

  return (
    <div className="space-y-6">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            {/* Current Password */}
            <FormField
              control={form.control}
              name="current_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('profile.changePassword.fields.currentPassword.label')}</FormLabel>
                  <FormControl>
                    <Input 
                      type="password"
                      showPasswordToggle={true}
                      {...field}
                      disabled={isSubmitting || isLoading}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {/* New Password */}
            <FormField
              control={form.control}
              name="new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('profile.changePassword.fields.newPassword.label')}</FormLabel>
                  <FormControl>
                    <Input 
                      type="password"
                      showPasswordToggle={true}
                      {...field}
                      disabled={isSubmitting || isLoading}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            {/* Confirm Password */}
            <FormField
              control={form.control}
              name="confirm_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('profile.changePassword.fields.confirmPassword.label')}</FormLabel>
                  <FormControl>
                    <Input 
                      type="password"
                      showPasswordToggle={true}
                      {...field}
                      disabled={isSubmitting || isLoading}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          <div className={cn(
            "flex gap-2",
            isMobile ? "flex-row justify-between" : "flex-row justify-end"
          )}>
            {onClose && (
              <Button 
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isSubmitting || isLoading}
                className={cn(
                  isMobile ? "flex-1" : "w-auto"
                )}
              >
                {t('common.actions.cancel')}
              </Button>
            )}
            <Button 
              type="submit" 
              disabled={isSubmitting || isLoading}
              className={cn(
                isMobile ? "flex-1" : "w-auto"
              )}
            >
              {isSubmitting || isLoading ? (
                <span className="inline-flex items-center justify-center gap-2">
                  <Spinner className="size-4" />
                </span>
              ) : (
                t('common.actions.confirm')
              )}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}

export default ChangePasswordForm;