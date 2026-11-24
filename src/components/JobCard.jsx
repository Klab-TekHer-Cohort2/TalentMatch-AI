import {
  Building2,
  CalendarDays,
  CheckCircle2,
  GraduationCap,
  MapPin,
  Send,
  Sparkles,
  Wallet,
} from "lucide-react";
import { formatDate, formatSalary, jobTypeLabel } from "../lib/utils";
import ScoreRing from "./ScoreRing";
import { SkillList } from "./SkillTag";

const MIN_APPLY_MATCH_SCORE = Number(import.meta.env.VITE_MIN_APPLY_MATCH_SCORE) || 50;

export default function JobCard({ job, applied = false, applying = false, onApply, onCourses }) {
  const matchScore = Number(job.score) || 0;
  const canApply = matchScore >= MIN_APPLY_MATCH_SCORE;

  return (
    <article className="card animate-fade-in p-5 sm:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold text-neutral-900">{job.title}</h3>
            <span className="chip bg-neutral-100 text-neutral-600">{jobTypeLabel(job.job_type)}</span>
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-neutral-500">
            <span className="inline-flex items-center gap-1.5">
              <Building2 size={14} /> {job.employer?.company_name || "Company"}
            </span>
            {job.location ? (
              <span className="inline-flex items-center gap-1.5">
                <MapPin size={14} /> {job.location}
              </span>
            ) : null}
            <span className="inline-flex items-center gap-1.5">
              <Wallet size={14} /> {formatSalary(job)}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <CalendarDays size={14} /> Apply by {formatDate(job.deadline)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3 sm:flex-col sm:items-end">
          <ScoreRing score={job.score} showLabel />
        </div>
      </div>

      <p className="mt-4 line-clamp-3 text-sm leading-relaxed text-neutral-600">{job.description}</p>

      <div className="mt-4 grid gap-4 rounded-xl border border-neutral-100 bg-neutral-50/60 p-4 sm:grid-cols-2">
        <div>
          <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-800">
            <CheckCircle2 size={14} /> Matched skills
          </p>
          <SkillList skills={job.matched_skills} variant="matched" limit={8} />
        </div>
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-600">
            Skill gaps
          </p>
          <SkillList skills={job.missing_skills} variant="missing" limit={8} empty="No gaps detected" />
        </div>
      </div>

      <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-neutral-200 bg-neutral-100/70 p-3.5 text-sm leading-relaxed text-black">
        <Sparkles size={16} className="mt-0.5 shrink-0 text-neutral-600" />
        <p>{job.explanation}</p>
      </div>

      <div className="mt-5 flex flex-col gap-2 sm:flex-row sm:justify-end">
        <button type="button" onClick={() => onCourses?.(job)} className="btn-secondary">
          <GraduationCap size={16} /> Courses to qualify
        </button>
        {applied ? (
          <span className="btn-secondary cursor-default border-neutral-200 bg-neutral-100 text-neutral-800">
            <CheckCircle2 size={16} /> Applied
          </span>
        ) : (
          <button
            type="button"
            onClick={() => onApply?.(job)}
            disabled={applying || !canApply}
            className="btn-primary"
            title={canApply ? undefined : `A ${MIN_APPLY_MATCH_SCORE}% match is required to apply`}
          >
            <Send size={16} /> {applying ? "Applying…" : "Apply now"}
          </button>
        )}
      </div>
      {!applied && !canApply ? (
        <p className="mt-3 text-right text-xs font-medium text-neutral-600">
          Your match is {matchScore}% — at least {MIN_APPLY_MATCH_SCORE}% is required to apply. Use the
          course plan to close the gaps.
        </p>
      ) : null}
    </article>
  );
}
