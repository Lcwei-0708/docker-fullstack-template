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

export function UpdateProfileForm({ user, onSuccess, onClose, onSubmittingChange }) {
  const { t } = useTranslation();
  const { updateUserProfile, isLoading } = useAuth();
  const isMobile = useMobile();
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (onSubmittingChange) {
      onSubmittingChange(isSubmitting || isLoading);
    }
  }, [isSubmitting, isLoading, onSubmittingChange]);

  const formSchema = useMemo(() => {
    return z.object({
      first_name: z
        .string()
        .min(1, t('profile.updateProfile.fields.firstName.validation.required')),
      last_name: z
        .string()
        .min(1, t('profile.updateProfile.fields.lastName.validation.required')),
      email: z
        .string()
        .min(1, t('profile.updateProfile.fields.email.validation.required'))
        .transform((val) => val.trim().toLowerCase())
        .refine((val) => {
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          return emailRegex.test(val);
        }, {
          message: t('profile.updateProfile.fields.email.validation.invalid'),
        }),
      phone: z
        .string()
        .min(1, t('profile.updateProfile.fields.phone.validation.required')),
    });
  }, [t]);

  const defaultValues = useMemo(() => ({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    phone: user?.phone || '',
  }), [user]);

  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues,
  });

  useEffect(() => {
    if (user) {
      form.reset({
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
      });
    }
  }, [user, form]);

  const handleSubmit = useCallback(async (formValues) => {
    setIsSubmitting(true);
    
    try {
      const result = await updateUserProfile({
        first_name: formValues.first_name,
        last_name: formValues.last_name,
        email: formValues.email,
        phone: formValues.phone,
      });
      
      if (result.success) {
        if (onSuccess) {
          await onSuccess(result.data);
        }
      }
    } catch (error) {
      console.error('Update profile error:', error);
    } finally {
      setIsSubmitting(false);
    }
  }, [updateUserProfile, onSuccess]);

  return (
    <div className="space-y-6">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="first_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t('profile.updateProfile.fields.firstName.label')}</FormLabel>
                    <FormControl>
                      <Input 
                        type="text"
                        {...field}
                        disabled={isSubmitting || isLoading}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="last_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{t('profile.updateProfile.fields.lastName.label')}</FormLabel>
                    <FormControl>
                      <Input 
                        type="text"
                        {...field}
                        disabled={isSubmitting || isLoading}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('profile.updateProfile.fields.email.label')}</FormLabel>
                  <FormControl>
                    <Input 
                      type="email"
                      {...field}
                      disabled={isSubmitting || isLoading}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t('profile.updateProfile.fields.phone.label')}</FormLabel>
                  <FormControl>
                    <Input 
                      type="tel"
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
                t('common.actions.save')
              )}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}

export default UpdateProfileForm;