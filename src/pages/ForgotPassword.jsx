import { ArrowLeft, KeyRound, Mail } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import Alert from "../components/Alert";
import Footer from "../components/Footer";
import { Spinner } from "../components/Loader";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/forgot-password", { email: email.trim() });
      setSent(true);
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
            <KeyRound size={22} />
          </span>
          <h1 className="mt-4 text-2xl font-bold text-neutral-900">Forgot your password?</h1>
          <p className="mt-2 text-sm leading-relaxed text-neutral-600">
            Enter the email you use for TalentMatch and we&apos;ll send a link to reset your
            password.
          </p>

          {sent ? (
            <div className="mt-6 space-y-4">
              <Alert variant="success">
                If an account exists for <span className="font-semibold">{email}</span>, a reset
                link has been sent. Check your inbox (and spam folder).
              </Alert>
              <p className="text-sm text-neutral-600">
                The link expires in 60 minutes. If you don&apos;t receive it, confirm email delivery
                (SMTP) is configured on the server and that you entered the correct address.
              </p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {error ? <Alert variant="error">{error}</Alert> : null}
              <div>
                <label htmlFor="email" className="label">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  autoComplete="email"
                  className="input"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? <Spinner /> : <Mail size={16} />}
                {loading ? "Sending link…" : "Send reset link"}
              </button>
            </form>
          )}

          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/login" className="btn-secondary">
              <ArrowLeft size={16} /> Back to login
            </Link>
            <Link to="/register" className="btn-ghost">
              Create account
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
