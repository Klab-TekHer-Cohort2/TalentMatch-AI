import {
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  Edit3,
  ExternalLink,
  FileText,
  FileUp,
  GraduationCap,
  KeyRound,
  LayoutDashboard,
  Link2,
  Loader2,
  Mail,
  MapPin,
  Phone,
  RefreshCw,
  Save,
  Send,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import AdvicePanel from "../components/AdvicePanel";
import Alert from "../components/Alert";
import DashboardTabs from "../components/DashboardTabs";
import EmptyState from "../components/EmptyState";
import JobCard from "../components/JobCard";
import { PageLoader, SkeletonCard, Spinner } from "../components/Loader";
import Modal from "../components/Modal";
import Navbar from "../components/Navbar";
import ScoreRing from "../components/ScoreRing";
import { SkillList } from "../components/SkillTag";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { formatDate, formatRelative, initials, jobTypeLabel } from "../lib/utils";

const TABS = [
  { key: "overview", label: "Overview", icon: LayoutDashboard },
  { key: "jobs", label: "Recommended jobs", icon: BriefcaseBusiness },
  { key: "courses", label: "Courses", icon: GraduationCap },
  { key: "applications", label: "Applications", icon: FileText },
];

const ALLOWED_EXTENSIONS = ["pdf", "docx"];
const MAX_BYTES = 5 * 1024 * 1024;
const MIN_APPLY_MATCH_SCORE = Number(import.meta.env.VITE_MIN_APPLY_MATCH_SCORE ?? 50);

function deriveCvKeyPoints(cv) {
  if (!cv) return [];
  const points = [];
  const titles = (cv.job_titles || []).filter(Boolean);
  const skills = (cv.skills || []).filter(Boolean);
  const experience = cv.experience || [];
  const education = cv.education || [];
  if (titles.length) points.push(`Target/experienced roles: ${titles.slice(0, 3).join(", ")}`);
  if (skills.length) points.push(`Core skills: ${skills.slice(0, 6).join(", ")}`);
  if (experience[0]) {
    const e = experience[0];
    const label = [e.title, e.company].filter(Boolean).join(" at ") || e.description || "";
    if (label) points.push(`Experience highlight: ${String(label).replace(/\s+/g, " ").trim().slice(0, 140)}`);
  }
  if (education[0]) {
    const d = education[0];
    const label = d.degree || d.institution || "";
    if (label) points.push(`Education: ${String(label).replace(/\s+/g, " ").trim().slice(0, 140)}`);
  }
  if (cv.summary) points.push(`Profile summary: ${String(cv.summary).replace(/\s+/g, " ").trim().slice(0, 140)}`);
  if (points.length < 3 && skills.length > 6) points.push(`Additional strengths: ${skills.slice(6, 10).join(", ")}`);
  while (points.length < 3) points.push("CV analysed and ready for job matching and skill-gap course recommendations.");
  return [...new Set(points)].slice(0, 5);
}

function formFromProfile(profile, name) {
  return {
    full_name: name || "",
    headline: profile?.headline || "",
    location: profile?.location || "",
    bio: profile?.bio || "",
    phone: profile?.phone || "",
    linkedin: profile?.links?.linkedin || "",
    website: profile?.links?.website || "",
    manual_skills: (profile?.manual_skills || []).join(", "),
  };
}

function withProtocol(value) {
  if (!value) return "";
  return /^https?:\/\//i.test(value) ? value : `https://${value}`;
}

export default function SeekerDashboard() {
  const { user, refreshUser } = useAuth();
  const [tab, setTab] = useState("overview");
  const [profile, setProfile] = useState(null);
  const [cv, setCv] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState(null);

  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(formFromProfile(null, user?.full_name));
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [uploadKeyPoints, setUploadKeyPoints] = useState(null);

  const [jobs, setJobs] = useState([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobsError, setJobsError] = useState("");
  const [jobsLoaded, setJobsLoaded] = useState(false);

  const [applications, setApplications] = useState([]);
  const [appsLoading, setAppsLoading] = useState(false);

  const [applyJob, setApplyJob] = useState(null);
  const [applyNote, setApplyNote] = useState("");
  const [applying, setApplying] = useState(false);
  const [applyError, setApplyError] = useState("");
  const [applyOtpOpen, setApplyOtpOpen] = useState(false);
  const [applyOtpCode, setApplyOtpCode] = useState("");
  const [applyOtpSending, setApplyOtpSending] = useState(false);
  const [applyOtpVerifying, setApplyOtpVerifying] = useState(false);
  const [applyOtpError, setApplyOtpError] = useState("");
  const [applyOtpNotice, setApplyOtpNotice] = useState("");

  const [advice, setAdvice] = useState(null);
  const [adviceLoading, setAdviceLoading] = useState(false);
  const [adviceError, setAdviceError] = useState("");

  const [courseJob, setCourseJob] = useState(null);
  const [jobAdvice, setJobAdvice] = useState(null);
  const [jobAdviceLoading, setJobAdviceLoading] = useState(false);
  const [jobAdviceError, setJobAdviceError] = useState("");

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
        const profileData = await api.get("/seeker/profile");
        if (cancelled) return;
        setProfile(profileData);
        setForm(formFromProfile(profileData, user?.full_name));
        try {
          const cvData = await api.get("/seeker/cv");
          if (!cancelled) setCv(cvData);
        } catch (cvError) {
          if (cvError.status !== 404 && !cancelled) setCv(null);
        }
        try {
          const apps = await api.get("/seeker/applications");
          if (!cancelled) setApplications(apps);
        } catch {
          /* applications are non-blocking */
        }
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

  useEffect(() => {
    if (tab === "jobs" && cv && !jobsLoaded) loadJobs();
    if (tab === "courses" && cv && !advice) loadAdvice();
    if (tab === "applications") loadApplications();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, cv]);

  const appliedJobIds = useMemo(
    () => new Set(applications.map((application) => application.job_id)),
    [applications],
  );

  const cvKeyPoints = useMemo(
    () => (uploadKeyPoints?.length ? uploadKeyPoints : deriveCvKeyPoints(cv)),
    [uploadKeyPoints, cv],
  );

  const applyableJobs = useMemo(
    () => jobs.filter((job) => (Number(job.score) || 0) >= MIN_APPLY_MATCH_SCORE),
    [jobs],
  );

  async function loadJobs() {
    setJobsLoading(true);
    setJobsError("");
    try {
      const data = await api.get("/seeker/jobs/recommended?limit=20");
      setJobs(data);
      setJobsLoaded(true);
    } catch (err) {
      setJobsError(err.message);
    } finally {
      setJobsLoading(false);
    }
  }

  async function loadApplications() {
    setAppsLoading(true);
    try {
      const data = await api.get("/seeker/applications");
      setApplications(data);
    } catch (err) {
      setJobsError(err.message);
    } finally {
      setAppsLoading(false);
    }
  }

  async function loadAdvice() {
    setAdviceLoading(true);
    setAdviceError("");
    try {
      const data = await api.get("/seeker/courses/recommended");
      setAdvice(data);
    } catch (err) {
      setAdviceError(err.message);
    } finally {
      setAdviceLoading(false);
    }
  }

  async function handleFile(file) {
    if (!file) return;
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setUploadError("Only PDF and DOCX files are supported.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setUploadError("File must be 5 MB or smaller.");
      return;
    }
    setUploadError("");
    setUploading(true);
    try {
      const data = await api.upload("/seeker/cv", file);
      setCv(data.cv);
      setUploadKeyPoints(data.key_points || null);
      setProfile((previous) => (previous ? { ...previous, skills: data.effective_skills } : previous));
      setJobs([]);
      setJobsLoaded(false);
      setAdvice(null);
      setNotice({ variant: "success", message: data.message });
      loadJobs();
    } catch (err) {
      setUploadError(err.message);
    } finally {
      setUploading(false);
      setDragging(false);
    }
  }

  async function saveProfile(event) {
    event.preventDefault();
    setSaving(true);
    setSaveError("");
    try {
      const links = {};
      if (form.linkedin.trim()) links.linkedin = form.linkedin.trim();
      if (form.website.trim()) links.website = form.website.trim();
      const payload = {
        full_name: form.full_name.trim(),
        headline: form.headline.trim() || null,
        location: form.location.trim() || null,
        bio: form.bio.trim() || null,
        phone: form.phone.trim() || null,
        links,
        manual_skills: form.manual_skills
          .split(",")
          .map((skill) => skill.trim())
          .filter(Boolean),
      };
      const updated = await api.put("/seeker/profile", payload);
      setProfile(updated);
      setForm(formFromProfile(updated, form.full_name));
      setEditing(false);
      await refreshUser();
      setNotice({ variant: "success", message: "Profile updated." });
    } catch (err) {
      setSaveError(err.message);
    } finally {
      setSaving(false);
    }
  }

  async function sendApplyOtp() {
    setApplyOtpError("");
    setApplyOtpSending(true);
    try {
      const result = await api.post("/auth/request-email-otp", { email: user.email });
      setApplyOtpNotice(result.message);
    } catch (err) {
      if (err.status === 429) {
        setApplyOtpNotice("A code was already sent. Check your inbox or wait before requesting another.");
      } else {
        setApplyOtpError(err.message);
      }
    } finally {
      setApplyOtpSending(false);
    }
  }

  async function verifyApplyOtp(event) {
    event.preventDefault();
    setApplyOtpError("");
    setApplyOtpVerifying(true);
    try {
      await api.post("/auth/verify-email-otp", { email: user.email, code: applyOtpCode.trim() });
      await refreshUser();
      setApplyOtpOpen(false);
      setApplyOtpCode("");
      await sendApplication();
    } catch (err) {
      setApplyOtpError(err.message);
    } finally {
      setApplyOtpVerifying(false);
    }
  }

  async function sendApplication() {
    if (!applyJob) return;
    setApplying(true);
    setApplyError("");
    try {
      const application = await api.post(`/seeker/jobs/${applyJob.id}/apply`, {
        cover_note: applyNote.trim() || null,
      });
      setApplications((previous) => [application, ...previous]);
      setApplyJob(null);
      setApplyNote("");
      setNotice({
        variant: "success",
        message: `Application sent to ${applyJob.employer?.company_name || "the employer"}.`,
      });
    } catch (err) {
      if (err.code === "EMAIL_NOT_VERIFIED") {
        setApplyError("");
        setApplyOtpCode("");
        setApplyOtpNotice("");
        setApplyOtpOpen(true);
        await sendApplyOtp();
      } else {
        setApplyError(err.message);
      }
    } finally {
      setApplying(false);
    }
  }

  function submitApplication(event) {
    event.preventDefault();
    return sendApplication();
  }

  async function openJobCourses(job) {
    setCourseJob(job);
    setJobAdvice(null);
    setJobAdviceError("");
    setJobAdviceLoading(true);
    try {
      const data = await api.get(`/seeker/courses/recommended?job_id=${job.id}`);
      setJobAdvice(data);
    } catch (err) {
      setJobAdviceError(err.message);
    } finally {
      setJobAdviceLoading(false);
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

  const tabs = TABS.map((item) => ({
    ...item,
    count:
      item.key === "jobs" && jobsLoaded
        ? jobs.length
        : item.key === "applications"
          ? applications.length
          : undefined,
  }));

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-50">
        <Navbar />
        <PageLoader label="Loading your workspace…" />
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
              Job seeker workspace
            </p>
            <h1 className="mt-1 text-2xl font-bold tracking-tight text-neutral-900 sm:text-3xl">
              Welcome back, {user?.full_name?.split(" ")[0] || "there"}
            </h1>
            <p className="mt-1 text-sm text-neutral-500">
              Your CV, matches, applications and course plan in one place.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden rounded-xl border border-neutral-200 bg-white px-3 py-2 text-xs font-medium text-neutral-500 shadow-sm sm:block">
              {profile?.skills?.length || 0} skills detected
            </span>
            <button type="button" onClick={() => setTab("jobs")} className="btn-primary">
              <Sparkles size={16} /> View matches
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
        </div>

        {tab === "overview" ? (
          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <section className="card p-6">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex items-start gap-4">
                    <span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-neutral-900 to-neutral-700 text-lg font-bold text-white">
                      {initials(user?.full_name)}
                    </span>
                    <div>
                      <h2 className="text-xl font-bold text-neutral-900">{user?.full_name}</h2>
                      <p className="text-sm text-neutral-600">
                        {profile?.headline || "Add a headline to introduce yourself"}
                      </p>
                      <p className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-neutral-500">
                        <span className="inline-flex items-center gap-1">
                          <Mail size={13} /> {user?.email}
                        </span>
                        {profile?.location ? (
                          <span className="inline-flex items-center gap-1">
                            <MapPin size={13} /> {profile.location}
                          </span>
                        ) : null}
                        {profile?.phone ? (
                          <span className="inline-flex items-center gap-1">
                            <Phone size={13} /> {profile.phone}
                          </span>
                        ) : null}
                      </p>
                    </div>
                  </div>
                  {!editing ? (
                    <div className="flex flex-wrap gap-2">
                      <button type="button" onClick={() => setEditing(true)} className="btn-secondary">
                        <Edit3 size={15} /> Edit profile
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
                        <KeyRound size={15} /> Change password
                      </button>
                    </div>
                  ) : null}
                </div>

                {!editing ? (
                  <div className="mt-5 space-y-4">
                    {profile?.bio ? <p className="text-sm leading-relaxed text-neutral-600">{profile.bio}</p> : null}
                    <div>
                      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">
                        Skills
                      </p>
                      <SkillList skills={profile?.skills || []} variant="neutral" empty="Upload a CV to extract skills" />
                    </div>
                    {profile?.links && Object.keys(profile.links).length ? (
                      <div className="flex flex-wrap gap-3 text-sm">
                        {Object.entries(profile.links).map(([key, value]) =>
                          value ? (
                            <a
                              key={key}
                              href={withProtocol(value)}
                              target="_blank"
                              rel="noreferrer noopener"
                              className="inline-flex items-center gap-1.5 font-medium text-neutral-900 hover:text-black"
                            >
                              <Link2 size={14} className="capitalize" /> {key}
                              <ExternalLink size={12} />
                            </a>
                          ) : null,
                        )}
                      </div>
                    ) : null}
                  </div>
                ) : (
                  <form onSubmit={saveProfile} className="mt-5 space-y-4 border-t border-neutral-100 pt-5">
                    {saveError ? <Alert variant="error">{saveError}</Alert> : null}
                    <div className="grid gap-4 sm:grid-cols-2">
                      <div>
                        <label htmlFor="full_name" className="label">Full name</label>
                        <input
                          id="full_name"
                          className="input"
                          value={form.full_name}
                          onChange={(event) => setForm({ ...form, full_name: event.target.value })}
                          required
                        />
                      </div>
                      <div>
                        <label htmlFor="headline" className="label">Headline</label>
                        <input
                          id="headline"
                          className="input"
                          placeholder="Senior Full Stack Engineer"
                          value={form.headline}
                          onChange={(event) => setForm({ ...form, headline: event.target.value })}
                        />
                      </div>
                      <div>
                        <label htmlFor="location" className="label">Location</label>
                        <input
                          id="location"
                          className="input"
                          placeholder="Lisbon, Portugal"
                          value={form.location}
                          onChange={(event) => setForm({ ...form, location: event.target.value })}
                        />
                      </div>
                      <div>
                        <label htmlFor="phone" className="label">Phone</label>
                        <input
                          id="phone"
                          className="input"
                          placeholder="+351 …"
                          value={form.phone}
                          onChange={(event) => setForm({ ...form, phone: event.target.value })}
                        />
                      </div>
                      <div>
                        <label htmlFor="linkedin" className="label">LinkedIn</label>
                        <input
                          id="linkedin"
                          className="input"
                          placeholder="linkedin.com/in/you"
                          value={form.linkedin}
                          onChange={(event) => setForm({ ...form, linkedin: event.target.value })}
                        />
                      </div>
                      <div>
                        <label htmlFor="website" className="label">Website</label>
                        <input
                          id="website"
                          className="input"
                          placeholder="yourportfolio.com"
                          value={form.website}
                          onChange={(event) => setForm({ ...form, website: event.target.value })}
                        />
                      </div>
                    </div>
                    <div>
                      <label htmlFor="bio" className="label">Bio</label>
                      <textarea
                        id="bio"
                        rows={3}
                        className="input resize-y"
                        placeholder="A short professional summary"
                        value={form.bio}
                        onChange={(event) => setForm({ ...form, bio: event.target.value })}
                      />
                    </div>
                    <div>
                      <label htmlFor="manual_skills" className="label">
                        Additional skills <span className="font-normal text-neutral-400">(comma separated)</span>
                      </label>
                      <input
                        id="manual_skills"
                        className="input"
                        placeholder="Communication, Leadership"
                        value={form.manual_skills}
                        onChange={(event) => setForm({ ...form, manual_skills: event.target.value })}
                      />
                    </div>
                    <div className="flex justify-end gap-2">
                      <button type="button" className="btn-secondary" onClick={() => { setEditing(false); setSaveError(""); }}>
                        Cancel
                      </button>
                      <button type="submit" className="btn-primary" disabled={saving}>
                        {saving ? <Spinner /> : <Save size={15} />}
                        {saving ? "Saving…" : "Save profile"}
                      </button>
                    </div>
                  </form>
                )}
              </section>

              <section className="card p-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className="section-title">CV and analysis</h2>
                    <p className="muted mt-1">
                      PDF or DOCX, maximum 5 MB. Scanned image-only files are not supported.
                    </p>
                  </div>
                  {cv ? (
                    <label className="btn-secondary cursor-pointer">
                      <FileUp size={15} /> Replace CV
                      <input
                        type="file"
                        accept=".pdf,.docx"
                        className="hidden"
                        disabled={uploading}
                        onChange={(event) => handleFile(event.target.files?.[0])}
                      />
                    </label>
                  ) : null}
                </div>

                {uploadError ? <Alert className="mt-4" variant="error" onClose={() => setUploadError("")}>{uploadError}</Alert> : null}

                <div
                  className={`mt-5 rounded-2xl border-2 border-dashed p-6 text-center transition ${
                    dragging ? "border-neutral-400 bg-neutral-100" : "border-neutral-300 bg-neutral-50/70"
                  }`}
                  onDragOver={(event) => {
                    event.preventDefault();
                    setDragging(true);
                  }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={(event) => {
                    event.preventDefault();
                    setDragging(false);
                    handleFile(event.dataTransfer.files?.[0]);
                  }}
                >
                  <span className="mx-auto grid h-11 w-11 place-items-center rounded-xl bg-white text-neutral-900 shadow-sm">
                    {uploading ? <Loader2 size={20} className="animate-spin" /> : <UploadCloud size={20} />}
                  </span>
                  <p className="mt-3 text-sm font-semibold text-neutral-800">
                    {uploading ? "Analysing your CV…" : cv ? "Drop a new CV to replace the current one" : "Drop your CV here"}
                  </p>
                  <p className="mt-1 text-xs text-neutral-500">PDF or DOCX · up to 5 MB</p>
                  <label className="btn-primary mt-4 cursor-pointer">
                    {uploading ? <Spinner /> : <FileUp size={15} />}
                    {uploading ? "Processing…" : cv ? "Upload replacement" : "Choose file"}
                    <input
                      type="file"
                      accept=".pdf,.docx"
                      className="hidden"
                      disabled={uploading}
                      onChange={(event) => handleFile(event.target.files?.[0])}
                    />
                  </label>
                  <p className="mt-3 text-[11px] text-neutral-400">
                    Parsing uses pdfplumber / python-docx. Matching never uses name, gender, age or photo.
                  </p>
                </div>

                {cv ? (
                  <div className="mt-6 space-y-5">
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-neutral-200 bg-white p-4">
                      <div className="flex items-center gap-3">
                        <span className="grid h-10 w-10 place-items-center rounded-lg bg-neutral-100 text-neutral-900">
                          <FileText size={18} />
                        </span>
                        <div>
                          <p className="text-sm font-semibold text-neutral-800">{cv.filename}</p>
                          <p className="text-xs text-neutral-500">
                            Uploaded {formatRelative(cv.uploaded_at)} · {(cv.size_bytes / 1024).toFixed(0)} KB
                          </p>
                        </div>
                      </div>
                      <span className="chip bg-neutral-100 text-neutral-800">
                        <CheckCircle2 size={13} className="mr-1" /> Active CV
                      </span>
                    </div>

                    {cvKeyPoints.length ? (
                      <div className="rounded-xl border border-neutral-200 bg-neutral-100/60 p-4">
                        <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-black">
                          <Sparkles size={14} /> Key points from your CV
                        </p>
                        <ul className="list-disc space-y-1 pl-5 text-sm text-neutral-700">
                          {cvKeyPoints.map((point, index) => (
                            <li key={index}>{point}</li>
                          ))}
                        </ul>
                      </div>
                    ) : null}

                    {cv.summary ? (
                      <div>
                        <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-500">Summary</p>
                        <p className="text-sm leading-relaxed text-neutral-600">{cv.summary}</p>
                      </div>
                    ) : null}

                    <div className="grid gap-5 sm:grid-cols-2">
                      <div>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">Extracted skills</p>
                        <SkillList skills={cv.skills} variant="course" />
                      </div>
                      <div>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">Job titles</p>
                        <SkillList skills={cv.job_titles} variant="neutral" empty="No titles detected" />
                      </div>
                    </div>

                    <div className="grid gap-5 sm:grid-cols-2">
                      <div>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">Education</p>
                        {cv.education?.length ? (
                          <ul className="space-y-2 text-sm text-neutral-600">
                            {cv.education.map((item, index) => (
                              <li key={index} className="rounded-lg border border-neutral-100 bg-neutral-50 px-3 py-2">
                                <span className="font-medium text-neutral-800">{item.degree || "Degree"}</span>
                                {item.institution ? <span className="block text-xs">{item.institution}</span> : null}
                                {item.year ? <span className="block text-xs text-neutral-400">{item.year}</span> : null}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-xs text-neutral-400">No education entries detected.</p>
                        )}
                      </div>
                      <div>
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-neutral-500">Experience</p>
                        {cv.experience?.length ? (
                          <ul className="space-y-2 text-sm text-neutral-600">
                            {cv.experience.slice(0, 4).map((item, index) => (
                              <li key={index} className="rounded-lg border border-neutral-100 bg-neutral-50 px-3 py-2">
                                <span className="font-medium text-neutral-800">
                                  {item.title || "Experience"}
                                  {item.company ? ` · ${item.company}` : ""}
                                </span>
                                {item.start || item.end ? (
                                  <span className="block text-xs text-neutral-400">
                                    {[item.start, item.end].filter(Boolean).join(" – ")}
                                  </span>
                                ) : null}
                                {item.description ? <span className="mt-1 block text-xs">{item.description}</span> : null}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-xs text-neutral-400">No experience entries detected.</p>
                        )}
                      </div>
                    </div>
                  </div>
                ) : null}
              </section>
            </div>

            <aside className="space-y-6">
              <section className="card p-6">
                <h2 className="section-title">Your snapshot</h2>
                <dl className="mt-4 space-y-3 text-sm">
                  <div className="flex items-center justify-between">
                    <dt className="text-neutral-500">CV status</dt>
                    <dd className={`font-semibold ${cv ? "text-black" : "text-neutral-500"}`}>
                      {cv ? "Uploaded" : "Missing"}
                    </dd>
                  </div>
                  <div className="flex items-center justify-between">
                    <dt className="text-neutral-500">Detected skills</dt>
                    <dd className="font-semibold text-neutral-800">{profile?.skills?.length || 0}</dd>
                  </div>
                  <div className="flex items-center justify-between">
                    <dt className="text-neutral-500">Job titles</dt>
                    <dd className="font-semibold text-neutral-800">{cv?.job_titles?.length || 0}</dd>
                  </div>
                  <div className="flex items-center justify-between">
                    <dt className="text-neutral-500">Applications</dt>
                    <dd className="font-semibold text-neutral-800">{applications.length}</dd>
                  </div>
                </dl>
              </section>

              <section className="card p-6">
                <h2 className="section-title">Recommended next steps</h2>
                <ol className="mt-4 space-y-3 text-sm">
                  {(cv
                    ? [
                        "Open Recommended jobs and review your top three explanations.",
                        "Apply to a strong match with a short, tailored note.",
                        "Use Courses to close the missing skills for a target role.",
                      ]
                    : [
                        "Upload a text-based PDF or DOCX CV to unlock matching.",
                        "Check the extracted skills and add anything missing to your profile.",
                        "Return to Recommended jobs once the analysis completes.",
                      ]
                  ).map((tip, index) => (
                    <li key={tip} className="flex gap-3">
                      <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-neutral-100 text-xs font-semibold text-neutral-900">
                        {index + 1}
                      </span>
                      <span className="text-neutral-600">{tip}</span>
                    </li>
                  ))}
                </ol>
                <div className="mt-5 grid gap-2">
                  <button type="button" onClick={() => setTab("jobs")} className="btn-primary w-full" disabled={!cv}>
                    <BriefcaseBusiness size={16} /> Browse matches
                  </button>
                  <button type="button" onClick={() => setTab("courses")} className="btn-secondary w-full" disabled={!cv}>
                    <GraduationCap size={16} /> Course plan
                  </button>
                </div>
              </section>

              <section className="rounded-2xl border border-neutral-200 bg-neutral-100/70 p-5">
                <p className="flex items-center gap-2 text-sm font-semibold text-black">
                  <Sparkles size={15} /> Fairness reminder
                </p>
                <p className="mt-2 text-xs leading-relaxed text-black">
                  Matching uses skills, experience language and semantic similarity only. Name, gender,
                  age and photo are never part of the score.
                </p>
              </section>
            </aside>
          </div>
        ) : null}

        {tab === "jobs" ? (
          <div className="mt-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-neutral-900">Recommended jobs</h2>
                <p className="muted">Ranked by 60% semantic similarity and 40% skill overlap.</p>
              </div>
              <button type="button" onClick={loadJobs} disabled={jobsLoading || !cv} className="btn-secondary">
                <RefreshCw size={15} className={jobsLoading ? "animate-spin" : ""} /> Refresh
              </button>
            </div>

            {jobsError ? <Alert className="mt-4" variant="error">{jobsError}</Alert> : null}

            {!cv ? (
              <div className="mt-5">
                <EmptyState
                  icon={FileUp}
                  title="Upload a CV to see matches"
                  description="Recommendations need a structured skill profile and embedding."
                  action={<button type="button" className="btn-primary" onClick={() => setTab("overview")}>Go to CV upload</button>}
                />
              </div>
            ) : jobsLoading ? (
              <div className="mt-5 space-y-4">
                <SkeletonCard rows={5} />
                <SkeletonCard rows={5} />
              </div>
            ) : jobs.length ? (
              <div className="mt-5 space-y-6">
                <div className="rounded-xl border border-neutral-200 bg-neutral-100/70 p-4 text-sm text-neutral-950">
                  <p className="font-semibold">Jobs you can apply for now</p>
                  <p className="mt-1 text-neutral-900">
                    {applyableJobs.length} of {jobs.length} recommended jobs meet the {MIN_APPLY_MATCH_SCORE}% match threshold. You can apply directly to those roles below.
                  </p>
                </div>

                {applyableJobs.length ? (
                  <section className="space-y-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wide text-neutral-800">Eligible to apply ({applyableJobs.length})</h3>
                    {applyableJobs.map((job) => (
                      <JobCard
                        key={job.id}
                        job={job}
                        applied={appliedJobIds.has(job.id)}
                        applying={applying && applyJob?.id === job.id}
                        onApply={(selected) => {
                          setApplyJob(selected);
                          setApplyNote("");
                          setApplyError("");
                        }}
                        onCourses={openJobCourses}
                      />
                    ))}
                  </section>
                ) : (
                  <Alert variant="warning">
                    No roles currently meet the {MIN_APPLY_MATCH_SCORE}% threshold. Use “Courses to qualify” on a target job or open the Courses tab to close skill gaps.
                  </Alert>
                )}

                {jobs.length > applyableJobs.length ? (
                  <section className="space-y-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wide text-neutral-600">Build skills to qualify ({jobs.length - applyableJobs.length})</h3>
                    {jobs
                      .filter((job) => (Number(job.score) || 0) < MIN_APPLY_MATCH_SCORE)
                      .map((job) => (
                        <JobCard
                          key={job.id}
                          job={job}
                          applied={appliedJobIds.has(job.id)}
                          applying={applying && applyJob?.id === job.id}
                          onApply={(selected) => {
                            setApplyJob(selected);
                            setApplyNote("");
                            setApplyError("");
                          }}
                          onCourses={openJobCourses}
                        />
                      ))}
                  </section>
                ) : null}
              </div>
            ) : (
              <div className="mt-5">
                <EmptyState
                  icon={BriefcaseBusiness}
                  title="No open jobs right now"
                  description="New roles appear here as employers post them. Refresh in a moment."
                />
              </div>
            )}
          </div>
        ) : null}

        {tab === "courses" ? (
          <div className="mt-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-neutral-900">Personalised course plan</h2>
                <p className="muted">Built from gaps across your top matches, using only catalog courses.</p>
              </div>
              <button type="button" onClick={loadAdvice} disabled={adviceLoading || !cv} className="btn-secondary">
                <RefreshCw size={15} className={adviceLoading ? "animate-spin" : ""} /> Refresh
              </button>
            </div>

            {adviceError ? <Alert className="mt-4" variant="error">{adviceError}</Alert> : null}

            {!cv ? (
              <div className="mt-5">
                <EmptyState
                  icon={GraduationCap}
                  title="A CV unlocks the course advisor"
                  description="We need your extracted skills to identify gaps and retrieve courses."
                  action={<button type="button" className="btn-primary" onClick={() => setTab("overview")}>Upload CV</button>}
                />
              </div>
            ) : adviceLoading ? (
              <div className="mt-5">
                <SkeletonCard rows={4} />
              </div>
            ) : advice ? (
              <div className="mt-5">
                <AdvicePanel
                  advice={advice.advice}
                  gaps={advice.skill_gaps}
                  courses={advice.courses}
                  generatedBy={advice.generated_by}
                  jobTitle={advice.job_title}
                />
              </div>
            ) : null}
          </div>
        ) : null}

        {tab === "applications" ? (
          <div className="mt-6">
            <h2 className="text-lg font-semibold text-neutral-900">Your applications</h2>
            <p className="muted">Employers make the final hiring decision.</p>

            {appsLoading ? (
              <div className="mt-5">
                <SkeletonCard rows={4} />
              </div>
            ) : applications.length ? (
              <div className="mt-5 space-y-4">
                {applications.map((application) => (
                  <article key={application.id} className="card p-5">
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <h3 className="font-semibold text-neutral-900">{application.job?.title || "Job"}</h3>
                        <p className="mt-1 text-sm text-neutral-500">
                          {application.job?.employer?.company_name || "Company"}
                          {application.job?.location ? ` · ${application.job.location}` : ""}
                          {application.job?.job_type ? ` · ${jobTypeLabel(application.job.job_type)}` : ""}
                        </p>
                        <p className="mt-1 flex items-center gap-1.5 text-xs text-neutral-400">
                          <CalendarDays size={13} /> Applied {formatDate(application.created_at)}
                          <span className="chip ml-2 bg-neutral-100 text-neutral-600 capitalize">{application.status}</span>
                        </p>
                      </div>
                      <ScoreRing score={application.match_score} showLabel />
                    </div>

                    <div className="mt-4 grid gap-3 sm:grid-cols-2">
                      <div>
                        <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-800">Matched</p>
                        <SkillList skills={application.matched_skills} variant="matched" limit={8} />
                      </div>
                      <div>
                        <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-neutral-600">Gaps</p>
                        <SkillList skills={application.missing_skills} variant="missing" limit={8} empty="No gaps" />
                      </div>
                    </div>

                    {application.cover_note ? (
                      <p className="mt-4 rounded-xl bg-neutral-50 p-3 text-sm italic text-neutral-600">
                        “{application.cover_note}”
                      </p>
                    ) : null}

                    {application.job ? (
                      <button
                        type="button"
                        className="btn-secondary mt-4"
                        onClick={() => openJobCourses(application.job)}
                      >
                        <GraduationCap size={15} /> Courses for this role
                      </button>
                    ) : null}
                  </article>
                ))}
              </div>
            ) : (
              <div className="mt-5">
                <EmptyState
                  icon={Send}
                  title="No applications yet"
                  description="When you apply to a match, it will appear here with its score snapshot."
                  action={<button type="button" className="btn-primary" onClick={() => setTab("jobs")}>Browse matches</button>}
                />
              </div>
            )}
          </div>
        ) : null}
      </main>

      <Modal
        open={Boolean(applyJob) && !applyOtpOpen}
        onClose={() => {
          if (!applying) setApplyJob(null);
        }}
        title={applyJob ? `Apply to ${applyJob.title}` : "Apply"}
        description={applyJob?.employer?.company_name}
      >
        <form onSubmit={submitApplication} className="space-y-4">
          {applyError ? <Alert variant="error">{applyError}</Alert> : null}
          <div className="rounded-xl border border-neutral-100 bg-neutral-50 p-3 text-sm">
            <p className="font-medium text-neutral-700">Match snapshot</p>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <ScoreRing score={applyJob?.score} size={46} />
              <div className="text-xs text-neutral-500">
                <p>{applyJob?.matched_skills?.length || 0} matched skills</p>
                <p>{applyJob?.missing_skills?.length || 0} skill gaps</p>
              </div>
            </div>
          </div>
          <div>
            <label htmlFor="cover_note" className="label">
              Note to the employer <span className="font-normal text-neutral-400">(optional)</span>
            </label>
            <textarea
              id="cover_note"
              rows={4}
              maxLength={2000}
              className="input resize-y"
              placeholder="Why are you a good fit for this role?"
              value={applyNote}
              onChange={(event) => setApplyNote(event.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-secondary" onClick={() => setApplyJob(null)} disabled={applying}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={applying}>
              {applying ? <Spinner /> : <Send size={15} />}
              {applying ? "Sending…" : "Send application"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        open={applyOtpOpen}
        onClose={() => {
          if (!applyOtpVerifying && !applying) setApplyOtpOpen(false);
        }}
        title="Verify your email"
        description="A 6-digit code was sent to your email address."
      >
        <form onSubmit={verifyApplyOtp} className="space-y-4">
          {applyOtpNotice ? <Alert variant="info">{applyOtpNotice}</Alert> : null}
          {applyOtpError ? <Alert variant="error">{applyOtpError}</Alert> : null}
          <div>
            <label htmlFor="apply_otp" className="label">
              Verification code
            </label>
            <input
              id="apply_otp"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              className="input text-center text-lg tracking-[0.4em]"
              placeholder="000000"
              value={applyOtpCode}
              onChange={(event) => setApplyOtpCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
            />
          </div>
          <p className="text-xs text-neutral-500">
            You can also open the verification link we emailed you. Come back and send the application again afterwards.
          </p>
          <div className="flex flex-wrap justify-end gap-2">
            <button type="button" className="btn-secondary" onClick={sendApplyOtp} disabled={applyOtpSending || applyOtpVerifying}>
              {applyOtpSending ? "Sending…" : "Resend code"}
            </button>
            <button type="submit" className="btn-primary" disabled={applyOtpVerifying || applying}>
              {applyOtpVerifying || applying ? <Spinner /> : <Mail size={15} />}
              {applyOtpVerifying || applying ? "Verifying…" : "Verify and apply"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal
        open={Boolean(courseJob)}
        onClose={() => setCourseJob(null)}
        title="Courses to qualify"
        description={courseJob ? `${courseJob.title} · ${courseJob.employer?.company_name || ""}` : ""}
        wide
      >
        {jobAdviceError ? <Alert variant="error">{jobAdviceError}</Alert> : null}
        {jobAdviceLoading ? (
          <div className="flex flex-col items-center justify-center gap-3 py-12 text-sm text-neutral-500">
            <Spinner size={26} className="text-neutral-900" />
            Retrieving courses for your gaps…
          </div>
        ) : jobAdvice ? (
          <AdvicePanel
            advice={jobAdvice.advice}
            gaps={jobAdvice.skill_gaps}
            courses={jobAdvice.courses}
            generatedBy={jobAdvice.generated_by}
            jobTitle={jobAdvice.job_title}
          />
        ) : null}
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
            <label htmlFor="current_password" className="label">Current password</label>
            <input
              id="current_password"
              type="password"
              required
              autoComplete="current-password"
              className="input"
              value={passwordForm.current}
              onChange={(event) => setPasswordForm({ ...passwordForm, current: event.target.value })}
            />
          </div>
          <div>
            <label htmlFor="new_password" className="label">New password</label>
            <input
              id="new_password"
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
            <label htmlFor="confirm_new_password" className="label">Confirm new password</label>
            <input
              id="confirm_new_password"
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
