import { ArrowLeft, CheckCircle2, KeyRound } from "lucide-react";
import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Alert from "../components/Alert";
import Footer from "../components/Footer";
import { Spinner } from "../components/Loader";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";

export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    if (!token) {
      setError("Reset link is missing or invalid. Request a new one.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      await api.post("/auth/reset-password", { token, new_password: password });
      setDone(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex flex-1 items-center justify-center bg-neutral-50 px-4 py-12">
        <div className="w-full max-w-lg rounded-3xl border border-neutral-200 bg-white p-7 shadow-xl sm:p-9">
          <span className="grid h-12 w-12 place-items-center rounded-xl bg-neutral-100 text-neutral-900">
            {done ? <CheckCircle2 size={22} /> : <KeyRound size={22} />}
          </span>
          <h1 className="mt-4 text-2xl font-bold text-neutral-900">
            {done ? "Password reset" : "Choose a new password"}
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-neutral-600">
            {done
              ? "Your password has been updated. You can now sign in with your new password."
              : "Enter a new password for your TalentMatch account."}
          </p>

          {!token && !done ? (
            <Alert className="mt-6" variant="error">
              This reset link is missing a token. Use the link from your email or{" "}
              <Link to="/forgot-password" className="font-semibold underline">
                request a new one
              </Link>
              .
            </Alert>
          ) : null}

          {done ? (
            <div className="mt-6">
              <Link to="/login" className="btn-primary w-full">
                <ArrowLeft size={16} /> Go to login
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {error ? <Alert variant="error">{error}</Alert> : null}
              <div>
                <label htmlFor="new_password" className="label">
                  New password
                </label>
                <input
                  id="new_password"
                  type="password"
                  required
                  minLength={8}
                  maxLength={72}
                  autoComplete="new-password"
                  className="input"
                  placeholder="At least 8 characters"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />
              </div>
              <div>
                <label htmlFor="confirm_password" className="label">
                  Confirm new password
                </label>
                <input
                  id="confirm_password"
                  type="password"
                  required
                  autoComplete="new-password"
                  className="input"
                  value={confirm}
                  onChange={(event) => setConfirm(event.target.value)}
                />
              </div>
              <button type="submit" disabled={loading || !token} className="btn-primary w-full">
                {loading ? <Spinner /> : <KeyRound size={16} />}
                {loading ? "Resetting…" : "Reset password"}
              </button>
              <p className="text-center text-sm text-neutral-500">
                <Link to="/forgot-password" className="font-medium text-neutral-900 hover:text-black">
                  Request a new link
                </Link>
              </p>
            </form>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
