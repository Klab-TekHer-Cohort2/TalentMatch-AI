import { Link, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import Courses from "./pages/Courses";
import EmployerDashboard from "./pages/EmployerDashboard";
import ForgotPassword from "./pages/ForgotPassword";
import Home from "./pages/Home";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import Register from "./pages/Register";
import ResetPassword from "./pages/ResetPassword";
import SeekerDashboard from "./pages/SeekerDashboard";
import VerifyEmail from "./pages/VerifyEmail";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/courses" element={<Courses />} />
      <Route
        path="/seeker"
        element={
          <ProtectedRoute role="job_seeker">
            <SeekerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/employer"
        element={
          <ProtectedRoute role="employer">
            <EmployerDashboard />
          </ProtectedRoute>
        }
      />
      <Route path="/dashboard" element={<DashboardRedirect />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

function DashboardRedirect() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-2xl font-semibold">Choose your workspace</h1>
      <p className="muted">Sign in to continue to the correct dashboard.</p>
      <Link to="/login" className="btn-primary">
        Go to login
      </Link>
    </div>
  );
}
