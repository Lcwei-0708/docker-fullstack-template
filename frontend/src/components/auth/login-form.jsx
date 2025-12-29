import React, { useState, useCallback, useMemo, useEffect, useLayoutEffect, useRef } from 'react'
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

const LoginButton = React.memo(({ onSubmit, t, className, isSubmitting }) => {
  return (
    <Button 
      className={cn("w-full min-h-[40px]", className)} 
      type="button" 
      onClick={onSubmit}
      disabled={isSubmitting}
    >
      <span className="inline-flex items-center justify-center gap-2 min-w-[120px]">
        {isSubmitting ? <Spinner className="size-4" /> : t('pages.auth.login.actions.submit', { defaultValue: 'Sign in' })}
      </span>
    </Button>
  )
})

LoginButton.displayName = 'LoginButton'

const emailPersistRef = { current: '' }
const formInstanceRef = { current: null }

export const LoginForm = ({ className, redirectTo = '/', ...props }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const authContext = useAuth()
  const isMobile = useIsMobile()
  const [isSubmitting, setIsSubmitting] = useState(false)
  
  const login = useMemo(() => authContext.login, [authContext.login])
  const clearError = useMemo(() => authContext.clearError, [authContext.clearError])
  
  const handleLogin = useCallback(async (credentials) => {
    clearError()
    return await login(credentials)
  }, [login, clearError])
  
  const emailRef = useRef(emailPersistRef.current)
  const emailInputRef = useRef(null)
  const [emailValue, setEmailValue] = useState(() => {
    const storedEmail = emailPersistRef.current
    if (storedEmail) {
      emailRef.current = storedEmail
    }
    return storedEmail || ''
  })
  
  const handleLoginRef = useRef(handleLogin)
  useEffect(() => {
    handleLoginRef.current = handleLogin
  }, [handleLogin])

  const formSchema = useMemo(() => {
    return z.object({
      email: z
        .string()
        .min(1, t('pages.auth.login.fields.email.validation.required', { defaultValue: 'Please enter your email' }))
        .refine((val) => {
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
          return emailRegex.test(val)
        }, {
          message: t('pages.auth.login.fields.email.validation.invalid', { defaultValue: 'Please enter a valid email format' }),
        }),
      password: z
        .string()
        .min(1, t('pages.auth.login.fields.password.validation.required', { defaultValue: 'Please enter your password' }))
        .min(6, t('pages.auth.login.fields.password.validation.minLength', { defaultValue: 'Password must be at least 6 characters' })),
    })
  }, [t])

  const stableDefaultValues = useMemo(() => ({
    email: emailPersistRef.current || '',
    password: '',
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

  useEffect(() => {
    if (!formInstanceRef.current) {
      formInstanceRef.current = form
    }
  }, [form])

  const formMethodsRef = useRef(form)
  useEffect(() => {
    formMethodsRef.current = form
  }, [form])
  
  useEffect(() => {
    if (emailPersistRef.current) {
      const currentEmail = form.getValues('email')
      if (currentEmail !== emailPersistRef.current) {
        form.setValue('email', emailPersistRef.current, { shouldValidate: false, shouldDirty: false, shouldTouch: false })
      }
    }
  }, [form])

  useLayoutEffect(() => {
    const storedEmail = emailPersistRef.current
    if (storedEmail) {
      if (emailRef.current !== storedEmail || emailValue !== storedEmail) {
        emailRef.current = storedEmail
        setEmailValue(storedEmail)
        if (formMethodsRef.current) {
          formMethodsRef.current.setValue('email', storedEmail, { shouldValidate: false, shouldDirty: false, shouldTouch: false })
        }
      }
    }
  }, [emailValue])

  useEffect(() => {
    const subscription = form.watch((value, { name, type }) => {
      if (name === 'email' && value.email !== undefined && type === 'change') {
        const currentEmail = value.email
        if (currentEmail !== emailRef.current && (currentEmail || !emailPersistRef.current)) {
          emailRef.current = currentEmail
          emailPersistRef.current = currentEmail
          setEmailValue(currentEmail)
        }
      }
    })
    return () => {
      subscription.unsubscribe()
    }
  }, [form])

  const navigateRef = useRef(navigate)
  const tRef = useRef(t)
  const redirectToRef = useRef(redirectTo)
  
  useEffect(() => {
    navigateRef.current = navigate
    tRef.current = t
    redirectToRef.current = redirectTo
  }, [navigate, t, redirectTo])
  
  const setEmailValueRef = useRef(setEmailValue)
  useEffect(() => {
    setEmailValueRef.current = setEmailValue
  }, [setEmailValue])
  
  const handleSubmit = useCallback(async (formValues) => {
    const currentEmail = formValues.email || emailRef.current || emailPersistRef.current
    
    emailRef.current = currentEmail
    emailPersistRef.current = currentEmail
    
    const data = {
      email: currentEmail,
      password: formValues.password,
    }
    
    setIsSubmitting(true)
    
    try {
      const result = await handleLoginRef.current(data)
      
      if (result.success) {
        emailRef.current = ''
        emailPersistRef.current = ''
        setEmailValueRef.current('')
        formMethodsRef.current.reset({ email: '', password: '' }, { keepValues: false })
        setTimeout(() => {
          navigateRef.current(redirectToRef.current, { replace: true })
        }, 0)
      } else if (result.requiresPasswordReset && result.resetToken) {
        // Redirect to reset password page with token
        emailRef.current = ''
        emailPersistRef.current = ''
        setEmailValueRef.current('')
        formMethodsRef.current.reset({ email: '', password: '' }, { keepValues: false })
        setTimeout(() => {
          navigateRef.current(`/reset-password?token=${encodeURIComponent(result.resetToken)}`, { replace: true })
        }, 0)
      } else {
        const emailToKeep = formValues.email || emailRef.current || emailPersistRef.current
        
        emailRef.current = emailToKeep
        emailPersistRef.current = emailToKeep
        
        formMethodsRef.current.setValue('password', '', { shouldValidate: false, shouldDirty: false, shouldTouch: false })
        
        setEmailValueRef.current(prev => prev !== emailToKeep ? emailToKeep : prev)
        
        setIsSubmitting(false)
      }
    } catch (error) {
      debugError('Login error:', error)
      const emailToKeep = formValues.email || emailRef.current || emailPersistRef.current
      
      emailRef.current = emailToKeep
      emailPersistRef.current = emailToKeep
      
      formMethodsRef.current.setValue('password', '', { shouldValidate: false, shouldDirty: false, shouldTouch: false })
      
      setEmailValueRef.current(prev => prev !== emailToKeep ? emailToKeep : prev)
      
      setIsSubmitting(false)
    }
  }, [])

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

  useEffect(() => {
    if (!isMobile && emailInputRef.current) {
      emailInputRef.current.focus()
    }
  }, [isMobile])

  return (
    <Form {...form}>
      <form
        className={cn('space-y-6', className)}
        onKeyDown={handleKeyDown}
        {...props}
      >
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t('pages.auth.login.fields.email.label', { defaultValue: 'Email' })}</FormLabel>
              <FormControl>
                <Input 
                  type="email"
                  placeholder="" 
                  {...field}
                  value={emailValue || field.value || ''}
                  onChange={(e) => {
                    const newValue = e.target.value
                    emailRef.current = newValue
                    emailPersistRef.current = newValue
                    setEmailValue(newValue)
                    field.onChange(e)
                  }}
                  onBlur={field.onBlur}
                  name={field.name}
                  ref={(e) => {
                    emailInputRef.current = e
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
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t('pages.auth.login.fields.password.label', { defaultValue: 'Password' })}</FormLabel>
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
        
        <LoginButton 
          onSubmit={onSubmitHandler} 
          t={t} 
          className={cn('mt-4')}
          isSubmitting={isSubmitting}
        />
        
        <div className="text-center text-sm flex items-center justify-center gap-2">
          <span className="text-muted-foreground">{t('pages.auth.login.links.newUser', { defaultValue: 'New user? ' })}</span>
          <Link 
            to="/register" 
            className="font-medium text-primary hover:underline"
            state={location.state}
          >
            {t('pages.auth.login.links.register', { defaultValue: 'Sign up' })}
          </Link>
        </div>
      </form>
    </Form>
  )
}

export default LoginForm