import { Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="border-t border-neutral-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-10 sm:px-6 lg:flex-row lg:items-start lg:justify-between lg:px-8">
        <div className="max-w-sm">
          <div className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-neutral-900 to-neutral-700 text-white">
              <Sparkles size={15} />
            </span>
            <span className="font-bold text-neutral-900">TalentMatch AI</span>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-neutral-500">
            Fair, explainable matching between people and opportunities, with a course advisor
            grounded in a real catalog.
          </p>
        </div>
        <div className="grid grid-cols-2 gap-8 text-sm sm:grid-cols-3">
          <div>
            <p className="font-semibold text-neutral-900">Product</p>
            <ul className="mt-2 space-y-1.5 text-neutral-500">
              <li><Link className="hover:text-neutral-900" to="/register">Create account</Link></li>
              <li><Link className="hover:text-neutral-900" to="/login">Login</Link></li>
              <li><Link className="hover:text-neutral-900" to="/courses">Course catalog</Link></li>
            </ul>
          </div>
          <div>
            <p className="font-semibold text-neutral-900">For</p>
            <ul className="mt-2 space-y-1.5 text-neutral-500">
              <li><Link className="hover:text-neutral-900" to="/register?role=job_seeker">Job seekers</Link></li>
              <li><Link className="hover:text-neutral-900" to="/register?role=employer">Employers</Link></li>
            </ul>
          </div>
          <div className="col-span-2 sm:col-span-1">
            <p className="font-semibold text-neutral-900">Scope</p>
            <p className="mt-2 text-xs leading-relaxed text-neutral-500">
              TalentMatch supports recruitment decisions. It does not hire automatically, guarantee
              jobs, or issue certificates. Employers make the final decision.
            </p>
          </div>
        </div>
      </div>
      <div className="border-t border-neutral-100 py-4 text-center text-xs text-neutral-400">
        © {new Date().getFullYear()} TalentMatch AI. Demo project.
      </div>
    </footer>
  );
}
