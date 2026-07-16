import React, { useState, useCallback, useEffect, useRef } from 'react'
import { useNavigate, Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { MailCheck, Home, Mail, LogIn } from 'lucide-react'
import { authService } from '@/services/auth.service'
import accountService from '@/services/account.service'
import { useAuth as useAuthContext } from '@/contexts/authContext'
import { useAuth } from '@/hooks/useAuth'
import { getCsrfTokenFromCookie } from '@/lib/cookies'
import { debugError } from '@/lib/utils'
import { Spinner } from '@/components/ui/spinner'

export const VerifyEmailForm = ({ className, token }) => {
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const authContextDirect = useAuthContext()
  
  // Calculate initial state based on token and email
  const initialState = React.useMemo(() => {
    const stateEmail = location.state?.email
    if (!token) {
      if (stateEmail) {
        return { isVerifying: false, verificationStatus: 'pending', email: stateEmail }
      } else {
        return { isVerifying: false, verificationStatus: 'error', email: '' }
      }
    }
    return { isVerifying: true, verificationStatus: null, email: stateEmail || '' }
  }, [token, location.state?.email])

  const [isVerifying, setIsVerifying] = useState(() => initialState.isVerifying)
  const [verificationStatus, setVerificationStatus] = useState(() => initialState.verificationStatus)
  const [errorMessage, setErrorMessage] = useState('')
  const [isResending, setIsResending] = useState(false)
  const [cooldownSeconds, setCooldownSeconds] = useState(0)
  const [email, setEmail] = useState(() => initialState.email)
  const intervalRef = useRef(null)
  const verificationInitiatedRef = useRef(false)
  const lastVerifiedTokenRef = useRef(null)
  const { isAuthenticated, isLoading: isAuthLoading, user } = useAuth()
  const { loginSuccess, setToken } = authContextDirect

  // Pending page only (no ?token=): if already logged in, go home.
  // Skip when user is waiting to confirm a profile email change (pending_email).
  useEffect(() => {
    if (token) return
    if (isAuthLoading || !isAuthenticated) return
    if (user?.pending_email) return
    navigate('/', { replace: true })
  }, [token, isAuthLoading, isAuthenticated, user?.pending_email, navigate])

  // Pending page: detect login completed in another tab (session cookie) via focus / polling
  useEffect(() => {
    if (token) return

    let cancelled = false
    const checkSession = async () => {
      if (cancelled || isAuthenticated) return
      try {
        const result = await authService.getToken({
          showErrorToast: false,
          csrfToken: getCsrfTokenFromCookie() ?? '',
        })
        const accessToken =
          typeof result === 'string'
            ? result
            : result?.access_token || result?.data?.access_token || null
        if (!cancelled && accessToken) {
          if (loginSuccess) {
            loginSuccess(null, accessToken)
          } else if (setToken) {
            setToken(accessToken)
          }
          navigate('/', { replace: true })
        }
      } catch (error) {
        // Still waiting for verification in another tab
      }
    }

    const onVisible = () => {
      if (document.visibilityState === 'visible') {
        checkSession()
      }
    }

    window.addEventListener('focus', checkSession)
    document.addEventListener('visibilitychange', onVisible)
    const intervalId = setInterval(checkSession, 4000)

    return () => {
      cancelled = true
      window.removeEventListener('focus', checkSession)
      document.removeEventListener('visibilitychange', onVisible)
      clearInterval(intervalId)
    }
  }, [token, isAuthenticated, loginSuccess, setToken, navigate])

  // Handle email verification when token is provided, or set pending state when only email is available
  useEffect(() => {
    if (!token) {
      setIsVerifying(false)
      const stateEmail = location.state?.email
      if (stateEmail) {
        setEmail(prev => prev !== stateEmail ? stateEmail : prev)
        setVerificationStatus(prev => prev !== 'pending' ? 'pending' : prev)
      } else {
        setVerificationStatus(prev => prev !== 'error' ? 'error' : prev)
        setErrorMessage(t('pages.auth.verifyEmail.messages.noToken', { defaultValue: 'No verification token provided' }))
      }
      verificationInitiatedRef.current = false
      lastVerifiedTokenRef.current = null
      return
    }

    if (verificationInitiatedRef.current && lastVerifiedTokenRef.current === token) {
      return
    }

    verificationInitiatedRef.current = true
    lastVerifiedTokenRef.current = token

    const verifyToken = async () => {
      setIsVerifying(true)
      setVerificationStatus(null)
      setErrorMessage('')
      try {
        const result = await authService.verifyEmail(token, { showErrorToast: false })
        if (result?.user && result?.access_token) {
          const { user, access_token } = result
          const loginSuccess = authContextDirect.loginSuccess
          const setUser = authContextDirect.setUser
          
          if (loginSuccess) {
            loginSuccess(user, access_token)
            await new Promise(resolve => setTimeout(resolve, 50))
            try {
              const profileResult = await accountService.getProfile({ showErrorToast: false, showSuccessToast: false })
              if (profileResult && setUser) {
                setUser(profileResult)
              }
            } catch (error) {
              debugError('Failed to fetch user profile:', error)
            }
          }
          setIsVerifying(false)
          navigate('/', { replace: true })
          return
        } else {
          setVerificationStatus('error')
          setErrorMessage(t('pages.auth.verifyEmail.messages.verificationFailed', { defaultValue: 'Email verification failed' }))
          verificationInitiatedRef.current = false
          lastVerifiedTokenRef.current = null
        }
      } catch (error) {
        debugError('Email verification error:', error)
        setVerificationStatus('error')
        const status = error.response?.status
        const errorMsg =
          status === 401
            ? t('pages.auth.verifyEmail.messages.invalidToken', {
                defaultValue: 'The verification link has expired or is invalid. Please request a new one.',
              })
            : status === 404
              ? t('pages.auth.verifyEmail.messages.userNotFound', {
                  defaultValue: 'User not found',
                })
              : status === 409
                ? t('pages.auth.verifyEmail.messages.emailExists', {
                    defaultValue: 'Email already exists',
                  })
                : t('pages.auth.verifyEmail.messages.verificationFailed', {
                    defaultValue: 'Email verification failed',
                  })
        setErrorMessage(errorMsg)
        verificationInitiatedRef.current = false
        lastVerifiedTokenRef.current = null
      } finally {
        setIsVerifying(false)
      }
    }

    verifyToken()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, t, location.state?.email, navigate])

  // Fetch email verification cooldown status
  const fetchCooldownRef = useRef(null)
  fetchCooldownRef.current = async (emailToCheck) => {
    if (!emailToCheck) return
    
    try {
      const result = await authService.getEmailVerificationCooldown(emailToCheck)
      if (result.status === 'success' && result.data?.data) {
        setCooldownSeconds(result.data.data.cooldown_seconds || 0)
      } else if (result.status === 'success' && result.data?.cooldown_seconds !== undefined) {
        setCooldownSeconds(result.data.cooldown_seconds || 0)
      }
    } catch (error) {
      debugError('Failed to fetch cooldown:', error)
    }
  }

  // Update email from location state and fetch cooldown when needed
  const cooldownFetchedRef = useRef(false)
  useEffect(() => {
    const stateEmail = location.state?.email
    if (stateEmail) {
      setEmail(prev => prev !== stateEmail ? stateEmail : prev)
      if ((verificationStatus === 'error' || verificationStatus === 'pending') && !cooldownFetchedRef.current) {
        cooldownFetchedRef.current = true
        fetchCooldownRef.current?.(stateEmail)
      }
    } else {
      cooldownFetchedRef.current = false
    }
  }, [location.state?.email, verificationStatus])

  // Update cooldown countdown timer
  useEffect(() => {
    if (cooldownSeconds > 0) {
      intervalRef.current = setInterval(() => {
        setCooldownSeconds((prev) => {
          if (prev <= 1) {
            if (intervalRef.current) {
              clearInterval(intervalRef.current)
              intervalRef.current = null
            }
            return 0
          }
          return prev - 1
        })
      }, 1000)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [cooldownSeconds])

  // Resend verification email
  const handleResend = useCallback(async () => {
    if (!email || cooldownSeconds > 0 || isResending) {
      return
    }

    setIsResending(true)
    try {
      await authService.resendVerification(email, { showErrorToast: true, showSuccessToast: true })
      await fetchCooldownRef.current?.(email)
    } catch (error) {
      debugError('Failed to resend verification email:', error)
      await fetchCooldownRef.current?.(email)
    } finally {
      setIsResending(false)
    }
  }, [email, cooldownSeconds, isResending])

  const navigateRef = useRef(navigate)
  useEffect(() => {
    navigateRef.current = navigate
  }, [navigate])

  if (isVerifying) {
    return (
      <div className={cn('space-y-6 flex items-center justify-center py-8', className)}>
        <div className="flex flex-col items-center gap-4">
          <Spinner className="size-8" />
        </div>
      </div>
    )
  }

  if (verificationStatus === 'success') {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="text-center">
          <p className="text-muted-foreground text-sm">
            {t('pages.auth.verifyEmail.messages.success', { defaultValue: 'Email verified successfully' })}
          </p>
        </div>
        <div className="flex justify-center pt-2">
          <Button asChild className="gap-2 text-sm">
            <Link to="/">
              <Home className="w-4 h-4" />
              {t('pages.auth.verifyEmail.actions.backToHome', { defaultValue: 'Go to Home' })}
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  if (verificationStatus === 'pending' && email) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="text-center">
          <p className="text-muted-foreground text-sm">
            {t('pages.auth.verifyEmail.messages.pending', { defaultValue: 'A verification email has been sent to your email address. Please check your inbox and click the verification link.' })}
          </p>
        </div>
        
        <div className="space-y-4">
          <Button
            onClick={handleResend}
            disabled={isResending || cooldownSeconds > 0}
            className="w-full gap-2"
          >
            {isResending ? (
              <>
                <Spinner className="size-4" />
              </>
            ) : cooldownSeconds > 0 ? (
              <>
                <Mail className="w-4 h-4" />
                {t('pages.auth.verifyEmail.actions.resendCooldown', { 
                  defaultValue: `Resend Email (${cooldownSeconds}s)`,
                  cooldownSeconds 
                })}
              </>
            ) : (
              <>
                <Mail className="w-4 h-4" />
                {t('pages.auth.verifyEmail.actions.resend', { defaultValue: 'Resend Verification Email' })}
              </>
            )}
          </Button>
        </div>
        
        <div className="flex justify-center pt-2">
          <Button asChild variant="outline" className="gap-2 text-sm">
            <Link to="/auth/login">
              <LogIn className="w-4 h-4" />
              {t('pages.auth.verifyEmail.actions.backToLogin', { defaultValue: 'Back to Login' })}
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  if (verificationStatus === 'error') {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="text-center">
          <p className="text-muted-foreground text-sm">
            {errorMessage || t('pages.auth.verifyEmail.messages.invalidToken', { defaultValue: 'The verification link has expired or is invalid. Please request a new one.' })}
          </p>
        </div>
        
        {email && (
          <div className="space-y-4">
            <Button
              onClick={handleResend}
              disabled={isResending || cooldownSeconds > 0}
              className="w-full gap-2"
            >
              {isResending ? (
                <>
                  <Spinner className="size-4" />
                </>
              ) : cooldownSeconds > 0 ? (
                <>
                  <Mail className="w-4 h-4" />
                  {t('pages.auth.verifyEmail.actions.resendCooldown', { 
                    defaultValue: `Resend Email (${cooldownSeconds}s)`,
                    cooldownSeconds 
                  })}
                </>
              ) : (
                <>
                  <Mail className="w-4 h-4" />
                  {t('pages.auth.verifyEmail.actions.resend', { defaultValue: 'Resend Verification Email' })}
                </>
              )}
            </Button>
          </div>
        )}
        
        <div className="flex justify-center pt-2">
          <Button asChild variant="outline" className="gap-2 text-sm">
            <Link to="/auth/login">
              <LogIn className="w-4 h-4" />
              {t('pages.auth.verifyEmail.actions.backToLogin', { defaultValue: 'Back to Login' })}
            </Link>
          </Button>
        </div>
      </div>
    )
  }

  return null
}

export default VerifyEmailForm