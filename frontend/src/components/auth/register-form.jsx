import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { cn, debugWarn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/hooks/useAuth'
import { debugError } from '@/lib/utils'
import { Spinner } from '@/components/ui/spinner'
import { useIsMobile } from '@/hooks/useMobile'

const RegisterButton = React.memo(({ onSubmit, t, className, isSubmitting }) => {
  return (
    <Button 
      className={cn("w-full min-h-[40px]", className)} 
      type="button" 
      onClick={onSubmit}
      disabled={isSubmitting}
    >
      <span className="inline-flex items-center justify-center gap-2 min-w-[120px]">
        {isSubmitting ? <Spinner className="size-4" /> : t('pages.auth.register.actions.submit', { defaultValue: 'Sign up' })}
      </span>
    </Button>
  )
})

RegisterButton.displayName = 'RegisterButton'

export const RegisterForm = ({ className, redirectTo = '/', ...props }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const authContext = useAuth()
  const isMobile = useIsMobile()
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const register = useMemo(() => authContext.register, [authContext.register])
  const clearError = useMemo(() => authContext.clearError, [authContext.clearError])
  
  const handleRegister = useCallback(async (userData) => {
    clearError()
    return await register(userData)
  }, [register, clearError])
  
  const handleRegisterRef = useRef(handleRegister)
  useEffect(() => {
    handleRegisterRef.current = handleRegister
  }, [handleRegister])

  const formSchema = useMemo(() => {
    return z.object({
      first_name: z
        .string()
        .min(1, t('pages.auth.register.fields.firstName.validation.required', { defaultValue: 'Please enter your first name' })),
      last_name: z
        .string()
        .min(1, t('pages.auth.register.fields.lastName.validation.required', { defaultValue: 'Please enter your last name' })),
      email: z
        .string()
        .min(1, t('pages.auth.register.fields.email.validation.required', { defaultValue: 'Please enter your email' }))
        .transform((val) => val.trim().toLowerCase())
        .refine((val) => {
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
          return emailRegex.test(val)
        }, {
          message: t('pages.auth.register.fields.email.validation.invalid', { defaultValue: 'Please enter a valid email format' }),
        }),
      phone: z
        .string()
        .min(1, t('pages.auth.register.fields.phone.validation.required', { defaultValue: 'Please enter your phone number' })),
      password: z
        .string()
        .min(1, t('pages.auth.register.fields.password.validation.required', { defaultValue: 'Please enter your password' }))
        .min(6, t('pages.auth.register.fields.password.validation.minLength', { defaultValue: 'Password must be at least 6 characters' })),
      confirm_password: z
        .string()
        .min(1, t('pages.auth.register.fields.confirmPassword.validation.required', { defaultValue: 'Please confirm your password' })),
    }).refine((data) => data.password === data.confirm_password, {
      message: t('pages.auth.register.fields.confirmPassword.validation.notMatch', { defaultValue: 'Passwords do not match' }),
      path: ['confirm_password'],
    })
  }, [t])

  const stableDefaultValues = useMemo(() => ({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    password: '',
    confirm_password: '',
  }), [])

  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: stableDefaultValues,
  })

  useEffect(() => {
    try {
      form.clearErrors()
      const newResolver = zodResolver(formSchema)
      
      if (form._options && typeof form._options === 'object' && 'resolver' in form._options) {
        form._options.resolver = newResolver
      }
      
      if ('_resolver' in form && form._resolver !== undefined) {
        form._resolver = newResolver
      }
      
      if (form.formState.isSubmitted) {
        setTimeout(() => {
          form.trigger()
        }, 0)
      }
    } catch (error) {
      debugWarn('Failed to update form resolver:', error)
      form.clearErrors()
      if (form.formState.isSubmitted) {
        setTimeout(() => {
          form.trigger()
        }, 0)
      }
    }
  }, [formSchema, form])

  const formMethodsRef = useRef(form)
  useEffect(() => {
    formMethodsRef.current = form
  }, [form])

  const navigateRef = useRef(navigate)
  const tRef = useRef(t)
  const redirectToRef = useRef(redirectTo)
  
  useEffect(() => {
    navigateRef.current = navigate
    tRef.current = t
    redirectToRef.current = redirectTo
  }, [navigate, t, redirectTo])
  
  const handleSubmit = useCallback(async (formValues) => {
    const data = {
      first_name: formValues.first_name,
      last_name: formValues.last_name,
      email: formValues.email,
      phone: formValues.phone,
      password: formValues.password,
    }
    
    setIsSubmitting(true)
    
    try {
      const result = await handleRegisterRef.current(data)
      
      if (result.success) {
        formMethodsRef.current.reset(stableDefaultValues, { keepValues: false })
        setTimeout(() => {
          navigateRef.current(redirectToRef.current, { replace: true })
        }, 0)
      } else {
        setIsSubmitting(false)
      }
    } catch (error) {
      debugError('Register error:', error)
      setIsSubmitting(false)
    }
  }, [stableDefaultValues])

  const onSubmitHandler = useCallback((e) => {
    e?.preventDefault?.()
    formMethodsRef.current.handleSubmit(handleSubmit)()
  }, [handleSubmit])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !isSubmitting) {
      e.preventDefault()
      onSubmitHandler(e)
    }
  }, [onSubmitHandler, isSubmitting])

  const firstNameInputRef = useRef(null)
  useEffect(() => {
    if (!isMobile && firstNameInputRef.current) {
      firstNameInputRef.current.focus()
    }
  }, [isMobile])

  return (
    <Form {...form}>
      <form
        className={cn('space-y-6', className)}
        onKeyDown={handleKeyDown}
        {...props}
      >
        <div className="grid grid-cols-2 gap-4 items-start">
          <FormField
            control={form.control}
            name="first_name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('pages.auth.register.fields.firstName.label', { defaultValue: 'First Name' })}</FormLabel>
                <FormControl>
                  <Input 
                    type="text"
                    placeholder="" 
                    {...field}
                    ref={(e) => {
                      firstNameInputRef.current = e
                      field.ref(e)
                    }}
                    disabled={isSubmitting} 
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
                <FormLabel>{t('pages.auth.register.fields.lastName.label', { defaultValue: 'Last Name' })}</FormLabel>
                <FormControl>
                  <Input 
                    type="text"
                    placeholder="" 
                    {...field}
                    disabled={isSubmitting} 
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
              <FormLabel>{t('pages.auth.register.fields.email.label', { defaultValue: 'Email' })}</FormLabel>
              <FormControl>
                <Input 
                  type="email"
                  placeholder="" 
                  {...field}
                  disabled={isSubmitting} 
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
              <FormLabel>{t('pages.auth.register.fields.phone.label', { defaultValue: 'Phone' })}</FormLabel>
              <FormControl>
                <Input 
                  type="tel"
                  placeholder="" 
                  {...field}
                  disabled={isSubmitting} 
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <div className="grid grid-cols-2 gap-4 items-start">
          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('pages.auth.register.fields.password.label', { defaultValue: 'Password' })}</FormLabel>
                <FormControl>
                  <Input 
                    type="password"
                    showPasswordToggle={true}
                    placeholder="" 
                    {...field} 
                    disabled={isSubmitting} 
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <FormField
            control={form.control}
            name="confirm_password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>{t('pages.auth.register.fields.confirmPassword.label', { defaultValue: 'Confirm Password' })}</FormLabel>
                <FormControl>
                  <Input 
                    type="password"
                    showPasswordToggle={true}
                    placeholder="" 
                    {...field} 
                    disabled={isSubmitting} 
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>
        
        <RegisterButton 
          onSubmit={onSubmitHandler} 
          t={t} 
          className={cn('mt-4')}
          isSubmitting={isSubmitting}
        />
        
        <div className="text-center text-sm flex items-center justify-center gap-2">
          <span className="text-muted-foreground">{t('pages.auth.register.links.existingUser', { defaultValue: 'Already have an account? ' })}</span>
          <Link 
            to="/login" 
            className="font-medium text-primary hover:underline"
            state={location.state}
          >
            {t('pages.auth.register.links.login', { defaultValue: 'Sign in' })}
          </Link>
        </div>
      </form>
    </Form>
  )
}

export default RegisterForm