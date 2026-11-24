import { Clock, ExternalLink, Layers, Target } from "lucide-react";
import SkillTag from "./SkillTag";

export default function CourseCard({ course, showRelevance = true }) {
  return (
    <article className="card flex h-full flex-col p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-neutral-900">
            {course.provider}
          </p>
          <h3 className="mt-1 text-base font-semibold leading-snug text-neutral-900">{course.title}</h3>
        </div>
        {showRelevance && course.relevance > 0 ? (
          <span className="chip shrink-0 bg-neutral-100 text-black" title="Semantic relevance">
            {Math.round(course.relevance)}%
          </span>
        ) : null}
      </div>

      <p className="mt-2 line-clamp-3 flex-1 text-sm leading-relaxed text-neutral-600">
        {course.description}
      </p>

      {course.covers?.length ? (
        <div className="mt-3">
          <p className="mb-1.5 flex items-center gap-1 text-xs font-semibold text-neutral-500">
            <Target size={13} /> Fills your gaps
          </p>
          <div className="flex flex-wrap gap-1.5">
            {course.covers.map((skill) => (
              <SkillTag key={skill} variant="matched">
                {skill}
              </SkillTag>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-neutral-500">
        <span className="inline-flex items-center gap-1">
          <Layers size={13} /> {course.level}
        </span>
        <span className="inline-flex items-center gap-1">
          <Clock size={13} /> {course.duration || "Self-paced"}
        </span>
      </div>

      <a
        href={course.url}
        target="_blank"
        rel="noreferrer noopener"
        className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-neutral-900 hover:text-black"
      >
        View course <ExternalLink size={14} />
      </a>
    </article>
  );
}
