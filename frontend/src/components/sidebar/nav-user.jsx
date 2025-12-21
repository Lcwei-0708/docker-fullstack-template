import * as React from "react"
import { Link } from "react-router-dom"
import { useTranslation } from "react-i18next"
import { useTheme } from "@/contexts/themeContext"
import { useAuth } from "@/hooks/useAuth"
import { useIsMobile } from "@/hooks/useMobile"
import { cn } from "@/lib/utils"
import {
  LogOut,
  Languages,
  Moon,
  Sun,
  Check,
  CircleUser,
  EllipsisVertical,
} from "lucide-react"
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog"

export function NavUser() {
  const { user, logout } = useAuth()
  const { t, i18n: i18nInstance } = useTranslation()
  const { theme, setTheme, themes } = useTheme()
  const isMobile = useIsMobile()
  const { state, toggleSidebar } = useSidebar()

  const [alertOpen, setAlertOpen] = React.useState(false)

  const themeOptions = [
    { value: themes.LIGHT, label: t("components.sidebar.setting.themeOptions.light"), icon: Sun },
    { value: themes.DARK, label: t("components.sidebar.setting.themeOptions.dark"), icon: Moon },
  ]

  const languageOptions = [
    { value: "zh-TW", label: "繁體中文" },
    { value: "en", label: "English" },
  ]

  const currentTheme = themeOptions.find(opt => opt.value === theme)?.label
  const currentLanguage = languageOptions.find(opt => opt.value === i18nInstance.language)?.label

  const username = React.useMemo(() => {
    if (!user) return '';
    return `${user.first_name || ''} ${user.last_name || ''}`.trim();
  }, [user]);

  const email = React.useMemo(() => {
    return user?.email || '';
  }, [user]);

  const displayName = username || t("components.sidebar.setting.guest")
  const displayEmail = email

  const userInitials = React.useMemo(() => {
    if (!user) return 'G';
    const first = user.first_name?.[0]?.toUpperCase() || '';
    const last = user.last_name?.[0]?.toUpperCase() || '';
    return (first + last) || user.email?.[0]?.toUpperCase() || 'G';
  }, [user]);

  const handleItemClick = () => {
    if (isMobile) {
      toggleSidebar()
    }
  }

  const handleLanguageChange = (languageValue) => {
    i18nInstance.changeLanguage(languageValue);
    localStorage.setItem("app-language", languageValue);
  }

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <SidebarMenuButton
                data-state={state}
                size="lg"
                className={cn(
                  "data-[state=open]:bg-sidebar-accent",
                  "data-[state=open]:text-sidebar-accent-foreground",
                  "group-data-[collapsible=icon]:size-13!",
                  "group-data-[collapsible=icon]:p-1!",
                  "group-data-[collapsible=icon]:mx-0.5!",
                  "group-data-[collapsible=icon]:rounded-lg!",
                  "flex items-center gap-2 p-2 h-13 rounded-md transition-[padding,margin,width] duration-300 ease-in-out will-change-transform",
                )}>
                <Avatar 
                  className={cn(
                    "h-9 w-9 rounded-md bg-transparent text-inherit transition-[padding,margin,width,height] duration-300 ease-in-out",
                    "group-data-[collapsible=icon]:h-11",
                    "group-data-[collapsible=icon]:w-11",
                    "group-data-[collapsible=icon]:rounded-md"
                  )}>
                  <AvatarImage src={user?.avatar} alt={displayName} />
                  <AvatarFallback className={cn("rounded-sm bg-primary text-primary-foreground")}>
                    {userInitials}
                  </AvatarFallback>
                </Avatar>
                <div className={cn(
                  "grid flex-1 text-left text-sm leading-tight transition-transform duration-300 ease-in-out",
                  "group-data-[collapsible=icon]:hidden"
                )}>
                  <span className={cn("truncate font-semibold")}>{displayName}</span>
                  <span className={cn("truncate text-xs")}>{displayEmail}</span>
                </div>
                <EllipsisVertical 
                  className={cn(
                    "ml-auto !size-5 transition-transform duration-300 ease-in-out",
                    "group-data-[collapsible=icon]:hidden"
                  )} 
                />
              </SidebarMenuButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className={cn(
                "min-w-[240px]"
              )}
              side={isMobile ? "top" : "right"}
              align={isMobile ? "center" : "end"}
              sideOffset={isMobile ? 8 : 4}>
              <DropdownMenuGroup className="gap-1 flex flex-col">
                <Link to="/profile" onClick={handleItemClick}>
                  <DropdownMenuItem className="cursor-pointer py-2">
                    <CircleUser className="mr-2 h-4 w-4" />
                    <span>{t("components.sidebar.title.profile")}</span>
                  </DropdownMenuItem>
                </Link>
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger className="[&>svg]:ml-0 cursor-pointer py-2">
                    <div className="flex items-center flex-1 gap-2">
                      {theme === themes.DARK ? <Moon className="mr-2 h-4 w-4" /> : <Sun className="mr-2 h-4 w-4" />}
                      <span>{t("components.sidebar.setting.theme")}</span>
                    </div>
                    <span className="text-xs text-muted-foreground ml-2">{currentTheme}</span>
                  </DropdownMenuSubTrigger>
                  <DropdownMenuSubContent 
                    className="gap-1 flex flex-col"
                    side={isMobile ? "bottom" : "right"}
                    align={isMobile ? "start" : "end"}
                    sideOffset={isMobile ? -140 : 4}
                    alignOffset={isMobile ? -200 : 0}>
                    {themeOptions.map((option) => (
                      <DropdownMenuItem
                        key={option.value}
                        onClick={() => setTheme(option.value)}
                        className={cn(
                          theme === option.value ? "bg-accent" : "",
                          "cursor-pointer flex items-center gap-6 py-2"
                        )}>
                        <div className="flex items-center gap-2">
                          <option.icon className="h-4 w-4" />
                          <span className="flex-2 flex">{option.label}</span>
                        </div>
                        <Check 
                          className={cn(
                            "ml-auto h-4 w-[2rem] flex justify-end",
                            theme === option.value ? "opacity-100" : "opacity-0"
                          )}
                        />
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuSub>
                <DropdownMenuSub>
                  <DropdownMenuSubTrigger className="[&>svg]:ml-0 cursor-pointer py-2">
                    <div className="flex items-center flex-1 gap-2">
                      <Languages className="mr-2 h-4 w-4" />
                      <span>{t("components.sidebar.setting.language")}</span>
                    </div>
                    <span className="text-xs text-muted-foreground ml-2">{currentLanguage}</span>
                  </DropdownMenuSubTrigger>
                  <DropdownMenuSubContent 
                    className="gap-1 flex flex-col"
                    side={isMobile ? "left" : "right"}
                    align={isMobile ? "center" : "end"}
                    sideOffset={isMobile ? -123 : 4}
                    alignOffset={isMobile ? -200 : 0}>
                    {languageOptions.map((option) => (
                      <DropdownMenuItem
                        key={option.value}
                        onClick={() => handleLanguageChange(option.value)}
                        className={cn(
                          i18nInstance.language === option.value ? "bg-accent" : "",
                          "cursor-pointer flex items-center gap-6 py-2"
                        )}>
                        <span>{option.label}</span>
                        {i18nInstance.language === option.value && (
                          <Check className="ml-auto h-4 w-4" />
                        )}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuSubContent>
                </DropdownMenuSub>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer py-2 text-destructive hover:!text-destructive hover:!bg-destructive/10" onClick={() => setAlertOpen(true)}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>{t("components.sidebar.setting.logout")}</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>

      <AlertDialog open={alertOpen} onOpenChange={setAlertOpen}>
        <AlertDialogContent className="w-[90%] rounded-lg">
          <AlertDialogHeader className={cn(
            "flex flex-col",
            isMobile ? "gap-2" : "gap-0"
          )}>
            <AlertDialogTitle>{t("components.sidebar.setting.logoutConfirm")}</AlertDialogTitle>
            <AlertDialogDescription>
              {t("components.sidebar.setting.logoutConfirmDescription")}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="flex-row gap-5 sm:gap-0 mt-2">
            <AlertDialogCancel className={cn(
              isMobile ? "w-full" : "",
              "text-sm mt-0"
            )}>{t("common.actions.cancel")}</AlertDialogCancel>
            <AlertDialogAction
              className={cn(
                isMobile ? "w-full" : "",
                "text-sm mt-0"
              )}
              onClick={() => {
                setAlertOpen(false)
                logout()
              }}>
              {t("common.actions.confirm")}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}