export function classNames(...values) {
  return values.filter(Boolean).join(" ");
}

export function initials(name = "") {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

const JOB_TYPES = {
  full_time: "Full-time",
  part_time: "Part-time",
  contract: "Contract",
  internship: "Internship",
  remote: "Remote",
};

export function jobTypeLabel(value) {
  return JOB_TYPES[value] || value || "Not specified";
}

export function formatSalary(job) {
  if (!job?.salary_min && !job?.salary_max) return "Salary not disclosed";
  const format = (value) =>
    new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(value);
  const currency = job.currency || "USD";
  if (job.salary_min && job.salary_max) {
    return `${currency} ${format(job.salary_min)} – ${format(job.salary_max)}`;
  }
  return `${currency} ${format(job.salary_min || job.salary_max)}`;
}

export function formatDate(value) {
  if (!value) return "No deadline";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("en", { year: "numeric", month: "short", day: "numeric" });
}

export function scoreColor(score = 0) {
  if (score >= 75) return "#000000";
  if (score >= 50) return "#525252";
  return "#a3a3a3";
}

export function scoreLabel(score = 0) {
  if (score >= 75) return "Strong match";
  if (score >= 50) return "Good match";
  return "Partial match";
}

export function formatRelative(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const diff = Date.now() - date.getTime();
  const days = Math.floor(diff / 86400000);
  if (days <= 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 30) return `${days} days ago`;
  return formatDate(value);
}
