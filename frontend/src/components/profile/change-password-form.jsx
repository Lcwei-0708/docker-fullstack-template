import { useState, useCallback, useMemo, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { Check } from 'lucide-react';
import { cn, debugError } from '@/lib/utils';
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
import { Progress } from '@/components/ui/progress';
import { useAuth } from '@/hooks/useAuth';
import { useIsMobile } from '@/hooks/useMobile';

export function ChangePasswordForm({ onSuccess, onClose, onSubmittingChange }) {
  const { t } = useTranslation();
  const { changePassword, isLoading } = useAuth();
  const isMobile = useIsMobile();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  useEffect(() => {
    if (onSubmittingChange) {
      onSubmittingChange(isSubmitting || isLoading);
    }
  }, [isSubmitting, isLoading, onSubmittingChange]);

  const formSchema = useMemo(() => {
    return z.object({
      current_password: z
        .string()
        .min(1, { message: t('pages.profile.security.fields.currentPassword.validation.required') })
        .min(6, { message: t('pages.profile.security.fields.currentPassword.validation.minLength') }),
      new_password: z
        .string()
        .min(1, { message: t('pages.profile.security.fields.newPassword.validation.required') })
        .min(6, { message: t('pages.profile.security.fields.newPassword.validation.minLength') }),
    });
  }, [t]);

  const defaultValues = useMemo(() => ({
    current_password: '',
    new_password: '',
  }), []);

  const checkPasswordStrength = useCallback((password) => {
    let strength = 0;
    if (password.length >= 8) strength += 25;
    if (password.match(/[A-Z]/)) strength += 25;
    if (password.match(/[0-9]/)) strength += 25;
    if (password.match(/[^A-Za-z0-9]/)) strength += 25;
    setPasswordStrength(strength);
  }, []);

  const strengthConfig = useMemo(() => {
    if (passwordStrength < 50) {
      return {
        label: t('pages.profile.security.fields.newPassword.strength.weak'),
        textColor: 'text-destructive',
        barColor: '[&>div]:bg-destructive dark:[&>div]:bg-destructive',
      };
    }
    if (passwordStrength < 75) {
      return {
        label: t('pages.profile.security.fields.newPassword.strength.medium'),
        textColor: 'text-warning',
        barColor: '[&>div]:bg-warning dark:[&>div]:bg-warning',
      };
    }
    if (passwordStrength < 100) {
      return {
        label: t('pages.profile.security.fields.newPassword.strength.strong'),
        textColor: 'text-success',
        barColor: '[&>div]:bg-success dark:[&>div]:bg-success',
      };
    }
    return {
      label: t('pages.profile.security.fields.newPassword.strength.veryStrong'),
      textColor: 'text-success',
      barColor: '[&>div]:bg-success dark:[&>div]:bg-success',
    };
  }, [passwordStrength, t]);

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
        setPasswordStrength(0);
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
            message: t('pages.profile.security.fields.currentPassword.validation.incorrect'),
          });
        } else {
          toast.error(errorMessage || t('pages.profile.security.messages.incorrect'));
        }
      }
    } catch (error) {
      debugError('Change password error:', error);
      
      if (error.isPasswordError) {
        const errorMessage = t('pages.profile.security.fields.currentPassword.validation.incorrect');
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
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-4 items-start">
            <FormField
              control={form.control}
              name="current_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel
                    htmlFor="current_password-input"
                    className={cn(
                      'flex items-center gap-1',
                      form.formState.errors.current_password && 'text-destructive'
                    )}
                  >
                    {t('pages.profile.security.fields.currentPassword.label')}
                    <span className="text-destructive">*</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      id="current_password-input"
                      type="password"
                      autoComplete="current-password"
                      showPasswordToggle={true}
                      {...field}
                      disabled={isSubmitting || isLoading}
                      className={cn(
                        form.formState.errors.current_password &&
                          'ring-2 ring-destructive focus-visible:ring-destructive'
                      )}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="new_password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel
                    htmlFor="new_password-input"
                    className={cn(
                      'flex items-center gap-1',
                      form.formState.errors.new_password && 'text-destructive'
                    )}
                  >
                    {t('pages.profile.security.fields.newPassword.label')}
                    <span className="text-destructive">*</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      id="new_password-input"
                      type="password"
                      autoComplete="new-password"
                      showPasswordToggle={true}
                      {...field}
                      disabled={isSubmitting || isLoading}
                      className={cn(
                        form.formState.errors.new_password &&
                          'ring-2 ring-destructive focus-visible:ring-destructive'
                      )}
                      onChange={(e) => {
                        field.onChange(e);
                        checkPasswordStrength(e.target.value);
                      }}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <div className="space-y-1.5 md:space-y-2">
            <div className="flex justify-between text-sm text-foreground">
              <span className={strengthConfig.textColor}>
                {strengthConfig.label}
              </span>
            </div>
            <Progress
              value={passwordStrength}
              className={cn(
                'h-2 w-full bg-muted',
                strengthConfig.barColor
              )}
            />
            <ul className="text-sm text-muted-foreground space-y-1 mt-2 md:mt-3">
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full flex-shrink-0 bg-muted-foreground" />
                <span className={cn(
                  form.watch('new_password')?.length >= 8 && 'text-success'
                )}>
                  {t('pages.profile.security.fields.newPassword.validation.minLength')}
                </span>
                {form.watch('new_password')?.length >= 8 && (
                  <Check className="size-4 text-success flex-shrink-0" />
                )}
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full flex-shrink-0 bg-muted-foreground" />
                <span className={cn(
                  form.watch('new_password')?.match(/[A-Z]/) && 'text-success'
                )}>
                  {t('pages.profile.security.fields.newPassword.strength.uppercase')}
                </span>
                {form.watch('new_password')?.match(/[A-Z]/) && (
                  <Check className="size-4 text-success flex-shrink-0" />
                )}
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full flex-shrink-0 bg-muted-foreground" />
                <span className={cn(
                  form.watch('new_password')?.match(/[0-9]/) && 'text-success'
                )}>
                  {t('pages.profile.security.fields.newPassword.strength.number')}
                </span>
                {form.watch('new_password')?.match(/[0-9]/) && (
                  <Check className="size-4 text-success flex-shrink-0" />
                )}
              </li>
              <li className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full flex-shrink-0 bg-muted-foreground" />
                <span className={cn(
                  form.watch('new_password')?.match(/[^A-Za-z0-9]/) && 'text-success'
                )}>
                  {t('pages.profile.security.fields.newPassword.strength.special')}
                </span>
                {form.watch('new_password')?.match(/[^A-Za-z0-9]/) && (
                  <Check className="size-4 text-success flex-shrink-0" />
                )}
              </li>
            </ul>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-4 md:mt-6">
          {onClose && (
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={isSubmitting || isLoading}
              className="flex items-center gap-1.5 md:gap-2 text-sm"
            >
              {t('common.actions.cancel')}
            </Button>
          )}
          <Button
            type="submit"
            disabled={isSubmitting || isLoading}
            className="flex items-center gap-1.5 md:gap-2 text-sm"
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
  );
}

export default ChangePasswordForm;