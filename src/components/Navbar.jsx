import { BriefcaseBusiness, LayoutDashboard, LogOut, Menu, Sparkles, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { initials } from "../lib/utils";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setOpen(false);
  }, [location.pathname]);

  const dashboardPath = user?.role === "employer" ? "/employer" : "/seeker";

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <header className="sticky top-0 z-40 border-b border-neutral-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-neutral-900 to-neutral-700 text-white shadow-sm">
            <Sparkles size={18} />
          </span>
          <span className="text-lg font-bold tracking-tight text-neutral-900">
            TalentMatch <span className="text-neutral-900">AI</span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          <Link to="/" className="btn-ghost">
            Home
          </Link>
          {user ? (
            <>
              <Link to={dashboardPath} className="btn-ghost">
                <LayoutDashboard size={16} /> Dashboard
              </Link>
              <div className="mx-2 hidden items-center gap-2 rounded-full border border-neutral-200 bg-neutral-50 py-1 pl-1 pr-3 lg:flex">
                <span className="grid h-7 w-7 place-items-center rounded-full bg-neutral-900 text-xs font-semibold text-white">
                  {initials(user.full_name)}
                </span>
                <span className="max-w-[140px] truncate text-sm font-medium text-neutral-700">
                  {user.full_name}
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wide text-neutral-900">
                  {user.role === "employer" ? "Employer" : "Seeker"}
                </span>
              </div>
              <button type="button" onClick={handleLogout} className="btn-secondary">
                <LogOut size={16} /> Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-ghost">
                Login
              </Link>
              <Link to="/register" className="btn-primary">
                Get started
              </Link>
            </>
          )}
        </nav>

        <button
          type="button"
          className="btn-ghost md:hidden"
          onClick={() => setOpen((value) => !value)}
          aria-label="Toggle navigation"
          aria-expanded={open}
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {open ? (
        <div className="border-t border-neutral-200 bg-white px-4 py-4 md:hidden">
          <div className="flex flex-col gap-1">
            <Link to="/" className="btn-ghost justify-start">
              Home
            </Link>
            {user ? (
              <>
                <Link to={dashboardPath} className="btn-ghost justify-start">
                  <LayoutDashboard size={16} /> Dashboard
                </Link>
                <div className="flex items-center gap-2 px-3 py-2">
                  <span className="grid h-8 w-8 place-items-center rounded-full bg-neutral-900 text-xs font-semibold text-white">
                    {initials(user.full_name)}
                  </span>
                  <div>
                    <p className="text-sm font-medium text-neutral-800">{user.full_name}</p>
                    <p className="text-xs capitalize text-neutral-500">{user.role?.replace("_", " ")}</p>
                  </div>
                </div>
                <button type="button" onClick={handleLogout} className="btn-secondary justify-start">
                  <LogOut size={16} /> Log out
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="btn-ghost justify-start">
                  Login
                </Link>
                <Link to="/register" className="btn-primary">
                  <BriefcaseBusiness size={16} /> Create account
                </Link>
              </>
            )}
          </div>
        </div>
      ) : null}
    </header>
  );
}
