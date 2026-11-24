import { BookOpen, ShieldCheck, Sparkles } from "lucide-react";
import CourseCard from "./CourseCard";
import { SkillList } from "./SkillTag";

export default function AdvicePanel({ advice, gaps = [], courses = [], generatedBy, jobTitle }) {
  return (
    <div className="space-y-5">
      <div className="rounded-2xl border border-neutral-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-neutral-900">
              <Sparkles size={14} /> Course advisor
            </p>
            <h3 className="mt-1 text-lg font-semibold text-neutral-900">
              {jobTitle ? `Courses to qualify for ${jobTitle}` : "Courses for your skill gaps"}
            </h3>
          </div>
          {generatedBy ? (
            <span className="chip bg-neutral-100 text-neutral-500">
              {generatedBy === "claude" ? "Claude advice" : "Catalog advisor"}
            </span>
          ) : null}
        </div>

        <div className="mt-4">
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
            Identified gaps
          </p>
          <SkillList skills={gaps} variant="missing" empty="No skill gaps detected" />
        </div>

        <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-neutral-200 bg-neutral-100/70 p-4 text-sm leading-relaxed text-neutral-950">
          <BookOpen size={17} className="mt-0.5 shrink-0 text-neutral-600" />
          <p className="whitespace-pre-line">{advice}</p>
        </div>

        <p className="mt-3 flex items-center gap-1.5 text-xs text-neutral-400">
          <ShieldCheck size={13} /> Grounded in the TalentMatch catalog. Courses do not guarantee a job.
        </p>
      </div>

      {courses.length ? (
        <div className="grid gap-4 md:grid-cols-2">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} />
          ))}
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-neutral-300 bg-white p-6 text-center text-sm text-neutral-500">
          No catalog course matched these gaps yet.
        </div>
      )}
    </div>
  );
}
