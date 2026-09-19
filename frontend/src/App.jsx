import { Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./hooks/useAuth.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import ManagerRoleDetail from "./pages/ManagerRoleDetail.jsx";
import EmployeePortal from "./pages/EmployeePortal.jsx";
import HrPortal from "./pages/HrPortal.jsx";

function RequireAuth({ children, allowedRoles }) {
  const { isAuthenticated, user } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    if (user?.role === "employee") return <Navigate to="/employee" replace />;
    if (user?.role === "hr") return <Navigate to="/hr" replace />;
    return <Navigate to="/manager" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />

      {/* Manager Routes */}
      <Route
        path="/manager"
        element={
          <RequireAuth allowedRoles={["manager", "hr", "admin"]}>
            <Dashboard />
          </RequireAuth>
        }
      />
      <Route
        path="/manager/roles/:roleId"
        element={
          <RequireAuth allowedRoles={["manager", "hr", "admin"]}>
            <ManagerRoleDetail />
          </RequireAuth>
        }
      />
      <Route
        path="/dashboard"
        element={
          <RequireAuth>
            <Dashboard />
          </RequireAuth>
        }
      />

      {/* Employee Routes */}
      <Route
        path="/employee"
        element={
          <RequireAuth allowedRoles={["employee", "manager", "hr", "admin"]}>
            <EmployeePortal />
          </RequireAuth>
        }
      />
      <Route
        path="/employee/opportunities/:roleId"
        element={
          <RequireAuth allowedRoles={["employee", "manager", "hr", "admin"]}>
            <EmployeePortal />
          </RequireAuth>
        }
      />
      <Route
        path="/employee/learning"
        element={
          <RequireAuth allowedRoles={["employee", "manager", "hr", "admin"]}>
            <EmployeePortal />
          </RequireAuth>
        }
      />

      {/* HR Routes */}
      <Route
        path="/hr"
        element={
          <RequireAuth allowedRoles={["hr", "admin"]}>
            <HrPortal />
          </RequireAuth>
        }
      />
      <Route
        path="/hr/transfers"
        element={
          <RequireAuth allowedRoles={["hr", "admin"]}>
            <HrPortal />
          </RequireAuth>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
