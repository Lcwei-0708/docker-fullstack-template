import { Routes, Route } from "react-router-dom";
import { routes } from "./routes";
import Home from "@/pages/Home";

const elementMap = {
  Home: <Home />,
};

export default function AppRouter() {
  return (
    <Routes>
      {routes.map(route => (
        <Route key={route.path} path={route.path} element={elementMap[route.element]} />
      ))}
    </Routes>
  );
}