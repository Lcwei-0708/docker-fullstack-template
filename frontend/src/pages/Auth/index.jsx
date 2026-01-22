import React, { useRef } from 'react'
import { useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { AnimatePresence, motion } from 'motion/react'
import { cn } from '@/lib/utils'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { LoginForm } from '@/components/auth/login-form'
import { RegisterForm } from '@/components/auth/register-form'
import { ResetPasswordForm } from '@/components/auth/reset-password-form'
import { ForgotPasswordForm } from '@/components/auth/forgot-password-form'
import { VerifyEmailForm } from '@/components/auth/verify-email-form'

const arePropsEqual = (prevProps, nextProps) => {
  const prevPath = prevProps.location?.pathname
  const nextPath = nextProps.location?.pathname
  const prevSearch = prevProps.location?.search
  const nextSearch = nextProps.location?.search
  const prevState = prevProps.location?.state?.from?.pathname
  const nextState = nextProps.location?.state?.from?.pathname
  const prevStateEmail = prevProps.location?.state?.email
  const nextStateEmail = nextProps.location?.state?.email
  const prevLanguage = prevProps.language
  const nextLanguage = nextProps.language
  
  const areEqual = prevPath === nextPath && 
                   prevSearch === nextSearch && 
                   prevState === nextState &&
                   prevStateEmail === nextStateEmail &&
                   prevLanguage === nextLanguage
  
  return areEqual
}

// language prop is used in arePropsEqual to trigger re-render on language change
const AuthComponent = React.memo(({ t, location, language }) => {
  const redirect = React.useMemo(() => {
    const result = location.state?.from?.pathname || 
           new URLSearchParams(location.search).get('redirect') || 
           '/'
    return result
  }, [location.state?.from?.pathname, location.search])

  const resetToken = React.useMemo(() => {
    return new URLSearchParams(location.search).get('token')
  }, [location.search])

  const verifyToken = React.useMemo(() => {
    return new URLSearchParams(location.search).get('token')
  }, [location.search])

  const activeTab = React.useMemo(() => {
    if (location.pathname === '/auth/verify-email') {
      return 'verify-email'
    }
    if (location.pathname === '/auth/reset-password') {
      return 'reset-password'
    }
    if (location.pathname === '/auth/forgot-password') {
      return 'forgot-password'
    }
    if (location.pathname === '/auth/register') {
      return 'register'
    }
    return 'login'
  }, [location.pathname])

  // State to track if forgot password is in confirmation state
  const [isForgotPasswordConfirmation, setIsForgotPasswordConfirmation] = React.useState(() => {
    if (activeTab !== 'forgot-password') return false
    
    const stateEmail = location.state?.email
    return !!stateEmail
  })

  // Reset confirmation state when switching away from forgot-password tab
  React.useEffect(() => {
    if (activeTab !== 'forgot-password') {
      setIsForgotPasswordConfirmation(false)
    } else {
      const stateEmail = location.state?.email
      setIsForgotPasswordConfirmation(!!stateEmail)
    }
  }, [activeTab, location.state?.email])

  // Callback to update confirmation state from child component
  const handleForgotPasswordStateChange = React.useCallback((isConfirmation) => {
    if (activeTab === 'forgot-password') {
      setIsForgotPasswordConfirmation(isConfirmation)
    }
  }, [activeTab])


  return (
    <div className={cn("min-h-[100dvh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8")}>
      <div className="max-w-lg min-w-[360px] md:min-w-[400px] space-y-8">
        <motion.div
          layout
          transition={{
            type: "spring",
            stiffness: 300,
            damping: 30,
            mass: 0.8,
          }}
        >
          <motion.div
            layout
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 30,
              mass: 0.8,
            }}
          >
            <Card className="gap-4">
            <CardHeader>
              <AnimatePresence mode="wait">
                <CardTitle className="text-lg tracking-tight text-center mb-2">
                    {activeTab === 'verify-email'
                        ? t("pages.auth.verifyEmail.title", { defaultValue: "Verify Email" })
                        : activeTab === 'reset-password'
                        ? t("pages.auth.resetPassword.title", { defaultValue: "Reset Password" })
                        : activeTab === 'forgot-password'
                        ? t("pages.auth.forgotPassword.title", { defaultValue: "Forgot Password" })
                        : activeTab === 'register' 
                        ? t("pages.auth.register.title", { defaultValue: "Sign up" })
                        : t("pages.auth.login.title", { defaultValue: "Sign in" })
                    }
                </CardTitle>
              </AnimatePresence>
              <CardDescription>
                <AnimatePresence mode="wait">
                  {activeTab === 'forgot-password' && !isForgotPasswordConfirmation && (
                    <p className="text-sm text-muted-foreground mb-6">
                      {t("pages.auth.forgotPassword.description", { defaultValue: "Enter your email address and we'll send you a link to reset your password." })}
                    </p>
                  )}
                </AnimatePresence>
              </CardDescription>
            </CardHeader>
            <CardContent>
              {activeTab === 'verify-email' ? (
                <VerifyEmailForm token={verifyToken} />
              ) : activeTab === 'reset-password' ? (
                <ResetPasswordForm token={resetToken} />
              ) : activeTab === 'forgot-password' ? (
                <ForgotPasswordForm onStateChange={handleForgotPasswordStateChange} />
              ) : activeTab === 'register' ? (
                <RegisterForm redirectTo={redirect} />
              ) : (
                <LoginForm redirectTo={redirect} />
              )}
            </CardContent>
            <CardFooter className="hidden">
            </CardFooter>
          </Card>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}, arePropsEqual)

AuthComponent.displayName = 'AuthComponent'

const getLocationKey = (location) => {
  return `${location.pathname}${location.search}${location.state?.from?.pathname || ''}`
}

export function Auth() {
  const { t, i18n } = useTranslation()
  const location = useLocation()
  const locationKey = getLocationKey(location)
  const language = i18n.language
  
  const propsRef = useRef({ t, location, locationKey, language })
  
  if (propsRef.current.locationKey !== locationKey || propsRef.current.language !== language) {
    propsRef.current = { t, location, locationKey, language }
  } else {
    propsRef.current.t = t
    propsRef.current.location = location
    propsRef.current.language = language
  }
  
  return <AuthComponent t={propsRef.current.t} location={propsRef.current.location} language={propsRef.current.language} />
}

export default Auth