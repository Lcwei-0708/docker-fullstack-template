import React, { useRef } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
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

const arePropsEqual = (prevProps, nextProps) => {
  const prevPath = prevProps.location?.pathname
  const nextPath = nextProps.location?.pathname
  const prevSearch = prevProps.location?.search
  const nextSearch = nextProps.location?.search
  const prevState = prevProps.location?.state?.from?.pathname
  const nextState = nextProps.location?.state?.from?.pathname
  const prevLanguage = prevProps.language
  const nextLanguage = nextProps.language
  
  const areEqual = prevPath === nextPath && 
                   prevSearch === nextSearch && 
                   prevState === nextState &&
                   prevLanguage === nextLanguage
  
  return areEqual
}

const AuthComponent = React.memo(({ t, location, language, navigate }) => {
  const redirect = React.useMemo(() => {
    const result = location.state?.from?.pathname || 
           new URLSearchParams(location.search).get('redirect') || 
           '/'
    return result
  }, [location.state?.from?.pathname, location.search])

  const resetToken = React.useMemo(() => {
    return new URLSearchParams(location.search).get('token')
  }, [location.search])

  const activeTab = React.useMemo(() => {
    if (location.pathname === '/reset-password') {
      return 'reset-password'
    }
    if (location.pathname === '/register') {
      return 'register'
    }
    return 'login'
  }, [location.pathname])


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
                    {activeTab === 'reset-password'
                        ? t("pages.auth.resetPassword.title", { defaultValue: "Reset Password" })
                        : activeTab === 'register' 
                        ? t("pages.auth.register.title", { defaultValue: "Sign up" })
                        : t("pages.auth.login.title", { defaultValue: "Sign in" })
                    }
                </CardTitle>
              </AnimatePresence>
              <CardDescription>
              </CardDescription>
            </CardHeader>
            <CardContent>
              {activeTab === 'reset-password' ? (
                <ResetPasswordForm token={resetToken} />
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
  const navigate = useNavigate()
  const locationKey = getLocationKey(location)
  const language = i18n.language
  
  const propsRef = useRef({ t, location, locationKey, language, navigate })
  
  if (propsRef.current.locationKey !== locationKey || propsRef.current.language !== language) {
    propsRef.current = { t, location, locationKey, language, navigate }
  } else {
    propsRef.current.t = t
    propsRef.current.location = location
    propsRef.current.language = language
    propsRef.current.navigate = navigate
  }
  
  return <AuthComponent t={propsRef.current.t} location={propsRef.current.location} language={propsRef.current.language} navigate={propsRef.current.navigate} />
}

export default Auth