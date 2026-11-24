import {
  BriefcaseBusiness,
  Building2,
  CalendarDays,
  CheckCircle2,
  FileText,
  KeyRound,
  Mail,
  MapPin,
  PlusCircle,
  RefreshCw,
  Save,
  Sparkles,
  Trash2,
  Users,
  Wallet,
} from "lucide-react";
import { useEffect, useState } from "react";
import Alert from "../components/Alert";
import DashboardTabs from "../components/DashboardTabs";
import EmptyState from "../components/EmptyState";
import { PageLoader, SkeletonCard, Spinner } from "../components/Loader";
import Modal from "../components/Modal";
import Navbar from "../components/Navbar";
import ScoreRing from "../components/ScoreRing";
import { SkillList, SkillTag } from "../components/SkillTag";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { formatDate, formatRelative, formatSalary, jobTypeLabel } from "../lib/utils";

const TABS = [
  { key: "jobs", label: "My jobs", icon: BriefcaseBusiness },
  { key: "post", label: "Post a job", icon: PlusCircle },
  { key: "candidates", label: "Candidates", icon: Users },
];

const EMPTY_JOB = {
  title: "",
  description: "",
  required_skills: "",
  location: "",
  job_type: "full_time",
  salary_min: "",
  salary_max: "",
  currency: "EUR",
  deadline: "",
};

const today = new Date().toISOString().slice(0, 10);

