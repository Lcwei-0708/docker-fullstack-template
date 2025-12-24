import * as React from "react"
import { ChevronsUpDown, Plus } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { useTranslation } from "react-i18next"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"

export function TeamSwitcher({
  teams = []
}) {
  const { isMobile, state, toggleSidebar } = useSidebar()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [activeTeam, setActiveTeam] = React.useState(teams?.[0])
  
  const shouldShowDropdown = teams && teams.length > 1
  const isCollapsed = state === "collapsed"

  const handleClick = () => {
    if (!shouldShowDropdown) {
      navigate("/")
      if (isMobile) {
        toggleSidebar()
      }
    }
  }

  if (!shouldShowDropdown) {
    const appName = t("components.app.name")
    const displayTeam = activeTeam || { logo: null, name: appName, plan: "" }
    const LogoComponent = displayTeam.logo
    
    return (
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton
            size="lg"
            onClick={handleClick}
            className={cn(
              "cursor-pointer h-14 p-2",
              "transition-[width,height,padding] duration-300 ease-in-out",
              "group-data-[collapsible=icon]:size-13!",
              "group-data-[collapsible=icon]:p-1!",
              "group-data-[collapsible=icon]:mx-0.5!",
              "group-data-[collapsible=icon]:rounded-lg!",
            )}>
            {LogoComponent ? (
              <LogoComponent 
                className={cn(
                  "transition-[width,height] duration-300 ease-in-out",
                  isCollapsed ? "size-11" : "size-10"
                )} 
              />
            ) : (
              <img 
                src="/logo.ico" 
                alt={appName} 
                className={cn(
                  "object-cover border",
                  "transition-[width,height] duration-300 ease-in-out",
                  isCollapsed ? "size-11 rounded-md" : "size-10 rounded-md"
                )} 
              />
            )}
            <div className={cn(
              "grid flex-1 text-left text-base leading-tight",
              "group-data-[collapsible=icon]:hidden"
            )}>
              <span className={cn("truncate font-bold")}>{displayTeam.name}</span>
              {displayTeam.plan && (
                <span className={cn("truncate text-sm")}>{displayTeam.plan}</span>
              )}
            </div>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    )
  }

  if (!activeTeam) {
    return null
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="lg"
              className={cn(
                "data-[state=open]:bg-sidebar-accent",
                "data-[state=open]:text-sidebar-accent-foreground"
              )}>
              <div
                className={cn(
                  "bg-sidebar-primary text-sidebar-primary-foreground",
                  "flex aspect-square size-8 items-center justify-center rounded-lg"
                )}>
                <activeTeam.logo className={cn("size-4")} />
              </div>
              <div className={cn("grid flex-1 text-left text-sm leading-tight")}>
                <span className={cn("truncate font-medium")}>{activeTeam.name}</span>
                <span className={cn("truncate text-xs")}>{activeTeam.plan}</span>
              </div>
              <ChevronsUpDown className={cn("ml-auto")} />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent
            className={cn(
              "w-(--radix-dropdown-menu-trigger-width)",
              "min-w-56 rounded-lg"
            )}
            align="start"
            side={isMobile ? "bottom" : "right"}
            sideOffset={4}>
            <DropdownMenuLabel className={cn("text-muted-foreground text-xs")}>
              Teams
            </DropdownMenuLabel>
            {teams.map((team, index) => (
              <DropdownMenuItem 
                key={team.name} 
                onClick={() => setActiveTeam(team)} 
                className={cn("gap-2 p-2")}>
                <div className={cn(
                  "flex size-6 items-center justify-center rounded-md border"
                )}>
                  <team.logo className={cn("size-3.5 shrink-0")} />
                </div>
                {team.name}
                <DropdownMenuShortcut>⌘{index + 1}</DropdownMenuShortcut>
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
            <DropdownMenuItem className={cn("gap-2 p-2")}>
              <div
                className={cn(
                  "flex size-6 items-center justify-center rounded-md border bg-transparent"
                )}>
                <Plus className={cn("size-4")} />
              </div>
              <div className={cn("text-muted-foreground font-medium")}>Add team</div>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
}