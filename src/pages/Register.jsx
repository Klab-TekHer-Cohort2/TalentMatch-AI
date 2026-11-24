import { BriefcaseBusiness, Eye, EyeOff, Mail, Search, Sparkles, UserPlus } from "lucide-react";
import { useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import Alert from "../components/Alert";
import Footer from "../components/Footer";
import Navbar from "../components/Navbar";
import { Spinner } from "../components/Loader";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";

export default function Register() {
  const { login, register, user, ready } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [role, setRole] = useState(params.get("role") === "employer" ? "employer" : "job_seeker");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        full_name: fullName.trim(),
        email: email.trim(),
        password,
        role,
      };
      if (role === "employer" && companyName.trim()) payload.company_name = companyName.trim();
      const signedIn = await register(payload);
      if (signedIn) {
        navigate(signedIn.role === "employer" ? "/employer" : "/seeker", { replace: true });
        return;
      }
      setOtpStep(true);
      setOtpCode("");
      setOtpMessage(`A 6-digit verification code was sent to ${email.trim()}.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function sendCode() {
    setOtpError("");
    setOtpSending(true);
    try {
      const result = await api.post("/auth/request-email-otp", { email: email.trim() });
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

  async function handleOtpSubmit(event) {
    event.preventDefault();
    setOtpError("");
    setOtpLoading(true);
    try {
      await api.post("/auth/verify-email-otp", { email: email.trim(), code: otpCode.trim() });
      const signedIn = await login(email.trim(), password);
      navigate(signedIn.role === "employer" ? "/employer" : "/seeker", { replace: true });
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
        <div className="grid w-full max-w-5xl overflow-hidden rounded-3xl border border-neutral-200 bg-white shadow-xl lg:grid-cols-[0.85fr_1.15fr]">
          <div className="hidden flex-col justify-between bg-gradient-to-br from-neutral-900 via-neutral-950 to-black p-9 text-white lg:flex">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold">
                <Sparkles size={13} /> Join TalentMatch AI
              </span>
              <h1 className="mt-6 text-3xl font-bold leading-tight">
                One account. Clear matches. Real next steps.
              </h1>
              <ul className="mt-6 space-y-3 text-sm text-neutral-200">
                <li>Structured CV analysis with skills, education and experience.</li>
                <li>Hybrid 60/40 match scores with explanations and skill gaps.</li>
                <li>Course advice grounded strictly in the catalog.</li>
                <li>No demographic attributes used in matching.</li>
              </ul>
            </div>
            <div className="rounded-xl border border-white/15 bg-white/5 p-4 text-xs leading-relaxed text-neutral-200">
              TalentMatch supports recruitment only. It never hires automatically, guarantees a job,
              or issues certificates.
            </div>
          </div>

          <div className="p-7 sm:p-9">
            <h2 className="text-2xl font-bold text-neutral-900">Create your account</h2>
            <p className="mt-1 text-sm text-neutral-500">Choose your role to get the right workspace.</p>

            <div className="mt-5 grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setRole("job_seeker")}
                aria-pressed={role === "job_seeker"}
                className={`rounded-xl border p-3 text-left transition ${
                  role === "job_seeker"
                    ? "border-neutral-900 bg-neutral-100 ring-2 ring-neutral-200"
                    : "border-neutral-200 hover:border-neutral-300"
                }`}
              >
                <Search size={18} className={role === "job_seeker" ? "text-neutral-900" : "text-neutral-400"} />
                <p className="mt-2 text-sm font-semibold text-neutral-900">Job seeker</p>
                <p className="text-xs text-neutral-500">Find roles and close gaps</p>
              </button>
              <button
                type="button"
                onClick={() => setRole("employer")}
                aria-pressed={role === "employer"}
                className={`rounded-xl border p-3 text-left transition ${
                  role === "employer"
                    ? "border-neutral-900 bg-neutral-100 ring-2 ring-neutral-200"
                    : "border-neutral-200 hover:border-neutral-300"
                }`}
              >
                <BriefcaseBusiness
                  size={18}
                  className={role === "employer" ? "text-neutral-900" : "text-neutral-400"}
                />
                <p className="mt-2 text-sm font-semibold text-neutral-900">Employer</p>
                <p className="text-xs text-neutral-500">Post jobs and shortlist</p>
              </button>
            </div>

            {otpStep ? (
              <form onSubmit={handleOtpSubmit} className="mt-6 space-y-4">
                <Alert variant="info">
                  Enter the 6-digit code sent to <span className="font-semibold">{email}</span> to activate your account.
                </Alert>
                {otpMessage ? <Alert variant="success">{otpMessage}</Alert> : null}
                {otpError ? <Alert variant="error">{otpError}</Alert> : null}
                <div>
                  <label htmlFor="signup_otp" className="label">
                    Verification code
                  </label>
                  <input
                    id="signup_otp"
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
                  {otpLoading ? "Verifying…" : "Verify and continue"}
                </button>
                <button type="button" disabled={otpSending} className="btn-secondary w-full" onClick={sendCode}>
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
                  Use different details
                </button>
              </form>
            ) : (
            <form onSubmit={handleSubmit} className="mt-5 space-y-4">
              {error ? <Alert variant="error">{error}</Alert> : null}
              <div>
                <label htmlFor="full_name" className="label">
                  Full name
                </label>
                <input
                  id="full_name"
                  required
                  minLength={2}
                  maxLength={120}
                  className="input"
                  placeholder="Alex Rivera"
                  autoComplete="name"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                />
              </div>

              {role === "employer" ? (
                <div>
                  <label htmlFor="company_name" className="label">
                    Company name <span className="font-normal text-neutral-400">(optional)</span>
                  </label>
                  <input
                    id="company_name"
                    maxLength={160}
                    className="input"
                    placeholder="Northstar Labs"
                    value={companyName}
                    onChange={(event) => setCompanyName(event.target.value)}
                  />
                </div>
              ) : null}

              <div>
                <label htmlFor="email" className="label">
                  Email address
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  className="input"
                  placeholder="you@example.com"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                />
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="password" className="label">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      required
                      minLength={8}
                      maxLength={72}
                      className="input pr-10"
                      placeholder="8+ characters"
                      autoComplete="new-password"
                      value={password}
                      onChange={(event) => setPassword(event.target.value)}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((value) => !value)}
                      className="absolute inset-y-0 right-0 grid w-9 place-items-center text-neutral-400 hover:text-neutral-600"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
                <div>
                  <label htmlFor="confirm_password" className="label">
                    Confirm password
                  </label>
                  <input
                    id="confirm_password"
                    type={showPassword ? "text" : "password"}
                    required
                    className="input"
                    placeholder="Repeat password"
                    autoComplete="new-password"
                    value={confirmPassword}
                    onChange={(event) => setConfirmPassword(event.target.value)}
                  />
                </div>
              </div>

              <button type="submit" disabled={loading} className="btn-primary w-full">
                {loading ? <Spinner /> : <UserPlus size={16} />}
                {loading ? "Creating account…" : "Create account"}
              </button>
            </form>
            )}

            <p className="mt-5 text-center text-sm text-neutral-500">
              Already registered?{" "}
              <Link to="/login" className="font-semibold text-neutral-900 hover:text-black">
                Log in
              </Link>
            </p>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
