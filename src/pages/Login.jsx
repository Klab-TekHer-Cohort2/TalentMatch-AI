import { Eye, EyeOff, LogIn, Mail, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import Alert from "../components/Alert";
import Footer from "../components/Footer";
import Navbar from "../components/Navbar";
import { Spinner } from "../components/Loader";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";

const DEMOS = [
  { label: "Job seeker demo", email: "alex@talentmatch.ai" },
  { label: "Employer demo", email: "employer+northstar@talentmatch.ai" },
];

export default function Login() {
  const { login, user, ready } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [otpStep, setOtpStep] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [otpSending, setOtpSending] = useState(false);
  const [otpLoading, setOtpLoading] = useState(false);
  const [otpMessage, setOtpMessage] = useState("");
  const [otpError, setOtpError] = useState("");

  if (ready && user) {
    return <Navigate to={user.role === "employer" ? "/employer" : "/seeker"} replace />;
  }

  function finishSignIn(signedIn) {
    const fallback = signedIn.role === "employer" ? "/employer" : "/seeker";
    navigate(location.state?.from || fallback, { replace: true });
  }

  async function sendCode(address) {
    setOtpError("");
    setOtpSending(true);
    try {
      const result = await api.post("/auth/request-email-otp", { email: address });
      setOtpMessage(result.message);
    } catch (err) {
      if (err.status === 429) {
        setOtpMessage("A code was already sent. Check your inbox or wait before requesting another.");
      } else {
        setOtpError(err.message);
      }
    } finally {
      setOtpSending(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      finishSignIn(await login(email.trim(), password));
    } catch (err) {
      if (err.code === "EMAIL_NOT_VERIFIED") {
        setOtpStep(true);
        setOtpCode("");
        await sendCode(email.trim());
      } else {
        setError(err.message);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleOtpSubmit(event) {
    event.preventDefault();
    setOtpError("");
    setOtpLoading(true);
    try {
      await api.post("/auth/verify-email-otp", { email: email.trim(), code: otpCode.trim() });
      finishSignIn(await login(email.trim(), password));
    } catch (err) {
      setOtpError(err.message);
    } finally {
      setOtpLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex flex-1 items-center justify-center bg-neutral-50 px-4 py-12">
        <div className="grid w-full max-w-4xl overflow-hidden rounded-3xl border border-neutral-200 bg-white shadow-xl lg:grid-cols-2">
          <div className="hidden flex-col justify-between bg-gradient-to-br from-neutral-900 via-black to-neutral-800 p-9 text-white lg:flex">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold">
                <Sparkles size={13} /> TalentMatch AI
              </span>
              <h1 className="mt-6 text-3xl font-bold leading-tight">
                Welcome back to fairer, clearer hiring.
              </h1>
              <p className="mt-3 text-sm leading-relaxed text-neutral-200">
                Pick up your matches, applications and personalized course plan where you left off.
              </p>
            </div>
            <div className="space-y-3 text-sm text-neutral-200">
              <p className="font-semibold text-white">Demo accounts</p>
              {DEMOS.map((demo) => (
                <button
                  key={demo.email}
                  type="button"
                  onClick={() => {
                    setEmail(demo.email);
                    setPassword("Password123!");
                    setError("");
                  }}
                  className="block w-full rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-left transition hover:bg-white/20"
                >
                  <span className="block text-xs font-semibold uppercase tracking-wide text-neutral-200">
                    {demo.label}
                  </span>
                  <span className="text-sm">{demo.email}</span>
                  <span className="block text-xs text-neutral-200">Password123!</span>
                </button>
              ))}
            </div>
          </div>

          <div className="p-7 sm:p-9">
            <h2 className="text-2xl font-bold text-neutral-900">Log in</h2>
            <p className="mt-1 text-sm text-neutral-500">
              Use your job seeker or employer account.
            </p>

            {otpStep ? (
              <form onSubmit={handleOtpSubmit} className="mt-6 space-y-4">
                <Alert variant="info">
                  Enter the 6-digit code sent to <span className="font-semibold">{email}</span> to verify your email and sign in.
                </Alert>
                {otpMessage ? <Alert variant="success">{otpMessage}</Alert> : null}
                {otpError ? <Alert variant="error">{otpError}</Alert> : null}
                <div>
                  <label htmlFor="otp" className="label">
                    Verification code
                  </label>
                  <input
                    id="otp"
                    type="text"
                    inputMode="numeric"
                    autoComplete="one-time-code"
                    pattern="[0-9]{6}"
                    maxLength={6}
                    required
                    className="input text-center text-lg tracking-[0.4em]"
                    placeholder="000000"
                    value={otpCode}
                    onChange={(event) => setOtpCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
                  />
                </div>
                <button type="submit" disabled={otpLoading} className="btn-primary w-full">
                  {otpLoading ? <Spinner /> : <Mail size={16} />}
                  {otpLoading ? "Verifying…" : "Verify and sign in"}
                </button>
                <button type="button" disabled={otpSending} className="btn-secondary w-full" onClick={() => sendCode(email.trim())}>
                  {otpSending ? "Sending…" : "Resend code"}
                </button>
                <button
                  type="button"
                  className="w-full text-xs font-medium text-neutral-500 hover:text-black"
                  onClick={() => {
                    setOtpStep(false);
                    setOtpError("");
                    setOtpMessage("");
                  }}
                >
                  Use a different account
                </button>
              </form>
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
              <div>
                <div className="flex items-center justify-between">
                  <label htmlFor="password" className="label mb-0">
                    Password
                  </label>
                  <Link
                    to="/forgot-password"
                    className="text-xs font-medium text-neutral-900 hover:text-black"
                  >
                    Forgot password?
                  </Link>
                </div>
                <div className="relative mt-1.5">
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    required
                    autoComplete="current-password"
                    className="input pr-11"
                    placeholder="Your password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((value) => !value)}
                    className="absolute inset-y-0 right-0 grid w-10 place-items-center text-neutral-400 hover:text-neutral-600"
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                  </button>
                </div>
              </div>
              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? <Spinner /> : <LogIn size={16} />}
                {loading ? "Signing in…" : "Sign in"}
              </button>
            </form>
            )}

            <div className="mt-5 rounded-xl bg-neutral-50 p-3 text-xs text-neutral-500 lg:hidden">
              <p className="font-semibold text-neutral-700">Demo credentials</p>
              <p className="mt-1">Seeker: alex@talentmatch.ai</p>
              <p>Employer: employer+northstar@talentmatch.ai</p>
              <p className="mt-1">Password: Password123!</p>
              <div className="mt-2 flex flex-wrap gap-2">
                {DEMOS.map((demo) => (
                  <button
                    key={demo.email}
                    type="button"
                    className="rounded-lg border border-neutral-200 bg-white px-2 py-1 font-medium text-neutral-600"
                    onClick={() => {
                      setEmail(demo.email);
                      setPassword("Password123!");
                    }}
                  >
                    {demo.label}
                  </button>
                ))}
              </div>
            </div>

            <p className="mt-6 text-center text-sm text-neutral-500">
              New to TalentMatch?{" "}
              <Link to="/register" className="font-semibold text-neutral-900 hover:text-black">
                Create an account
              </Link>
            </p>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
