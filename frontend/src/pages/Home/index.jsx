import nginxLogo from "@/assets/nginx.svg";
import reactLogo from "@/assets/react.svg";
import fastapiLogo from "@/assets/fastapi.svg";
import mariadbLogo from "@/assets/mariadb.svg";
import { cn } from "@/lib/utils";
import { useTranslation, Trans } from "react-i18next";

function Home() {
  const { t } = useTranslation();

  const logoClass = cn(
    "w-20 h-20",
    "sm:w-24 sm:h-24",
    "md:w-26 md:h-26",
    "lg:w-28 lg:h-28",
    "transition-all duration-300",
    "user-select-none"
  );

  return (
    <>
      <div
        className={cn(
          "min-h-[100dvh] flex flex-col items-center justify-center p-4 relative",
          "bg-background text-foreground"
        )}
      >
        <h1
          className={cn(
            "text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-7 text-center",
            "text-foreground"
          )}
        >
          {t("home.title")}
        </h1>

        <p
          className={cn(
            "mb-16 text-center text-base md:text-lg lg:text-xl max-w-2xl",
            "text-muted-foreground"
          )}
        >
          <Trans
            i18nKey="home.description"
            components={{
              bold: <span className={cn("text-foreground font-semibold")} />,
            }}
          />
        </p>

        <div
          className={cn(
            "grid gap-8 mb-12",
            "grid-cols-2",
            "sm:grid-cols-4",
            "md:gap-12",
            "lg:gap-16"
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