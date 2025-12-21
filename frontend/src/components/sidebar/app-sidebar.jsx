import * as React from "react"
import { useTranslation } from "react-i18next"
import { useAuth } from "@/hooks/useAuth"
import { useSidebarRoutes } from "@/lib/sidebar-routes"
import { NavMain } from "./nav-main"
import { NavProjects } from "./nav-projects"
import { NavUser } from "./nav-user"
import { TeamSwitcher } from "./team-switcher"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarSeparator,
} from "@/components/ui/sidebar"

export function AppSidebar({
  user,
  onLogout,
  ...props
}) {
  const { isAuthenticated } = useAuth()
  const { t } = useTranslation()
  const { navMain, projects, groups } = useSidebarRoutes(isAuthenticated)

  // Group navMain items by their group
  const groupedNavMain = React.useMemo(() => {
    const grouped = {}
    navMain.forEach((item) => {
      const group = item.group || "Other"
      if (!grouped[group]) {
        grouped[group] = []
      }
      grouped[group].push(item)
    })
    return grouped
  }, [navMain])

  // Group projects items by their group
  const groupedProjects = React.useMemo(() => {
    const grouped = {}
    projects.forEach((item) => {
      const group = item.group || "Projects"
      if (!grouped[group]) {
        grouped[group] = []
      }
      grouped[group].push(item)
    })
    return grouped
  }, [projects])

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={[]} />
      </SidebarHeader>
      <SidebarSeparator className="group-data-[collapsible=icon]:-mt-[1px] group-data-[collapsible=icon]:!h-[1.5px]" />
      <SidebarContent className="group-data-[collapsible=icon]:pt-0">
        {groups
          .map((group) => {
            if (group === "Projects") {
              const groupProjects = groupedProjects[group] || []
              if (groupProjects.length === 0) return null
              return (
                <NavProjects 
                  key={group}
                  projects={groupProjects}
                  groupLabel={t(`components.sidebar.groups.${group}`, { defaultValue: group })}
                />
              )
            } else {
              const groupNavMain = groupedNavMain[group] || []
              if (groupNavMain.length === 0) return null
              return (
                <NavMain 
                  key={group}
                  items={groupNavMain}
                  groupLabel={t(`components.sidebar.groups.${group}`, { defaultValue: group })}
                />
              )
            }
          })
          .filter(Boolean)
          .map((component, index, array) => {
            const isLastGroup = index === array.length - 1
            return (
              <React.Fragment key={component.key || index}>
                {component}
                {!isLastGroup && (
                  <SidebarSeparator className="group-data-[collapsible=icon]:-my-2 !w-[60%] group-data-[collapsible=icon]:!h-[1px]" />
                )}
              </React.Fragment>
            )
          })}
      </SidebarContent>
      <SidebarSeparator className="group-data-[collapsible=icon]:!h-[1.5px] !w-[75%]" />
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  );
}
