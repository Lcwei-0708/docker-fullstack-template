import * as React from "react";
import { Folder, Forward, MoreHorizontal, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { Icon } from "@/components/ui/icon";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"

export function NavProjects({
  projects,
  groupLabel
}) {
  const { isMobile, toggleSidebar } = useSidebar()
  
  const handleItemClick = React.useCallback(() => {
    if (isMobile) {
      toggleSidebar()
    }
  }, [isMobile, toggleSidebar])

  if (!projects || projects.length === 0) {
    return null;
  }

  return (
    <SidebarGroup className={cn("group-data-[collapsible=icon]:hidden")}>
      {groupLabel && <SidebarGroupLabel>{groupLabel}</SidebarGroupLabel>}
      <SidebarMenu>
        {projects.map((item) => (
          <SidebarMenuItem key={item.path || item.title || item.name}>
            <SidebarMenuButton asChild isActive={item.isActive}>
              <Link to={item.path || item.url} onClick={handleItemClick}>
                {item.iconName && (
                  <Icon name={item.iconName} isActive={item.isActive} />
                )}
                <span>{item.title || item.name}</span>
              </Link>
            </SidebarMenuButton>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuAction showOnHover>
                  <MoreHorizontal />
                  <span className={cn("sr-only")}>More</span>
                </SidebarMenuAction>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className={cn("w-48 rounded-sm")}
                side={isMobile ? "bottom" : "right"}
                align={isMobile ? "end" : "start"}>
                <DropdownMenuItem>
                  <Folder className={cn("text-muted-foreground")} />
                  <span>View Project</span>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Forward className={cn("text-muted-foreground")} />
                  <span>Share Project</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <Trash2 className={cn("text-muted-foreground")} />
                  <span>Delete Project</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        ))}
        <SidebarMenuItem>
          <SidebarMenuButton className={cn("text-sidebar-foreground/70")}>
            <MoreHorizontal className={cn("text-sidebar-foreground/70")} />
            <span>More</span>
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>
    </SidebarGroup>
  );
}