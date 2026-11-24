import { Loader2 } from "lucide-react";

export function Spinner({ size = 18, className = "" }) {
  return <Loader2 size={size} className={`animate-spin ${className}`} aria-hidden="true" />;
}

export function PageLoader({ label = "Loading…" }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-neutral-500">
      <Spinner size={28} className="text-neutral-900" />
      <p className="text-sm font-medium">{label}</p>
    </div>
  );
}

export function SkeletonCard({ rows = 3 }) {
  return (
    <div className="card animate-pulse p-5">
      <div className="h-5 w-2/3 rounded bg-neutral-200" />
      <div className="mt-3 h-3 w-1/3 rounded bg-neutral-100" />
      <div className="mt-6 space-y-2">
        {Array.from({ length: rows }).map((_, index) => (
          <div key={index} className="h-3 w-full rounded bg-neutral-100" />
        ))}
      </div>
    </div>
  );
}
