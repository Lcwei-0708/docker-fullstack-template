import { Routes, Route } from "react-router-dom";
import { routes } from "./routes";
import { debugWarn } from "@/lib/utils";
import ProtectedRoute from "@/components/core/protected-route";
import Layout from "@/components/core/layout";
import ErrorPage from "@/pages/ErrorPages";
import Home from "@/pages/Home";
import Profile from "@/pages/Profile";
import Auth from "@/pages/Auth";
import Users from "@/pages/Users";
import Roles from "@/pages/Roles";

const elementMap = {
  Home: <Home />,
  Profile: <Profile />,
  Auth: <Auth />,
  Users: <Users />,
  Roles: <Roles />,
};

function getRouteElement(elementName) {
  if (elementMap[elementName]) {
    return elementMap[elementName];
  }
  
  debugWarn(`Route element "${elementName}" not found. Please create the corresponding page component.`);
  return <ErrorPage errorCode="404" customTitle="Page not found" customMessage={`Page component "${elementName}" not found`} />;
}

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
                {getRouteElement(route.element)}
              </Layout>
            </ProtectedRoute>
          }
        />
      ))}
      <Route path="*" element={<Layout><ErrorPage errorCode="404" /></Layout>} />
    </Routes>
  );
}