import { Routes, Route } from "react-router-dom";
import { routes } from "./routes";
import ProtectedRoute from "@/components/core/protected-route";
import Layout from "@/components/core/layout";
import Home from "@/pages/Home";
import Profile from "@/pages/Profile";
import Auth from "@/pages/Auth";
import ErrorPage from "@/pages/ErrorPages";

const elementMap = {
  Home: <Home />,
  Profile: <Profile />,
  Auth: <Auth />,
};

export default function AppRouter() {
  return (
    <Routes>
      {routes.map(route => (
        <Route
          key={route.path}
          path={route.path}
          element={
            <ProtectedRoute permissions={route.permissions} requireAuth={route.requireAuth}>
              <Layout>
                {elementMap[route.element]}
              </Layout>
            </ProtectedRoute>
          }
        />
      ))}
      <Route path="*" element={<Layout><ErrorPage errorCode="404" /></Layout>} />
    </Routes>
  );
}