export default function EmployerDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState("jobs");
  const [profile, setProfile] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(null);

  const [profileOpen, setProfileOpen] = useState(false);
  const [profileForm, setProfileForm] = useState({
    company_name: "",
    website: "",
    location: "",
    description: "",
  });
  const [savingProfile, setSavingProfile] = useState(false);
  const [profileError, setProfileError] = useState("");

  const [form, setForm] = useState(EMPTY_JOB);
  const [posting, setPosting] = useState(false);
  const [postError, setPostError] = useState("");
  const [createdJob, setCreatedJob] = useState(null);

  const [selectedJobId, setSelectedJobId] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  const [candidatesError, setCandidatesError] = useState("");
  const [candidateFilter, setCandidateFilter] = useState("all");
  const [actionId, setActionId] = useState(null);
  const [actionError, setActionError] = useState("");

  const [passwordOpen, setPasswordOpen] = useState(false);
  const [passwordForm, setPasswordForm] = useState({ current: "", next: "", confirm: "" });
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordError, setPasswordError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [profileData, jobData] = await Promise.all([
          api.get("/employer/profile"),
          api.get("/employer/jobs"),
        ]);
        if (cancelled) return;
        setProfile(profileData);
        setProfileForm({
          company_name: profileData.company_name || "",
          website: profileData.website || "",
          location: profileData.location || "",
          description: profileData.description || "",
        });
        setJobs(jobData);
        if (jobData.length && !selectedJobId) setSelectedJobId(jobData[0].id);
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(null), 6000);
    return () => clearTimeout(timer);
  }, [notice]);

  const selectedJob = jobs.find((job) => job.id === selectedJobId) || null;
  const appliedCandidates = candidates.filter((candidate) => candidate.applied);
  const eligibleCandidates = candidates.filter((candidate) => candidate.eligible);
  const visibleCandidates =
    candidateFilter === "applied"
      ? appliedCandidates
      : candidateFilter === "eligible"
        ? eligibleCandidates
        : candidates;

  async function loadJobs() {
    try {
      const data = await api.get("/employer/jobs");
      setJobs(data);
      if (!selectedJobId && data.length) setSelectedJobId(data[0].id);
    } catch (err) {
      setError(err.message);
    }
  }

  async function loadCandidates(jobId) {
    if (!jobId) {
      setCandidates([]);
      return;
    }
    setCandidatesLoading(true);
    setCandidatesError("");
    setCandidates([]);
    try {
      const data = await api.get(`/employer/jobs/${jobId}/candidates`);
      setCandidates(data);
    } catch (err) {
      setCandidatesError(err.message);
      setCandidates([]);
    } finally {
      setCandidatesLoading(false);
    }
  }

  function openCandidates(job) {
    setSelectedJobId(job.id);
    setCandidateFilter("all");
    setTab("candidates");
    loadCandidates(job.id);
  }

  async function handlePostJob(event) {
    event.preventDefault();
    setPosting(true);
    setPostError("");
    setCreatedJob(null);
    try {
      const payload = {
        title: form.title.trim(),
        description: form.description.trim(),
        required_skills: form.required_skills
          .split(",")
          .map((skill) => skill.trim())
          .filter(Boolean),
        location: form.location.trim() || null,
        job_type: form.job_type,
        salary_min: form.salary_min === "" ? null : Number(form.salary_min),
        salary_max: form.salary_max === "" ? null : Number(form.salary_max),
        currency: form.currency.trim() || "USD",
        deadline: form.deadline || null,
      };
      const job = await api.post("/employer/jobs", payload);
      setJobs((previous) => [job, ...previous]);
      setCreatedJob(job);
      setForm(EMPTY_JOB);
      setTab("jobs");
      setNotice({ variant: "success", message: "Job posted. Skills were auto-extracted from the description." });
    } catch (err) {
      setPostError(err.message);
    } finally {
      setPosting(false);
    }
  }

  async function saveCompanyProfile(event) {
    event.preventDefault();
    setSavingProfile(true);
    setProfileError("");
    try {
      const updated = await api.put("/employer/profile", {
        company_name: profileForm.company_name.trim(),
        website: profileForm.website.trim() || null,
        location: profileForm.location.trim() || null,
        description: profileForm.description.trim() || null,
      });
      setProfile(updated);
      setProfileOpen(false);
      setNotice({ variant: "success", message: "Company profile updated." });
    } catch (err) {
      setProfileError(err.message);
    } finally {
      setSavingProfile(false);
    }
  }

  async function changePassword(event) {
    event.preventDefault();
    setPasswordError("");
    if (passwordForm.next.length < 8) {
      setPasswordError("New password must be at least 8 characters.");
      return;
    }
    if (passwordForm.next !== passwordForm.confirm) {
      setPasswordError("New passwords do not match.");
      return;
    }
    setChangingPassword(true);
    try {
      await api.post("/auth/change-password", {
        current_password: passwordForm.current,
        new_password: passwordForm.next,
      });
      setPasswordOpen(false);
      setPasswordForm({ current: "", next: "", confirm: "" });
      setNotice({ variant: "success", message: "Password updated successfully." });
    } catch (err) {
      setPasswordError(err.message);
    } finally {
      setChangingPassword(false);
    }
  }

  async function toggleJobStatus(job) {
    setActionId(job.id);
    setActionError("");
    try {
      const updated = await api.patch(`/employer/jobs/${job.id}`, {
        status: job.status === "open" ? "closed" : "open",
      });
      setJobs((previous) => previous.map((item) => (item.id === job.id ? updated : item)));
      setNotice({
        variant: "success",
        message: updated.status === "open" ? "Job reopened." : "Job closed to new applications.",
      });
    } catch (err) {
      setActionError(err.message);
    } finally {
      setActionId(null);
    }
  }

  async function deleteJob(job) {
    const confirmed = window.confirm(
      `Delete “${job.title}”? Applications for this job will also be removed. This cannot be undone.`,
    );
    if (!confirmed) return;
    setActionId(job.id);
    setActionError("");
    try {
      await api.delete(`/employer/jobs/${job.id}`);
      setJobs((previous) => previous.filter((item) => item.id !== job.id));
      if (selectedJobId === job.id) {
        setSelectedJobId(null);
        setCandidates([]);
      }
      setNotice({ variant: "success", message: "Job deleted." });
    } catch (err) {
      setActionError(err.message);
    } finally {
      setActionId(null);
    }
  }

  const tabs = TABS.map((item) => ({
    ...item,
    count: item.key === "jobs" ? jobs.length : undefined,
  }));

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-50">
        <Navbar />
        <PageLoader label="Loading your employer workspace…" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      <Navbar />
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-neutral-900">
              Employer workspace
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-neutral-900 sm:text-3xl">
              {profile?.company_name || "Your company"}
            </h1>
            <p className="mt-1 text-sm text-neutral-500">
              Post roles, manage your listings and review ranked candidates.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <button type="button" onClick={() => setProfileOpen(true)} className="btn-secondary">
              <Building2 size={16} /> Company profile
            </button>
            <button
              type="button"
              onClick={() => {
                setPasswordError("");
                setPasswordForm({ current: "", next: "", confirm: "" });
                setPasswordOpen(true);
              }}
              className="btn-secondary"
            >
              <KeyRound size={16} /> Change password
            </button>
            <button type="button" onClick={() => setTab("post")} className="btn-primary">
              <PlusCircle size={16} /> Post a job
            </button>
          </div>
        </div>

        <div className="mt-6">
          <DashboardTabs items={tabs} active={tab} onChange={setTab} />
        </div>

        <div className="mt-5 space-y-4">
          {notice ? (
            <Alert variant={notice.variant} onClose={() => setNotice(null)}>
              {notice.message}
            </Alert>
          ) : null}
          {error ? <Alert variant="error">{error}</Alert> : null}
          {actionError ? (
            <Alert variant="error" onClose={() => setActionError("")}>
              {actionError}
            </Alert>
          ) : null}
        </div>

        {tab === "jobs" ? (
          <div className="mt-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-neutral-900">Your job posts</h2>
                <p className="muted">You can only edit, close or delete your own jobs.</p>
              </div>
              <button type="button" onClick={loadJobs} className="btn-secondary">
                <RefreshCw size={15} /> Refresh
              </button>
            </div>

            {createdJob ? (
              <Alert className="mt-4" variant="success">
                <p className="font-semibold">“{createdJob.title}” is live.</p>
                <p className="mt-1 text-xs">
                  Auto-extracted skills: {(createdJob.required_skills || []).join(", ") || "none detected — add them manually next time."}
                </p>
              </Alert>
            ) : null}

            {jobs.length ? (
              <div className="mt-5 space-y-4">
                {jobs.map((job) => (
                  <article key={job.id} className="card p-5 sm:p-6">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-lg font-semibold text-neutral-900">{job.title}</h3>
                          <span
                            className={`chip capitalize ${
                              job.status === "open"
                                ? "bg-neutral-100 text-neutral-800"
                                : "bg-neutral-100 text-neutral-500"
                            }`}
                          >
                            {job.status}
                          </span>
                          <span className="chip bg-neutral-100 text-black">
                            {job.application_count} application{job.application_count === 1 ? "" : "s"}
                          </span>
                        </div>
                        <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-sm text-neutral-500">
                          {job.location ? (
                            <span className="inline-flex items-center gap-1.5">
                              <MapPin size={14} /> {job.location}
                            </span>
                          ) : null}
                          <span>{jobTypeLabel(job.job_type)}</span>
                          <span className="inline-flex items-center gap-1.5">
                            <Wallet size={14} /> {formatSalary(job)}
                          </span>
                          <span className="inline-flex items-center gap-1.5">
                            <CalendarDays size={14} /> {formatDate(job.deadline)}
                          </span>
                          <span className="text-xs text-neutral-400">Posted {formatRelative(job.created_at)}</span>
                        </div>
                      </div>
                    </div>

                    <p className="mt-3 line-clamp-2 text-sm leading-relaxed text-neutral-600">
                      {job.description}
                    </p>

                    <div className="mt-3">
                      <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                        Required skills
                      </p>
                      <SkillList skills={job.required_skills} variant="course" limit={12} empty="No skills detected" />
                    </div>

                    <div className="mt-5 flex flex-wrap gap-2">
                      <button type="button" onClick={() => openCandidates(job)} className="btn-primary">
                        <Users size={15} /> View candidates
                      </button>
                      <button
                        type="button"
                        onClick={() => toggleJobStatus(job)}
                        disabled={actionId === job.id}
                        className="btn-secondary"
                      >
                        {actionId === job.id ? <Spinner /> : <BriefcaseBusiness size={15} />}
                        {job.status === "open" ? "Close job" : "Reopen job"}
                      </button>
                      <button
                        type="button"
                        onClick={() => deleteJob(job)}
                        disabled={actionId === job.id}
                        className="btn-danger"
                      >
                        {actionId === job.id ? <Spinner /> : <Trash2 size={15} />} Delete
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="mt-5">
                <EmptyState
                  icon={BriefcaseBusiness}
                  title="No jobs posted yet"
                  description="Create your first role. Required skills are extracted automatically from the description."
                  action={
                    <button type="button" className="btn-primary" onClick={() => setTab("post")}>
                      <PlusCircle size={16} /> Post a job
                    </button>
                  }
                />
              </div>
            )}
          </div>
        ) : null}

        {tab === "post" ? (
          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <form onSubmit={handlePostJob} className="card space-y-4 p-6 lg:col-span-2">
              <div>
                <h2 className="text-lg font-semibold text-neutral-900">Post a new job</h2>
                <p className="muted mt-1">
                  Skills are extracted from the description; you can also add or override them.
                </p>
              </div>

              {postError ? <Alert variant="error">{postError}</Alert> : null}

              <div>
                <label htmlFor="title" className="label">Job title</label>
                <input
                  id="title"
                  required
                  minLength={3}
                  maxLength={160}
                  className="input"
                  placeholder="Senior Full Stack Engineer"
                  value={form.title}
                  onChange={(event) => setForm({ ...form, title: event.target.value })}
                />
              </div>

              <div>
                <label htmlFor="description" className="label">Job description</label>
                <textarea
                  id="description"
                  required
                  minLength={30}
                  maxLength={20000}
                  rows={7}
                  className="input resize-y"
                  placeholder="Describe responsibilities, stack and requirements…"
                  value={form.description}
                  onChange={(event) => setForm({ ...form, description: event.target.value })}
                />
                <p className="mt-1 text-xs text-neutral-400">
                  Minimum 30 characters. Be specific about tools and skills for better matching.
                </p>
              </div>

              <div>
                <label htmlFor="required_skills" className="label">
                  Required skills <span className="font-normal text-neutral-400">(optional, comma separated)</span>
                </label>
                <input
                  id="required_skills"
                  className="input"
                  placeholder="React, TypeScript, PostgreSQL"
                  value={form.required_skills}
                  onChange={(event) => setForm({ ...form, required_skills: event.target.value })}
                />
                <p className="mt-1 text-xs text-neutral-400">
                  Leave blank to rely fully on automatic extraction.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="location" className="label">Location</label>
                  <input
                    id="location"
                    className="input"
                    placeholder="Remote (EU)"
                    value={form.location}
                    onChange={(event) => setForm({ ...form, location: event.target.value })}
                  />
                </div>
                <div>
                  <label htmlFor="job_type" className="label">Job type</label>
                  <select
                    id="job_type"
                    className="input"
                    value={form.job_type}
                    onChange={(event) => setForm({ ...form, job_type: event.target.value })}
                  >
                    <option value="full_time">Full-time</option>
                    <option value="part_time">Part-time</option>
                    <option value="contract">Contract</option>
                    <option value="internship">Internship</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="salary_min" className="label">Salary minimum</label>
                  <input
                    id="salary_min"
                    type="number"
                    min="0"
                    className="input"
                    placeholder="70000"
                    value={form.salary_min}
                    onChange={(event) => setForm({ ...form, salary_min: event.target.value })}
                  />
                </div>
                <div>
                  <label htmlFor="salary_max" className="label">Salary maximum</label>
                  <input
                    id="salary_max"
                    type="number"
                    min="0"
                    className="input"
                    placeholder="95000"
                    value={form.salary_max}
                    onChange={(event) => setForm({ ...form, salary_max: event.target.value })}
                  />
                </div>
                <div>
                  <label htmlFor="currency" className="label">Currency</label>
                  <input
                    id="currency"
                    maxLength={10}
                    className="input"
                    value={form.currency}
                    onChange={(event) => setForm({ ...form, currency: event.target.value.toUpperCase() })}
                  />
                </div>
                <div>
                  <label htmlFor="deadline" className="label">Application deadline</label>
                  <input
                    id="deadline"
                    type="date"
                    min={today}
                    className="input"
                    value={form.deadline}
                    onChange={(event) => setForm({ ...form, deadline: event.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 border-t border-neutral-100 pt-4">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setForm(EMPTY_JOB);
                    setPostError("");
                  }}
                >
                  Reset
                </button>
                <button type="submit" disabled={posting} className="btn-primary">
                  {posting ? <Spinner /> : <PlusCircle size={16} />}
                  {posting ? "Posting…" : "Publish job"}
                </button>
              </div>
            </form>

            <aside className="space-y-5">
              {createdJob ? (
                <div className="card p-5">
                  <p className="flex items-center gap-2 text-sm font-semibold text-neutral-800">
                    <CheckCircle2 size={16} /> Last job published
                  </p>
                  <h3 className="mt-2 font-semibold text-neutral-900">{createdJob.title}</h3>
                  <p className="mt-1 text-xs text-neutral-500">
                    {createdJob.application_count} applications · {formatDate(createdJob.deadline)}
                  </p>
                  <div className="mt-3">
                    <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                      Extracted skills
                    </p>
                    <SkillList skills={createdJob.required_skills} variant="course" limit={10} />
                  </div>
                </div>
              ) : null}

              <div className="rounded-2xl border border-neutral-200 bg-neutral-100/70 p-5">
                <p className="flex items-center gap-2 text-sm font-semibold text-black">
                  <Sparkles size={15} /> How matching works
                </p>
                <ul className="mt-3 space-y-2 text-xs leading-relaxed text-black">
                  <li>60% semantic similarity between the CV and job embeddings.</li>
                  <li>40% overlap with your required skills.</li>
                  <li>Every candidate gets matched and missing skill lists plus an explanation.</li>
                  <li>Names, gender, age and photos are excluded from scoring.</li>
                </ul>
              </div>

              <div className="card p-5 text-xs leading-relaxed text-neutral-500">
                <p className="text-sm font-semibold text-neutral-800">Fair hiring reminder</p>
                <p className="mt-2">
                  Rankings are decision support, not a hiring decision. Review candidates holistically
                  and keep the final choice with your team.
                </p>
              </div>
            </aside>
          </div>
        ) : null}

        {tab === "candidates" ? (
          <div className="mt-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-neutral-900">Candidates for this job</h2>
                <p className="muted">
                  Candidates who applied or meet the minimum match score to apply, ranked by fit.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <label htmlFor="job_select" className="text-sm font-medium text-neutral-600">
                  Job
                </label>
                <select
                  id="job_select"
                  className="input w-full sm:w-72"
                  value={selectedJobId || ""}
                  onChange={(event) => {
                    const value = Number(event.target.value);
                    setSelectedJobId(value || null);
                    setCandidateFilter("all");
                    loadCandidates(value || null);
                  }}
                >
                  <option value="">Select a job…</option>
                  {jobs.map((job) => (
                    <option key={job.id} value={job.id}>
                      {job.title} ({job.application_count})
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => loadCandidates(selectedJobId)}
                  disabled={!selectedJobId || candidatesLoading}
                >
                  <RefreshCw size={15} className={candidatesLoading ? "animate-spin" : ""} />
                </button>
              </div>
            </div>

            {candidatesError ? <Alert className="mt-4" variant="error">{candidatesError}</Alert> : null}

            {candidates.length ? (
              <div className="mt-5 flex flex-wrap gap-2" role="group" aria-label="Filter candidates">
                {[
                  { key: "all", label: `All (${candidates.length})` },
                  { key: "applied", label: `Applied (${appliedCandidates.length})` },
                  { key: "eligible", label: `Eligible to apply (${eligibleCandidates.length})` },
                ].map((option) => (
                  <button
                    key={option.key}
                    type="button"
                    aria-pressed={candidateFilter === option.key}
                    className={candidateFilter === option.key ? "btn-primary" : "btn-secondary"}
                    onClick={() => setCandidateFilter(option.key)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            ) : null}

            {!jobs.length ? (
              <div className="mt-5">
                <EmptyState
                  icon={BriefcaseBusiness}
                  title="Post a job first"
                  description="Candidate rankings are calculated per job."
                  action={
                    <button type="button" className="btn-primary" onClick={() => setTab("post")}>
                      Post a job
                    </button>
                  }
                />
              </div>
            ) : !selectedJob ? (
              <div className="mt-5">
                <EmptyState
                  icon={Users}
                  title="Choose a job"
                  description="Select one of your jobs above to see ranked candidates."
                />
              </div>
            ) : candidatesLoading ? (
              <div className="mt-5 space-y-4">
                <SkeletonCard rows={4} />
                <SkeletonCard rows={4} />
              </div>
            ) : visibleCandidates.length ? (
              <div className="mt-5 space-y-4">
                {visibleCandidates.map((candidate) => (
                  <article key={candidate.seeker_id} className="card p-5">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="font-semibold text-neutral-900">{candidate.full_name}</h3>
                          {candidate.applied ? (
                            <span className="chip bg-neutral-100 text-black">
                              <CheckCircle2 size={12} className="mr-1" /> Applied
                            </span>
                          ) : (
                            <span className="chip bg-neutral-100 text-neutral-800">
                              Eligible to apply
                            </span>
                          )}
                        </div>
                        <p className="mt-1 text-sm text-neutral-600">
                          {candidate.headline || "Candidate"}
                          {candidate.location ? ` · ${candidate.location}` : ""}
                        </p>
                        <p className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-neutral-500">
                          <a
                            className="inline-flex items-center gap-1 hover:text-neutral-900"
                            href={`mailto:${candidate.email}`}
                          >
                            <Mail size={13} /> {candidate.email}
                          </a>
                          <span className="inline-flex items-center gap-1">
                            <FileText size={13} /> {candidate.cv_filename || "CV"}
                          </span>
                        </p>
                      </div>
                      <ScoreRing score={candidate.score} showLabel />
                    </div>

                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <div>
                        <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-800">
                          Matched ({candidate.matched_skills.length})
                        </p>
                        <SkillList skills={candidate.matched_skills} variant="matched" limit={10} />
                      </div>
                      <div>
                        <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-600">
                          Gaps ({candidate.missing_skills.length})
                        </p>
                        <SkillList skills={candidate.missing_skills} variant="missing" limit={10} empty="No gaps" />
                      </div>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {candidate.skills.slice(0, 14).map((skill) => (
                        <SkillTag key={skill} variant="neutral">
                          {skill}
                        </SkillTag>
                      ))}
                    </div>

                    <div className="mt-4 flex items-start gap-2.5 rounded-xl border border-neutral-200 bg-neutral-100/60 p-3.5 text-sm leading-relaxed text-neutral-950">
                      <Sparkles size={16} className="mt-0.5 shrink-0 text-neutral-600" />
                      <p>{candidate.explanation}</p>
                    </div>

                    <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-neutral-500 sm:max-w-sm">
                      <span>Semantic: {Math.round(candidate.semantic_score)}%</span>
                      <span>Skill overlap: {Math.round(candidate.skill_score)}%</span>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="mt-5">
                <EmptyState
                  icon={Users}
                  title={candidates.length ? "No candidates in this view" : "No candidates to rank yet"}
                  description={
                    candidates.length
                      ? "Choose another filter to see the candidates for this job."
                      : "Candidates appear once they upload a CV. Share the platform or check back shortly."
                  }
                />
              </div>
            )}
          </div>
        ) : null}
      </main>

      <Modal
        open={profileOpen}
        onClose={() => setProfileOpen(false)}
        title="Company profile"
        description="This information appears on your job posts."
      >
        <form onSubmit={saveCompanyProfile} className="space-y-4">
          {profileError ? <Alert variant="error">{profileError}</Alert> : null}
          <div>
            <label htmlFor="company_name" className="label">Company name</label>
            <input
              id="company_name"
              required
              minLength={2}
              maxLength={160}
              className="input"
              value={profileForm.company_name}
              onChange={(event) => setProfileForm({ ...profileForm, company_name: event.target.value })}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="company_website" className="label">Website</label>
              <input
                id="company_website"
                className="input"
                placeholder="https://example.com"
                value={profileForm.website}
                onChange={(event) => setProfileForm({ ...profileForm, website: event.target.value })}
              />
            </div>
            <div>
              <label htmlFor="company_location" className="label">Location</label>
              <input
                id="company_location"
                className="input"
                placeholder="London, UK"
                value={profileForm.location}
                onChange={(event) => setProfileForm({ ...profileForm, location: event.target.value })}
              />
            </div>
          </div>
          <div>
            <label htmlFor="company_description" className="label">About the company</label>
            <textarea
              id="company_description"
              rows={4}
              maxLength={4000}
              className="input resize-y"
              value={profileForm.description}
              onChange={(event) => setProfileForm({ ...profileForm, description: event.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-secondary" onClick={() => setProfileOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={savingProfile}>
              {savingProfile ? <Spinner /> : <Save size={15} />}
              {savingProfile ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        open={passwordOpen}
        onClose={() => {
          if (!changingPassword) setPasswordOpen(false);
        }}
        title="Change password"
        description="Enter your current password and choose a new one."
      >
        <form onSubmit={changePassword} className="space-y-4">
          {passwordError ? <Alert variant="error">{passwordError}</Alert> : null}
          <div>
            <label htmlFor="emp_current_password" className="label">Current password</label>
            <input
              id="emp_current_password"
              type="password"
              required
              autoComplete="current-password"
              className="input"
              value={passwordForm.current}
              onChange={(event) => setPasswordForm({ ...passwordForm, current: event.target.value })}
            />
          </div>
          <div>
            <label htmlFor="emp_new_password" className="label">New password</label>
            <input
              id="emp_new_password"
              type="password"
              required
              minLength={8}
              maxLength={72}
              autoComplete="new-password"
              className="input"
              placeholder="At least 8 characters"
              value={passwordForm.next}
              onChange={(event) => setPasswordForm({ ...passwordForm, next: event.target.value })}
            />
          </div>
          <div>
            <label htmlFor="emp_confirm_new_password" className="label">Confirm new password</label>
            <input
              id="emp_confirm_new_password"
              type="password"
              required
              autoComplete="new-password"
              className="input"
              value={passwordForm.confirm}
              onChange={(event) => setPasswordForm({ ...passwordForm, confirm: event.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-secondary" onClick={() => setPasswordOpen(false)} disabled={changingPassword}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={changingPassword}>
              {changingPassword ? <Spinner /> : <KeyRound size={15} />}
              {changingPassword ? "Updating…" : "Update password"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
