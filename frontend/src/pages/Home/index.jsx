import { cn } from "@/lib/utils";
import nginxLogo from "@/assets/nginx.svg";
import reactLogo from "@/assets/react.svg";
import fastapiLogo from "@/assets/fastapi.svg";
import mariadbLogo from "@/assets/mariadb.svg";
import { useTranslation, Trans } from "react-i18next";

function Home() {
  const { t } = useTranslation();

  const logoClass = cn(
    "w-16 h-16",
    "sm:w-20 sm:h-20",
    "md:w-24 md:h-24",
    "lg:w-28 lg:h-28",
    "transition-all duration-300"
  );

  return (
    <div
      className={cn(
        "min-h-screen flex flex-col items-center justify-center p-4",
        "bg-primary text-primary"
      )}
    >
      <h1
        className={cn(
          "text-2xl sm:text-3xl md:text-4xl lg:text-5xl font-bold mb-7 text-center",
          "text-accent"
        )}
      >
        {t("Home.title")}
      </h1>
      <p
        className={cn(
          "mb-16 text-center text-base md:text-lg lg:text-xl max-w-2xl",
          "text-secondary"
        )}
      >
        <Trans
          i18nKey="Home.description"
          components={{
            bold: <span className={cn("text-accent font-semibold")} />,
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
  );
}

export default Home;