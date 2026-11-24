import { scoreColor, scoreLabel } from "../lib/utils";

export default function ScoreRing({ score = 0, size = 68, showLabel = false }) {
  const clamped = Math.max(0, Math.min(100, Number(score) || 0));
  const radius = 26;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;
  const color = scoreColor(clamped);

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg viewBox="0 0 64 64" width={size} height={size} role="img" aria-label={`${Math.round(clamped)}% match`}>
          <circle cx="32" cy="32" r={radius} fill="none" stroke="#e5e5e5" strokeWidth="6" />
          <circle
            cx="32"
            cy="32"
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform="rotate(-90 32 32)"
            style={{ transition: "stroke-dashoffset 500ms ease" }}
          />
        </svg>
        <span
          className="absolute inset-0 grid place-items-center text-sm font-bold"
          style={{ color }}
        >
          {Math.round(clamped)}%
        </span>
      </div>
      {showLabel ? (
        <span className="text-[11px] font-medium uppercase tracking-wide text-neutral-500">
          {scoreLabel(clamped)}
        </span>
      ) : null}
    </div>
  );
}
