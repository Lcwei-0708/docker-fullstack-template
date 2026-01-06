import { useTranslation } from "react-i18next";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Home, ArrowLeft, AlertCircle, FileQuestion, ShieldAlert, Server, Lock } from "lucide-react";

/**
 * Error - Universal error page component
 * @param {string} errorCode - Error code (404, 403, 500, 401, etc.)
 * @param {string} customTitle - Custom title (optional)
 * @param {string} customMessage - Custom message (optional)
 * @returns {JSX.Element}
 */
function Error({ errorCode: propErrorCode, customTitle: propCustomTitle, customMessage: propCustomMessage }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get error info from props or location.state
  const errorCode = propErrorCode || location.state?.errorCode || "404";
  const customTitle = propCustomTitle || location.state?.customTitle;
  const customMessage = propCustomMessage || location.state?.customMessage;

  // Get icon based on error code
  const getErrorIcon = (code) => {
    const iconMap = {
      "404": FileQuestion,
      "403": ShieldAlert,
      "500": Server,
      "401": Lock,
      default: AlertCircle,
    };

    return iconMap[code] || iconMap.default;
  };

  const Icon = getErrorIcon(errorCode);

  const title = customTitle || t(`errors.${errorCode}.title`, { defaultValue: t("errors.unknown.title") });
  const message = customMessage || t(`errors.${errorCode}.message`, { defaultValue: t("errors.unknown.message") });

  const handleGoHome = () => {
    navigate("/");
  };

  const handleGoBack = () => {
    navigate(-1);
  };

  return (
    <div
      className={cn(
        "h-full min-h-full flex items-center justify-center p-4",
        "bg-background w-full"
      )}
    >
      <div className="max-w-md w-full text-center space-y-6 flex-shrink-0">
        {/* Error Icon */}
        <div className="flex justify-center">
          <div
            className={cn(
              "p-4 sm:p-6 rounded-full bg-card/80 backdrop-blur-sm",
              "shadow-lg border border-border"
            )}
          >
            <Icon className={cn("w-12 h-12 sm:w-20 sm:h-20 text-primary")} />
          </div>
        </div>

        {/* Error Code */}
        <div className="space-y-2">
          <h1 className="text-4xl sm:text-6xl font-bold text-foreground">
            {errorCode}
          </h1>
          <h2 className="text-xl sm:text-2xl font-semibold text-foreground">
            {title}
          </h2>
          <p className="text-sm sm:text-base text-muted-foreground mt-4">
            {message}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-row gap-2 sm:gap-3 justify-center pt-4">
          <Button onClick={handleGoBack} variant="outline" className="gap-2 text-sm">
            <ArrowLeft className="w-4 h-4" />
            {t("common.back", { defaultValue: "Back" })}
          </Button>
          <Button onClick={handleGoHome} className="gap-2 text-sm">
            <Home className="w-4 h-4" />
            {t("common.home", { defaultValue: "Home" })}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default Error;