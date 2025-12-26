import React from "react";
import { useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { routes } from "@/router/routes";
import { useAuth } from "@/hooks/useAuth";
import { debugError } from "@/lib/utils";

export function transformRoutesToSidebar(filterByAuth = true, isAuthenticated = false, t = null, permissionMap = {}) {
  const visibleRoutes = routes.filter((route) => {
    if (!route.sidebar) return false;
    
    const showInSidebar = route.sidebar.showInSidebar !== undefined 
      ? route.sidebar.showInSidebar 
      : (route.requireAuth && filterByAuth ? isAuthenticated : !route.requireAuth);
    
    if (!showInSidebar) return false;
    
    // Check if user has required permissions
    if (route.permissions && route.permissions.length > 0) {
      if (!isAuthenticated) return false;
      const hasPermission = permissionMap[route.path];
      if (hasPermission !== true) return false;
    }
    
    return true;
  });

  const parentRoutes = visibleRoutes.filter((route) => !route.sidebar.parent);
  const childRoutes = visibleRoutes.filter((route) => route.sidebar.parent);

  // Group routes by sidebar group
  const routeMap = new Map();
  parentRoutes.forEach((route) => {
    const group = route.sidebar.group || "Platform";
    if (!routeMap.has(group)) {
      routeMap.set(group, []);
    }
    routeMap.get(group).push({
      ...route,
      items: [],
    });
  });

  // Attach child routes to their parent routes
  childRoutes.forEach((childRoute) => {
    if (childRoute.permissions && childRoute.permissions.length > 0) {
      if (!isAuthenticated) return;
      const hasPermission = permissionMap[childRoute.path];
      if (hasPermission !== true) return;
    }
    
    const parentPath = childRoute.sidebar.parent;
    for (const [group, routes] of routeMap.entries()) {
      const parentRoute = routes.find((r) => r.path === parentPath);
      if (parentRoute) {
        const label = childRoute.sidebar.label 
          ? (t ? t(childRoute.sidebar.label, { defaultValue: childRoute.path }) : childRoute.sidebar.label)
          : childRoute.path;
        parentRoute.items.push({
          title: label,
          label: childRoute.sidebar.label,
          url: childRoute.path,
          path: childRoute.path,
          iconName: childRoute.sidebar.iconName,
        });
        break;
      }
    }
  });

  const navMain = [];
  const projects = [];

  routeMap.forEach((groupRoutes, group) => {
    groupRoutes.sort((a, b) => {
      const orderA = a.sidebar?.order ?? 999;
      const orderB = b.sidebar?.order ?? 999;
      return orderA - orderB;
    });

    const formattedRoutes = groupRoutes.map((route) => {
      const label = route.sidebar.label 
        ? (t ? t(route.sidebar.label, { defaultValue: route.path }) : route.sidebar.label)
        : route.path;
      
      return {
        title: label,
        label: route.sidebar.label,
        url: route.path,
        path: route.path,
        iconName: route.sidebar.iconName,
        isActive: route.sidebar.isActive || false,
        items: route.items || [],
        group: group,
      };
    });

    if (group === "Projects") {
      projects.push(...formattedRoutes);
    } else {
      navMain.push(...formattedRoutes);
    }
  });

  return {
    navMain,
    projects,
    groups: Array.from(routeMap.keys()),
  };
}

export function useCurrentRouteSidebar() {
  const location = useLocation();
  const currentRoute = routes.find((route) => route.path === location.pathname);
  return currentRoute?.sidebar || null;
}

export function useSidebarRoutes(isAuthenticated = false) {
  const location = useLocation();
  const { t } = useTranslation();
  const { permissions, isLoadingPermissions, checkPermissions } = useAuth();

  // Build permission map: check if user has required permissions for each route
  const permissionMap = React.useMemo(() => {
    if (!isAuthenticated || isLoadingPermissions || !permissions || !checkPermissions) {
      return {};
    }

    if (typeof permissions !== 'object' || Object.keys(permissions).length === 0) {
      return {};
    }

    const routesWithPermissions = routes.filter(
      (route) => route.permissions && route.permissions.length > 0
    );

    const map = {};
    for (const route of routesWithPermissions) {
      try {
        const hasAll = checkPermissions(route.permissions);
        map[route.path] = hasAll;
      } catch (error) {
        debugError(`Failed to check permissions for route ${route.path}:`, error);
        map[route.path] = false;
      }
    }

    return map;
  }, [isAuthenticated, isLoadingPermissions, permissions, checkPermissions]);

  const { navMain, projects, groups } = transformRoutesToSidebar(true, isAuthenticated, t, permissionMap);

  // Set active state: parent is active if any child is active, or if current route has this parent
  const navMainWithActive = navMain.map((item) => {
    const subItemsWithActive = item.items
      .filter((subItem) => {
        const subRoute = routes.find((r) => r.path === subItem.path);
        if (subRoute?.permissions && subRoute.permissions.length > 0) {
          return permissionMap[subItem.path] === true;
        }
        return true;
      })
      .map((subItem) => ({
        ...subItem,
        title: subItem.label ? t(subItem.label, { defaultValue: subItem.path }) : subItem.title,
        isActive: location.pathname === subItem.path,
      }));
    
    const hasActiveSubItem = subItemsWithActive.some((subItem) => subItem.isActive);
    const isExactMatch = location.pathname === item.path;
    const currentRoute = routes.find((r) => r.path === location.pathname);
    const hasThisAsParent = currentRoute?.sidebar?.parent === item.path;
    
    const isItemActive = hasActiveSubItem || isExactMatch || hasThisAsParent;
    
    return {
      ...item,
      title: item.label ? t(item.label, { defaultValue: item.path }) : item.title,
      isActive: isItemActive,
      items: subItemsWithActive,
    };
  });

  const projectsWithActive = projects.map((item) => ({
    ...item,
    title: item.label ? t(item.label, { defaultValue: item.path }) : item.title,
    isActive: location.pathname === item.path,
  }));

  return {
    navMain: navMainWithActive,
    projects: projectsWithActive,
    groups,
    isCheckingPermissions: isLoadingPermissions,
  };
}