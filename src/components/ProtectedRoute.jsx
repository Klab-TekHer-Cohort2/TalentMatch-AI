import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { PageLoader } from "./Loader";

export default function ProtectedRoute({ children, role }) {
  const { user, token, ready } = useAuth();
  const location = useLocation();

  if (!ready) return <PageLoader label="Checking your session…" />;
  if (!token || !user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (role && user.role !== role) {
    return <Navigate to={user.role === "employer" ? "/employer" : "/seeker"} replace />;
  }
  return children;
}
