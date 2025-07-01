import nginxLogo from "@/assets/nginx.svg";
import reactLogo from "@/assets/react.svg";
import fastapiLogo from "@/assets/fastapi.svg";
import mariadbLogo from "@/assets/mariadb.svg";
import { cn } from "@/lib/utils";
import { useTranslation, Trans } from "react-i18next";
import { useTheme } from "@/contexts/themeContext";
import { Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import i18n from "@/i18n";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu";

function Home() {
  const { t, i18n: i18nInstance } = useTranslation();
  const { isDark, toggleTheme } = useTheme();

  const language = i18nInstance.language;

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    localStorage.setItem("app-language", lng);
  };

  const logoClass = cn(
    "w-16 h-16",
    "sm:w-20 sm:h-20",
    "md:w-24 md:h-24",
    "lg:w-28 lg:h-28",
    "transition-all duration-300",
    "user-select-none"
  );

  return (
    <>
      <div
        className={cn(
          "min-h-screen flex flex-col items-center justify-center p-4 relative",
          "bg-background text-foreground"
        )}
      >
        <div className="absolute top-4 right-4 flex items-center gap-2">
          <Button
            size="icon"
            variant="ghost"
            onClick={toggleTheme}
            className="rounded-full size-10"
          >
            {isDark ? (
              <Sun className="size-5" />
            ) : (
              <Moon className="size-5" />
            )}
          </Button>
        </div>

        <div className="absolute top-4 left-4">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="px-4">
                {language === "en" ? "English" : "繁體中文"}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="gap-1 flex flex-col">
              <DropdownMenuItem
                onClick={() => changeLanguage("en")}
                className={language === "en" ? "font-bold bg-accent" : ""}
              >
                English
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => changeLanguage("zh-TW")}
                className={language === "zh-TW" ? "font-bold bg-accent" : ""}
              >
                繁體中文
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <h1
          className={cn(
            "text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-7 text-center",
            "text-foreground"
          )}
        >
          {t("Home.title")}
        </h1>

        <p
          className={cn(
            "mb-16 text-center text-base md:text-lg lg:text-xl max-w-2xl",
            "text-muted-foreground"
          )}
        >
          <Trans
            i18nKey="Home.description"
            components={{
              bold: <span className={cn("text-foreground font-semibold")} />,
            }}
          />
        </p>

        <div
          className={cn(
            "grid gap-8 mb-12",
            "grid-cols-2", // Mobile: 2 items per row
            "sm:grid-cols-4", // Small tablet and above: 4 items per row
            "md:gap-12", // Larger gap on tablet
            "lg:gap-16" // Even larger gap on laptop/desktop
          )}
        >
          <img
            src={nginxLogo}
            alt="Nginx"
            title="Nginx"
            className={cn(
              logoClass,
              "hover:drop-shadow-[0_8px_32px_rgba(1,150,57,0.85)]"
            )}
          />
          <img
            src={reactLogo}
            alt="React"
            title="React"
            className={cn(
              logoClass,
              "hover:drop-shadow-[0_8px_32px_rgba(97,218,251,0.95)]"
            )}
          />
          <img
            src={fastapiLogo}
            alt="FastAPI"
            title="FastAPI"
            className={cn(
              logoClass,
              "hover:drop-shadow-[0_12px_32px_rgba(0,150,136,0.85)]"
            )}
          />
          <img
            src={mariadbLogo}
            alt="MariaDB"
            title="MariaDB"
            className={cn(
              logoClass,
              "hover:drop-shadow-[0_12px_32px_rgba(221,114,0,1)]"
            )}
          />
        </div>
      </div>
    </>
  );
}

export default Home;