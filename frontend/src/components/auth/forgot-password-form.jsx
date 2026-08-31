import React, { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { cn, debugWarn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { MailCheck } from "lucide-react";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { authService } from "@/services/auth.service";
import { debugError } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";
import { useIsMobile } from "@/hooks/useMobile";

const SubmitButton = React.memo(({ onSubmit, t, className, isSubmitting }) => {
  return (
    <Button
      className={cn("w-full min-h-[40px]", className)}
      type="button"
      onClick={onSubmit}
      disabled={isSubmitting}
    >
      <span className="inline-flex items-center justify-center gap-2 min-w-[120px]">
        {isSubmitting ? (
          <Spinner className="size-4" />
        ) : (
          t("common.actions.submit", { defaultValue: "Submit" })
        )}
      </span>
    </Button>
  );
});

SubmitButton.displayName = "SubmitButton";

export const ForgotPasswordForm = ({ className, onStateChange, ...props }) => {
  const location = useLocation();
  const { t } = useTranslation();
  const isMobile = useIsMobile();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [cooldownSeconds, setCooldownSeconds] = useState(0);
  const [isLoadingCooldown, setIsLoadingCooldown] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [email, setEmail] = useState("");
  const intervalRef = useRef(null);

  const fetchCooldown = useCallback(async (emailToCheck) => {
    if (!emailToCheck) return;

    setIsLoadingCooldown(true);
    try {
      const result = await authService.getPasswordResetCooldown(emailToCheck);
      if (result.status === "success" && result.data?.data) {
        setCooldownSeconds(result.data.data.cooldown_seconds || 0);
      } else if (result.status === "success" && result.data?.cooldown_seconds !== undefined) {
        setCooldownSeconds(result.data.cooldown_seconds || 0);
      }
    } catch (error) {
      debugError("Failed to fetch cooldown:", error);
    } finally {
      setIsLoadingCooldown(false);
    }
  }, []);

  // Initialize email from location state (only when coming from other pages)
  useEffect(() => {
    const stateEmail = location.state?.email;

    if (stateEmail) {
      setEmail(stateEmail);
      setShowConfirmation(true);
      // Notify parent component about confirmation state
      if (onStateChange) {
        onStateChange(true);
      }
      // Fetch cooldown status
      fetchCooldown(stateEmail);
    }
  }, [fetchCooldown, location.state?.email, onStateChange]);

  // Countdown timer - only countdown, stop at 0
  useEffect(() => {
    if (cooldownSeconds > 0) {
      intervalRef.current = setInterval(() => {
        setCooldownSeconds((prev) => {
          if (prev <= 1) {
            if (intervalRef.current) {
              clearInterval(intervalRef.current);
              intervalRef.current = null;
            }
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [cooldownSeconds]);

  const formSchema = useMemo(() => {
    return z.object({
      email: z
        .string()
        .min(
          1,
          t("pages.auth.forgotPassword.fields.email.validation.required", {
            defaultValue: "Please enter your email",
          })
        )
        .refine(
          (val) => {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(val);
          },
          {
            message: t("pages.auth.forgotPassword.fields.email.validation.invalid", {
              defaultValue: "Please enter a valid email format",
            }),
          }
        ),
    });
  }, [t]);

  const stableDefaultValues = useMemo(
    () => ({
      email: email || "",
    }),
    [email]
  );

  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: stableDefaultValues,
  });

  // Update form when email changes
  useEffect(() => {
    if (email && form.getValues("email") !== email) {
      form.setValue("email", email, { shouldValidate: false });
    }
  }, [email, form]);

  useEffect(() => {
    try {
      form.clearErrors();
      const newResolver = zodResolver(formSchema);

      if (form._options && typeof form._options === "object" && "resolver" in form._options) {
        form._options.resolver = newResolver;
      }

      if ("_resolver" in form && form._resolver !== undefined) {
        form._resolver = newResolver;
      }

      if (form.formState.isSubmitted) {
        setTimeout(() => {
          form.trigger();
        }, 0);
      }
    } catch (error) {
      debugWarn("Failed to update form resolver:", error);
      form.clearErrors();
      if (form.formState.isSubmitted) {
        setTimeout(() => {
          form.trigger();
        }, 0);
      }
    }
  }, [formSchema, form]);

  const formMethodsRef = useRef(form);
  useEffect(() => {
    formMethodsRef.current = form;
  }, [form]);

  const handleSubmit = useCallback(
    async (formValues) => {
      setIsSubmitting(true);

      try {
        await authService.forgotPassword(formValues.email, {
          showErrorToast: true,
          showSuccessToast: true,
        });

        // Success - switch to confirmation mode
        const submittedEmail = formValues.email;
        setEmail(submittedEmail);
        setShowConfirmation(true);

        // Notify parent component about confirmation state
        if (onStateChange) {
          onStateChange(true);
        }

        // Fetch cooldown status
        await fetchCooldown(submittedEmail);

        setIsSubmitting(false);
      } catch (error) {
        debugError("Forgot password error:", error);
        // If error is due to cooldown, switch to confirmation mode and fetch cooldown
        if (error.response?.status === 400 && formValues.email) {
          const submittedEmail = formValues.email;
          setEmail(submittedEmail);
          setShowConfirmation(true);

          // Notify parent component about confirmation state
          if (onStateChange) {
            onStateChange(true);
          }

          await fetchCooldown(submittedEmail);
        }
        setIsSubmitting(false);
      }
    },
    [fetchCooldown, onStateChange]
  );

  const handleResend = useCallback(async () => {
    if (cooldownSeconds > 0 || isResending || !email) {
      return;
    }

    setIsResending(true);

    try {
      await authService.forgotPassword(email, {
        showErrorToast: true,
        showSuccessToast: true,
      });

      // Fetch new cooldown after successful send
      await fetchCooldown(email);
    } catch (error) {
      debugError("Resend email error:", error);
      // If error is due to cooldown, fetch the current cooldown status
      if (error.response?.status === 400) {
        await fetchCooldown(email);
      }
    } finally {
      setIsResending(false);
    }
  }, [email, cooldownSeconds, isResending, fetchCooldown]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  const onSubmitHandler = useCallback(
    (e) => {
      e?.preventDefault?.();
      formMethodsRef.current.handleSubmit(handleSubmit)();
    },
    [handleSubmit]
  );

  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === "Enter" && !isSubmitting && !showConfirmation) {
        e.preventDefault();
        onSubmitHandler(e);
      }
    },
    [onSubmitHandler, isSubmitting, showConfirmation]
  );

  const emailInputRef = useRef(null);
  useEffect(() => {
    if (!isMobile && emailInputRef.current && !showConfirmation) {
      emailInputRef.current.focus();
    }
  }, [isMobile, showConfirmation]);

  // Confirmation view
  if (showConfirmation && email) {
    return (
      <div className={cn("space-y-6", className)} {...props}>
        <div className="flex flex-col items-center gap-4 text-center">
          <div className="rounded-md bg-primary/10 p-4">
            <MailCheck className="size-12 text-primary" />
          </div>

          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              {t("pages.auth.forgotPasswordConfirmation.description", {
                defaultValue: "We've sent a password reset link to {{email}}",
                email,
              })}
            </p>
          </div>
        </div>
        <Button
          type="button"
          variant={cooldownSeconds > 0 ? "outline" : "default"}
          onClick={handleResend}
          disabled={cooldownSeconds > 0 || isResending || isLoadingCooldown}
          className="w-full mt-4 disabled:opacity-70"
        >
          {isResending ? (
            <span className="inline-flex items-center justify-center gap-2">
              <Spinner className="size-4" />
            </span>
          ) : cooldownSeconds > 0 ? (
            <span>
              {t("pages.auth.forgotPasswordConfirmation.actions.resendCooldown", {
                defaultValue: "Resend email ({{time}})",
                time: formatTime(cooldownSeconds),
              })}
            </span>
          ) : (
            <span>
              {t("pages.auth.forgotPasswordConfirmation.actions.resend", {
                defaultValue: "Resend email",
              })}
            </span>
          )}
        </Button>
      </div>
    );
  }

  // Input form view
  return (
    <Form {...form}>
      <form className={cn("space-y-6", className)} onKeyDown={handleKeyDown} {...props}>
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>
                {t("pages.auth.forgotPassword.fields.email.label", { defaultValue: "Email" })}
              </FormLabel>
              <FormControl>
                <Input
                  type="email"
                  placeholder=""
                  {...field}
                  ref={(e) => {
                    emailInputRef.current = e;
                    field.ref(e);
                  }}
                  disabled={isSubmitting}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <SubmitButton
          onSubmit={onSubmitHandler}
          t={t}
          className={cn("mt-4")}
          isSubmitting={isSubmitting}
        />

        <div className="text-center text-sm flex items-center justify-center gap-2">
          <Link
            to="/auth/login"
            className="font-medium text-primary hover:underline"
            state={location.state}
          >
            {t("pages.auth.forgotPassword.actions.backToLogin", { defaultValue: "Back to Login" })}
          </Link>
        </div>
      </form>
    </Form>
  );
};

export default ForgotPasswordForm;
