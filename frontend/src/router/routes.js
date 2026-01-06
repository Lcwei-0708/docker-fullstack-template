/**
 * Route Configuration
 * @typedef {Object} RouteConfig
 * @property {string} path - Route path
 * @property {string} element - Component name
 * @property {boolean} requireAuth - Whether authentication is required
 * @property {string[]} permissions - Required permissions list
 * @property {Object} [sidebar] - Sidebar configuration
 * @property {string} [sidebar.group] - Sidebar group name (e.g., "Platform", "Projects"). Will be converted to lowercase and used as i18n key: "components.sidebar.groups.{group.toLowerCase()}"
 * @property {string} [sidebar.iconName] - Icon name for assets/icons/ (e.g., "home", "profile"). Files should be named: {iconName}-active.svg and {iconName}-inactive.svg
 * @property {string} [sidebar.label] - i18n translation key for sidebar label (e.g., "components.sidebar.routes.home")
 * @property {boolean} [sidebar.showInSidebar] - Whether to show in sidebar (default: true if requireAuth is true)
 * @property {string} [sidebar.parent] - Parent route path (for nested structure). Set this to create a subitem under a parent item
 * @property {number} [sidebar.order] - Sort order (lower number appears first)
 * @property {boolean} [sidebar.isActive] - Whether to expand by default (only for parent items with subitems)
 * 
 * @example
 * // Parent item with subitems:
 * {
 *   path: "/example",
 *   element: "Example",
 *   requireAuth: true,
 *   sidebar: {
 *     group: "Example",
 *     iconName: "example",
 *     label: "components.sidebar.routes.example",
 *     showInSidebar: true,
 *     order: 1,
 *     isActive: true
 *   }
 * },
 * // Subitem (child route):
 * {
 *   path: "/example/users",
 *   element: "Users",
 *   requireAuth: true,
 *   sidebar: {
 *     parent: "/example",
 *     iconName: "users",
 *     label: "components.sidebar.routes.users",
 *     showInSidebar: true,
 *   }
 * }
 */

export const routes = [
  {
    path: "/",
    element: "Home",
    requireAuth: false,
    permissions: [],
    sidebar: {
      showInSidebar: false,
    },
  },
  {
    path: "/login",
    element: "Auth",
    requireAuth: false,
    permissions: [],
    sidebar: {
      showInSidebar: false,
    },
  },
  {
    path: "/register",
    element: "Auth",
    requireAuth: false,
    permissions: [],
    sidebar: {
      showInSidebar: false,
    },
  },
  {
    path: "/reset-password",
    element: "Auth",
    requireAuth: false,
    permissions: [],
    sidebar: {
      showInSidebar: false,
    },
  },
  {
    path: "/profile",
    element: "Profile",
    requireAuth: true,
    permissions: [],
    sidebar: {
      showInSidebar: false,
    },
  },
  {
    path: "/users",
    element: "Users",
    requireAuth: true,
    permissions: ["view-users", "manage-users"],
    sidebar: {
      group: "systemManagement",
      iconName: "users",
      label: "components.sidebar.routes.users",
      showInSidebar: true,
      order: 1,
    },
  },
  {
    path: "/roles",
    element: "Roles",
    requireAuth: true,
    permissions: ["view-roles", "manage-roles"],
    sidebar: {
      group: "systemManagement",
      iconName: "roles",
      label: "components.sidebar.routes.roles",
      showInSidebar: true,
      order: 2,
    },
  }
];