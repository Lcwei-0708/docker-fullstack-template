import * as React from "react";
import { ChevronRight } from "lucide-react";
import { Link } from "react-router-dom";
import { Icon } from "@/components/ui/icon";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  useSidebar,
} from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"

function CollapsedMenuItemWithDropdown({ item }) {
  const [dropdownOpen, setDropdownOpen] = React.useState(false);
  const [showTooltip, setShowTooltip] = React.useState(true);
  
  React.useEffect(() => {
    if (dropdownOpen) {
      setShowTooltip(false);
    } else {
      const timer = setTimeout(() => {
        setShowTooltip(true);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [dropdownOpen]);
  
  return (
    <DropdownMenu 
      open={dropdownOpen}
      onOpenChange={setDropdownOpen}>
      <SidebarMenuItem>
        <DropdownMenuTrigger asChild>
          <SidebarMenuButton 
            size="lg"
            tooltip={showTooltip && !dropdownOpen ? item.title : undefined}
            isActive={item.isActive}
            className={cn(
              "group-data-[collapsible=icon]:size-12!",
              "group-data-[collapsible=icon]:p-2!",
              "group-data-[collapsible=icon]:mx-1!",
              "group-data-[collapsible=icon]:rounded-lg!",
              item.isActive && "hover:!bg-primary/15 hover:!text-primary",
            )}>
            {item.iconName && (
              <Icon 
                name={item.iconName}
                isActive={item.isActive}
                className={cn(
                  "text-sidebar-foreground [&>svg]:!size-7 transition-[width,height] duration-300 ease-in-out",
                  "group-data-[collapsible=icon]:mx-0.5 group-data-[collapsible=icon]:!size-7",
                )}
              />
            )}
            <span>{item.title}</span>
          </SidebarMenuButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent side="right" align="start" sideOffset={7} className="w-48 gap-1 flex flex-col">
          <DropdownMenuLabel className="text-sm font-medium text-center">{item.title}</DropdownMenuLabel>
          <DropdownMenuSeparator className="my-0"/>
          {item.items.map((subItem) => (
            <DropdownMenuItem key={subItem.path || subItem.title} asChild>
              <Link 
                to={subItem.path || subItem.url}
                onClick={handleItemClick}
                className={cn(
                  "flex items-center",
                  subItem.isActive && "bg-primary/15 text-primary font-semibold hover:!bg-primary/15 hover:!text-primary"
                )}>
                {subItem.iconName && (
                  <Icon 
                    name={subItem.iconName}
                    isActive={subItem.isActive}
                    className={cn(
                      "text-sidebar-foreground transition-[width,height] duration-300 ease-in-out [&>svg]:!size-6",
                    )}
                  />
                )}
                <span>{subItem.title}</span>
              </Link>
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </SidebarMenuItem>
    </DropdownMenu>
  );
}

export function NavMain({
  items,
  groupLabel
}) {
  const { state, isMobile, toggleSidebar } = useSidebar()
  const isCollapsed = state === "collapsed"
  const shouldUseDropdown = isCollapsed && !isMobile
  
  const handleItemClick = React.useCallback(() => {
    if (isMobile) {
      toggleSidebar()
    }
  }, [isMobile, toggleSidebar])
  
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <SidebarGroup>
      {groupLabel && <SidebarGroupLabel>{groupLabel}</SidebarGroupLabel>}
      <SidebarMenu>
        {items.map((item) => {
          const hasItems = item.items && item.items.length > 0;
          
          if (hasItems) {
            if (shouldUseDropdown) {
              return (
                <CollapsedMenuItemWithDropdown key={item.path || item.title} item={item} />
              );
            }
            
            return (
              <Collapsible
                key={item.path || item.title}
                asChild
                defaultOpen={item.isActive}
                className={cn("group/collapsible")}>
                <SidebarMenuItem>
                  <CollapsibleTrigger asChild>
                    <SidebarMenuButton 
                      size="lg"
                      tooltip={item.title}
                      isActive={item.isActive}
                      className={cn(
                        "group-data-[collapsible=icon]:size-12!",
                        "group-data-[collapsible=icon]:p-2!",
                        "group-data-[collapsible=icon]:mx-1!",
                        "group-data-[collapsible=icon]:rounded-lg!",
                        item.isActive && "hover:!bg-primary/15 hover:!text-primary",
                      )}>
                      {item.iconName && (
                        <Icon 
                          name={item.iconName}
                          isActive={item.isActive}
                          className={cn(
                            "text-sidebar-foreground [&>svg]:!size-7 transition-[width,height] duration-300 ease-in-out",
                            "group-data-[collapsible=icon]:mx-0.5 group-data-[collapsible=icon]:!size-7",
                          )}
                        />
                      )}
                      <span>{item.title}</span>
                      <ChevronRight
                        className={cn(
                          "ml-auto transition-transform duration-300 ease-in-out",
                          "group-data-[state=open]/collapsible:rotate-90"
                        )} />
                    </SidebarMenuButton>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="mt-1">
                    <SidebarMenuSub>
                      {item.items.map((subItem) => (
                        <SidebarMenuSubItem key={subItem.path || subItem.title}>
                          <SidebarMenuSubButton 
                            asChild 
                            isActive={subItem.isActive}
                            className={cn(
                              subItem.isActive && "hover:bg-primary/15 hover:text-primary",
                            )}>
                            <Link to={subItem.path || subItem.url} onClick={handleItemClick}>
                              {subItem.iconName && (
                                <Icon 
                                  name={subItem.iconName}
                                  isActive={subItem.isActive}
                                  className={cn(
                                    "text-sidebar-foreground [&>svg]:!size-7 transition-[width,height] duration-300 ease-in-out",
                                    "group-data-[collapsible=icon]:mx-0.5 group-data-[collapsible=icon]:!size-7",
                                  )}
                                />
                              )}
                              <span>{subItem.title}</span>
                            </Link>
                          </SidebarMenuSubButton>
                        </SidebarMenuSubItem>
                      ))}
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </SidebarMenuItem>
              </Collapsible>
            );
          } else {
            return (
              <SidebarMenuItem key={item.path || item.title}>
                <SidebarMenuButton 
                  size="lg"
                  asChild
                  tooltip={item.title}
                  isActive={item.isActive}
                  className={cn(
                    "group-data-[collapsible=icon]:size-12!",
                    "group-data-[collapsible=icon]:p-2!",
                    "group-data-[collapsible=icon]:mx-1!",
                    "group-data-[collapsible=icon]:rounded-lg!",
                    item.isActive && "hover:bg-primary/15 hover:text-primary",
                  )}>
                  <Link to={item.path || item.url} onClick={handleItemClick}>
                    {item.iconName && (
                      <Icon 
                        name={item.iconName}
                        isActive={item.isActive}
                        className={cn(
                          "text-sidebar-foreground [&>svg]:!size-7 transition-[width,height] duration-300 ease-in-out",
                          "group-data-[collapsible=icon]:mx-0.5 group-data-[collapsible=icon]:!size-7",
                        )}
                      />
                    )}
                    <span>{item.title}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            );
          }
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
}