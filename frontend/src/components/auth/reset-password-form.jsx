import React, { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { cn, debugWarn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { LogIn } from 'lucide-react'
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

const ResetPasswordButton = React.memo(({ onSubmit, t, className, isSubmitting }) => {
  return (
    <Button 
      className={cn("w-full min-h-[40px]", className)} 
      type="button" 
      onClick={onSubmit}
      disabled={isSubmitting}
    >
      <span className="inline-flex items-center justify-center gap-2 min-w-[120px]">
        {isSubmitting ? <Spinner className="size-4" /> : t('pages.auth.resetPassword.actions.submit', { defaultValue: 'Reset Password' })}
      </span>
    </Button>
  )
})

ResetPasswordButton.displayName = 'ResetPasswordButton'

export const ResetPasswordForm = ({ className, token, ...props }) => {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const authContext = useAuth()
  const isMobile = useIsMobile()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isValidatingToken, setIsValidatingToken] = useState(true)
  const [tokenValid, setTokenValid] = useState(false)
  
  const resetPassword = useMemo(() => authContext.resetPassword, [authContext.resetPassword])
  const validateResetToken = useMemo(() => authContext.validateResetToken, [authContext.validateResetToken])
  const clearError = useMemo(() => authContext.clearError, [authContext.clearError])
  
  const handleResetPassword = useCallback(async (newPassword, resetToken) => {
    clearError()
    return await resetPassword(newPassword, resetToken)
  }, [resetPassword, clearError])
  
  const handleResetPasswordRef = useRef(handleResetPassword)
  useEffect(() => {
    handleResetPasswordRef.current = handleResetPassword
  }, [handleResetPassword])

  // Track if token validation has been initiated
  const validationInitiatedRef = useRef(false)
  const lastValidatedTokenRef = useRef(null)

  // Validate token on mount or when token changes
  useEffect(() => {
    // Skip if no token
    if (!token) {
      setIsValidatingToken(false)
      setTokenValid(false)
      validationInitiatedRef.current = false
      lastValidatedTokenRef.current = null
      return
    }

    // Skip if already validating or already validated this token
    if (validationInitiatedRef.current && lastValidatedTokenRef.current === token) {
      return
    }

    // Mark as initiated and store the token being validated
    validationInitiatedRef.current = true
    lastValidatedTokenRef.current = token

    const validateToken = async () => {
      setIsValidatingToken(true)
      try {
        const result = await validateResetToken(token)
        if (result.success) {
          setTokenValid(true)
        } else {
          setTokenValid(false)
          validationInitiatedRef.current = false
          lastValidatedTokenRef.current = null
        }
      } catch (error) {
        debugError('Token validation error:', error)
        setTokenValid(false)
        validationInitiatedRef.current = false
        lastValidatedTokenRef.current = null
      } finally {
        setIsValidatingToken(false)
      }
    }

    validateToken()
  }, [token, validateResetToken, t])
  
  const formSchema = useMemo(() => {
    return z.object({
      password: z
        .string()
        .min(1, t('pages.auth.resetPassword.fields.password.validation.required', { defaultValue: 'Please enter your new password' }))
        .min(6, t('pages.auth.resetPassword.fields.password.validation.minLength', { defaultValue: 'Password must be at least 6 characters' })),
      confirm_password: z
        .string()
        .min(1, t('pages.auth.resetPassword.fields.confirmPassword.validation.required', { defaultValue: 'Please confirm your new password' })),
    }).refine((data) => data.password === data.confirm_password, {
      message: t('pages.auth.resetPassword.fields.confirmPassword.validation.notMatch', { defaultValue: 'Passwords do not match' }),
      path: ['confirm_password'],
    })
  }, [t])

  const stableDefaultValues = useMemo(() => ({
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
  
  useEffect(() => {
    navigateRef.current = navigate
    tRef.current = t
  }, [navigate, t])
  
  const handleSubmit = useCallback(async (formValues) => {
    if (!token || !tokenValid) {
      return
    }
    
    setIsSubmitting(true)
    
    try {
      const result = await handleResetPasswordRef.current(formValues.password, token)
      
      if (result.success) {
        formMethodsRef.current.reset(stableDefaultValues, { keepValues: false })
        setTimeout(() => {
          navigateRef.current('/', { replace: true })
        }, 0)
      } else {
        // Check if error is 401 (token expired/invalid)
        if (result.status === 401) {
          setTokenValid(false)
        }
        setIsSubmitting(false)
      }
    } catch (error) {
      debugError('Reset password error:', error)
      // Check if error is 401 (token expired/invalid)
      if (error.response?.status === 401) {
        setTokenValid(false)
      }
      setIsSubmitting(false)
    }
  }, [token, tokenValid, stableDefaultValues])

  const onSubmitHandler = useCallback((e) => {
    e?.preventDefault?.()
    if (!tokenValid) {
      return
    }
    formMethodsRef.current.handleSubmit(handleSubmit)()
  }, [handleSubmit, tokenValid])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !isSubmitting && tokenValid) {
      e.preventDefault()
      onSubmitHandler(e)
    }
  }, [onSubmitHandler, isSubmitting, tokenValid])

  const passwordInputRef = useRef(null)
  useEffect(() => {
    if (!isMobile && passwordInputRef.current && tokenValid) {
      passwordInputRef.current.focus()
    }
  }, [isMobile, tokenValid])

  // Show loading state while validating token
  if (isValidatingToken) {
    return (
      <div className={cn('space-y-6 flex items-center justify-center py-8', className)}>
        <div className="flex flex-col items-center gap-4">
          <Spinner className="size-8" />
        </div>
      </div>
    )
  }

  // Show error if token is invalid
  if (!tokenValid) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="text-center">
          <p className="text-muted-foreground text-sm">
            {t('pages.auth.resetPassword.messages.invalidToken', { defaultValue: 'The reset password link has expired or is invalid. Please request a new one.' })}
          </p>
        </div>
        <div className="flex justify-center pt-2">
          <Button asChild className="gap-2 text-sm">
            <Link to="/login">
              <LogIn className="w-4 h-4" />
              {t('pages.auth.resetPassword.actions.backToLogin', { defaultValue: 'Back to Login' })}
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  return (
    <Form {...form}>
      <form
        className={cn('space-y-6', className)}
        onKeyDown={handleKeyDown}
        {...props}
      >
        <FormField
          control={form.control}
          name="password"
          render={({ field }) => (
            <FormItem>
              <FormLabel>{t('pages.auth.resetPassword.fields.password.label', { defaultValue: 'New Password' })}</FormLabel>
              <FormControl>
                <Input 
                  type="password"
                  showPasswordToggle={true}
                  placeholder="" 
                  {...field} 
                  ref={(e) => {
                    passwordInputRef.current = e
                    field.ref(e)
                  }}
                  disabled={isSubmitting || !tokenValid} 
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
              <FormLabel>{t('pages.auth.resetPassword.fields.confirmPassword.label', { defaultValue: 'Confirm New Password' })}</FormLabel>
              <FormControl>
                <Input 
                  type="password"
                  showPasswordToggle={true}
                  placeholder="" 
                  {...field} 
                  disabled={isSubmitting || !tokenValid} 
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <ResetPasswordButton 
          onSubmit={onSubmitHandler} 
          t={t} 
          className={cn('mt-4')}
          isSubmitting={isSubmitting}
        />
      </form>
    </Form>
  )
}

export default ResetPasswordForm

