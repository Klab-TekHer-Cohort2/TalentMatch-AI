import { CheckCircle2, Mail, RotateCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Alert from "../components/Alert";
import Footer from "../components/Footer";
import { Spinner } from "../components/Loader";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";

export default function VerifyEmail() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [status, setStatus] = useState(token ? "verifying" : "missing");
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;

    let active = true;
    api.post("/auth/verify-email", { token })
      .then(() => {
        if (active) setStatus("verified");
      })
      .catch((err) => {
        if (active) {
          setError(err.message);
          setStatus("error");
        }
      });

    return () => {
      active = false;
    };
  }, [token]);

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="flex flex-1 items-center justify-center bg-neutral-50 px-4 py-12">
        <div className="w-full max-w-lg rounded-3xl border border-neutral-200 bg-white p-7 text-center shadow-xl sm:p-9">
          <span className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-neutral-100 text-neutral-900">
            {status === "verified" ? <CheckCircle2 size={22} /> : <Mail size={22} />}
          </span>
          <h1 className="mt-4 text-2xl font-bold text-neutral-900">
            {status === "verified" ? "Email verified" : "Verify your email"}
          </h1>

          {status === "verifying" ? (
            <div className="mt-6 flex justify-center"><Spinner /></div>
          ) : null}
          {status === "verified" ? (
            <>
              <p className="mt-2 text-sm text-neutral-600">
                You can now receive account notifications and use password reset.
              </p>
              <Link to="/login" className="btn-primary mt-6 w-full">Continue to login</Link>
            </>
          ) : null}
          {status === "error" ? <Alert className="mt-6" variant="error">{error}</Alert> : null}
          {status === "missing" ? (
            <Alert className="mt-6" variant="error">
              This verification link is missing a token.
            </Alert>
          ) : null}

          {status !== "verifying" ? (
            <Link to="/login" className="btn-secondary mt-4 w-full">
              <RotateCcw size={16} /> Back to login
            </Link>
          ) : null}
        </div>
      </main>
      <Footer />
    </div>
  );
}
