const VARIANTS = {
  matched: "bg-neutral-100 text-neutral-800 ring-1 ring-inset ring-neutral-200",
  missing: "bg-neutral-100 text-neutral-600 ring-1 ring-inset ring-neutral-100",
  course: "bg-neutral-100 text-black ring-1 ring-inset ring-neutral-200",
  neutral: "bg-neutral-100 text-neutral-600",
};

export function SkillTag({ children, variant = "neutral", title }) {
  return (
    <span title={title} className={`chip ${VARIANTS[variant] || VARIANTS.neutral}`}>
      {children}
    </span>
  );
}

export default SkillTag;

export function SkillList({ skills = [], variant = "neutral", limit, empty = "None listed" }) {
  if (!skills.length) return <span className="text-xs text-neutral-400">{empty}</span>;
  const shown = limit ? skills.slice(0, limit) : skills;
  return (
    <div className="flex flex-wrap gap-1.5">
      {shown.map((skill) => (
        <SkillTag key={skill} variant={variant}>
          {skill}
        </SkillTag>
      ))}
      {limit && skills.length > limit ? (
        <SkillTag variant="neutral">+{skills.length - limit} more</SkillTag>
      ) : null}
    </div>
  );
}
