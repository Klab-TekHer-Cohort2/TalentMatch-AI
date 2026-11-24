import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";

const AuthContext = createContext(null);

function readStoredUser() {
  try {
    const raw = localStorage.getItem("tm_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("tm_token"));
  const [user, setUser] = useState(readStoredUser);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      if (!localStorage.getItem("tm_token")) {
        setReady(true);
        return;
      }
      try {
        const me = await api.get("/auth/me");
        if (!cancelled) {
          setUser(me);
          localStorage.setItem("tm_user", JSON.stringify(me));
        }
      } catch {
        if (!cancelled) {
          localStorage.removeItem("tm_token");
          localStorage.removeItem("tm_user");
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) setReady(true);
      }
    }
    bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  const persist = useCallback((data) => {
    localStorage.setItem("tm_token", data.access_token);
    localStorage.setItem("tm_user", JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    return data.user;
  }, []);

  const login = useCallback(
    async (email, password) => {
      const data = await api.post("/auth/login", { email, password });
      return persist(data);
    },
    [persist],
  );

  const register = useCallback(
    async (payload) => {
      const data = await api.post("/auth/register", payload);
      if (!data.access_token) return null;
      return persist(data);
    },
    [persist],
  );

  const logout = useCallback(() => {
    localStorage.removeItem("tm_token");
    localStorage.removeItem("tm_user");
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    const me = await api.get("/auth/me");
    setUser(me);
    localStorage.setItem("tm_user", JSON.stringify(me));
    return me;
  }, []);

  const value = useMemo(
    () => ({ token, user, ready, login, register, logout, refreshUser }),
    [token, user, ready, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
