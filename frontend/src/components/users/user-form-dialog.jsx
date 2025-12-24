import * as React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useTranslation } from 'react-i18next';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Spinner } from '@/components/ui/spinner';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

// User form dialog component for creating and editing users
export function UserFormDialog({
  open,
  onOpenChange,
  user,
  onSubmit,
  isSubmitting = false,
  roles = [],
}) {
  const { t } = useTranslation();
  const isEditMode = !!user;

  // Build form validation schema
  const formSchema = React.useMemo(() => {
    const baseSchema = {
      first_name: z
        .string()
        .min(1, t('pages.profile.profile.fields.firstName.validation.required', 'First name is required')),
      last_name: z
        .string()
        .min(1, t('pages.profile.profile.fields.lastName.validation.required', 'Last name is required')),
      email: z
        .string()
        .min(1, t('pages.profile.profile.fields.email.validation.required', 'Email is required'))
        .transform((val) => val.trim().toLowerCase())
        .refine((val) => {
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          return emailRegex.test(val);
        }, {
          message: t('pages.profile.profile.fields.email.validation.invalid', 'Invalid email format'),
        }),
      phone: z
        .string()
        .min(1, t('pages.profile.profile.fields.phone.validation.required', 'Phone is required')),
      role: z.string().optional().nullable(),
      status: z.boolean().default(true),
    };

    // Add password field only for create mode
    if (!isEditMode) {
      baseSchema.password = z
        .string()
        .min(1, t('pages.auth.register.fields.password.validation.required', 'Password is required'))
        .min(6, t('pages.auth.register.fields.password.validation.minLength', 'Password must be at least 6 characters'));
    }

    return z.object(baseSchema);
  }, [t, isEditMode]);

  // Set default form values
  const defaultValues = React.useMemo(() => ({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    phone: user?.phone || '',
    password: '',
    role: user?.role || null,
    status: user?.status !== undefined ? user.status : true,
  }), [user?.id, user?.first_name, user?.last_name, user?.email, user?.phone, user?.role, user?.status]);

  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues,
  });

  // Reset form when user data changes
  React.useEffect(() => {
    const resetValues = user
      ? {
          first_name: user.first_name || '',
          last_name: user.last_name || '',
          email: user.email || '',
          phone: user.phone || '',
          password: '',
          role: user.role || null,
          status: user.status !== undefined ? user.status : true,
        }
      : {
          first_name: '',
          last_name: '',
          email: '',
          phone: '',
          password: '',
          role: null,
          status: true,
        };
    
    form.reset(resetValues, { keepDefaultValues: false });
  }, [user?.id, form]);

  // Handle form submission
  const handleSubmit = React.useCallback((formValues) => {
    if (onSubmit) {
      onSubmit(formValues);
    }
  }, [onSubmit]);

  // Handle form cancellation
  const handleCancel = React.useCallback(() => {
    if (onOpenChange) {
      onOpenChange(false);
    }
  }, [onOpenChange]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent showCloseButton={false} className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {isEditMode
              ? t('pages.usersManagement.dialog.editTitle', 'Edit User')
              : t('pages.usersManagement.dialog.createTitle', 'Create User')}
          </DialogTitle>
          <DialogDescription>
            {isEditMode
              ? t('pages.usersManagement.dialog.editDescription', 'Update user information')
              : t('pages.usersManagement.dialog.createDescription', 'Create a new user account')}
          </DialogDescription>
        </DialogHeader>
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
                      {t('pages.profile.profile.fields.firstName.label', 'First Name')}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        id="first_name"
                        name="first_name"
                        type="text"
                        autoComplete="given-name"
                        {...field}
                        disabled={isSubmitting}
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
                      {t('pages.profile.profile.fields.lastName.label', 'Last Name')}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        id="last_name"
                        name="last_name"
                        type="text"
                        autoComplete="family-name"
                        {...field}
                        disabled={isSubmitting}
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
                      {t('pages.auth.login.fields.email.label', 'Email')}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        id="email"
                        name="email"
                        type="email"
                        autoComplete="email"
                        {...field}
                        disabled={isSubmitting}
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
                      {t('pages.profile.profile.fields.phone.label', 'Phone')}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        id="phone"
                        name="phone"
                        type="tel"
                        autoComplete="tel"
                        {...field}
                        disabled={isSubmitting}
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
            {!isEditMode && (
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel
                      htmlFor="password"
                      className={cn(
                        'flex items-center gap-1',
                        form.formState.errors.password && 'text-destructive'
                      )}
                    >
                      {t('pages.auth.register.fields.password.label', 'Password')}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        id="password"
                        name="password"
                        type="password"
                        showPasswordToggle={true}
                        autoComplete="new-password"
                        {...field}
                        disabled={isSubmitting}
                        className={cn(
                          form.formState.errors.password &&
                            'ring-2 ring-destructive focus-visible:ring-destructive'
                        )}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}
            <div className="grid grid-cols-2 gap-5 md:gap-4 items-start">
              <FormField
                control={form.control}
                name="role"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel
                      htmlFor="role"
                      className={cn(
                        'flex items-center gap-1',
                        form.formState.errors.role && 'text-destructive'
                      )}
                    >
                      {t('pages.usersManagement.fields.role.label', 'Role')}
                    </FormLabel>
                    <FormControl>
                      <Select
                        name="role"
                        value={field.value ? field.value : '__none__'}
                        onValueChange={(value) => field.onChange(value === '__none__' ? null : value)}
                        disabled={isSubmitting}
                      >
                        <SelectTrigger
                          id="role"
                          className={cn(
                            form.formState.errors.role &&
                              'ring-2 ring-destructive focus-visible:ring-destructive'
                          )}
                        >
                          <SelectValue placeholder={t('common.actions.select', 'Select...')} />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="__none__">
                            {t('common.actions.none', 'None')}
                          </SelectItem>
                          {roles.length > 0 ? (
                            roles.map((role) => {
                              const roleName = role.name || role;
                              const roleValue = role.name || role;
                              return (
                                <SelectItem key={roleValue} value={roleValue}>
                                  {roleName}
                                </SelectItem>
                              );
                            })
                          ) : (
                            <SelectItem value="__loading__" disabled>
                              {t('common.status.loading', 'Loading...')}
                            </SelectItem>
                          )}
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="status"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel
                      htmlFor="status"
                      className={cn(
                        'flex items-center gap-1',
                        form.formState.errors.status && 'text-destructive'
                      )}
                    >
                      {t('pages.profile.fields.status.label', 'Status')}
                      <span className="text-destructive">*</span>
                    </FormLabel>
                    <FormControl>
                      <Select
                        name="status"
                        value={field.value ? 'true' : 'false'}
                        onValueChange={(value) => field.onChange(value === 'true')}
                        disabled={isSubmitting}
                      >
                        <SelectTrigger
                          id="status"
                          className={cn(
                            form.formState.errors.status &&
                              'ring-2 ring-destructive focus-visible:ring-destructive'
                          )}
                        >
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="true">
                            {t('pages.profile.fields.status.values.active', 'Active')}
                          </SelectItem>
                          <SelectItem value="false">
                            {t('pages.profile.fields.status.values.inactive', 'Inactive')}
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                disabled={isSubmitting}
                className="text-sm"
              >
                {t('common.actions.cancel', 'Cancel')}
              </Button>
              <Button
                type="submit"
                disabled={isSubmitting}
                className="text-sm"
              >
                {isSubmitting ? (
                  <span className="inline-flex items-center justify-center gap-2">
                    <Spinner className="size-4" />
                  </span>
                ) : (
                  isEditMode
                    ? t('common.actions.save', 'Save')
                    : t('common.actions.create', 'Create')
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

export default UserFormDialog;