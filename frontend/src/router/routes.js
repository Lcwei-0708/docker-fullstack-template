export const routes = [
  { path: "/", element: "Home", requireAuth: false, permissions: [] },
  { path: "/profile", element: "Profile", requireAuth: true, permissions: [] },
  { path: "/login", element: "Auth", requireAuth: false, permissions: [] },
  { path: "/register", element: "Auth", requireAuth: false, permissions: [] },
];