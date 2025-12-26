import { useState, useCallback, useMemo, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
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
import { useAuth } from '@/hooks/useAuth';
import { useIsMobile } from '@/hooks/useMobile';

export function UpdateProfileForm({ user, onSuccess, onClose, onSubmittingChange }) {
  const { t } = useTranslation();
  const { updateUserProfile, isLoading } = useAuth();
  const isMobile = useIsMobile();
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
        .min(1, t('pages.profile.profile.fields.firstName.validation.required')),
      last_name: z
        .string()
        .min(1, t('pages.profile.profile.fields.lastName.validation.required')),
      email: z
        .string()
        .min(1, t('pages.profile.profile.fields.email.validation.required'))
        .transform((val) => val.trim().toLowerCase())
        .refine((val) => {
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          return emailRegex.test(val);
        }, {
          message: t('pages.profile.profile.fields.email.validation.invalid'),
        }),
      phone: z
        .string()
        .min(1, t('pages.profile.profile.fields.phone.validation.required')),
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
      } else {
        toast.error(result.error || t('common.status.error'));
      }
    } catch (error) {
      debugError('Update profile error:', error);
      toast.error(error.message || t('common.status.error'));
    } finally {
      setIsSubmitting(false);
    }
  }, [updateUserProfile, onSuccess]);

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-5 md:space-y-4 text-sm">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-4 items-start">
          <FormField
            control={form.control}
            name="first_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel
                  htmlFor="first_name"
                  className={cn(
                    'flex items-center gap-1',
                    form.formState.errors.first_name && 'text-destructive'
                  )}
                >
                  {t('pages.profile.profile.fields.firstName.label')}
                  <span className="text-destructive">*</span>
                </FormLabel>
                <FormControl>
                  <Input
                    id="first_name"
                    type="text"
                    {...field}
                    disabled={isSubmitting || isLoading}
                    className={cn(
                      form.formState.errors.first_name &&
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
            name="last_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel
                  htmlFor="last_name"
                  className={cn(
                    'flex items-center gap-1',
                    form.formState.errors.last_name && 'text-destructive'
                  )}
                >
                  {t('pages.profile.profile.fields.lastName.label')}
                  <span className="text-destructive">*</span>
                </FormLabel>
                <FormControl>
                  <Input
                    id="last_name"
                    type="text"
                    {...field}
                    disabled={isSubmitting || isLoading}
                    className={cn(
                      form.formState.errors.last_name &&
                        'ring-2 ring-destructive focus-visible:ring-destructive'
                    )}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-4 items-start">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel
                  htmlFor="email"
                  className={cn(
                    'flex items-center gap-1',
                    form.formState.errors.email && 'text-destructive'
                  )}
                >
                  {t('pages.profile.profile.fields.email.label')}
                  <span className="text-destructive">*</span>
                </FormLabel>
                <FormControl>
                  <Input
                    id="email"
                    type="email"
                    autoComplete="email"
                    {...field}
                    disabled={isSubmitting || isLoading}
                    className={cn(
                      form.formState.errors.email &&
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
            name="phone"
            render={({ field }) => (
              <FormItem>
                <FormLabel
                  htmlFor="phone"
                  className={cn(
                    'flex items-center gap-1',
                    form.formState.errors.phone && 'text-destructive'
                  )}
                >
                  {t('pages.profile.profile.fields.phone.label')}
                  <span className="text-destructive">*</span>
                </FormLabel>
                <FormControl>
                  <Input
                    id="phone"
                    type="tel"
                    autoComplete="tel"
                    {...field}
                    disabled={isSubmitting || isLoading}
                    className={cn(
                      form.formState.errors.phone &&
                        'ring-2 ring-destructive focus-visible:ring-destructive'
                    )}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
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
              t('common.actions.save')
            )}
          </Button>
        </div>
      </form>
    </Form>
  );
}

export default UpdateProfileForm;