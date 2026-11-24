import { BookOpen, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import Alert from "../components/Alert";
import CourseCard from "../components/CourseCard";
import EmptyState from "../components/EmptyState";
import Footer from "../components/Footer";
import { PageLoader } from "../components/Loader";
import Navbar from "../components/Navbar";
import { api } from "../lib/api";

const LEVELS = ["all", "beginner", "intermediate", "advanced"];

export default function Courses() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState("all");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await api.get("/courses?limit=100");
        if (!cancelled) setCourses(data);
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
  }, []);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return courses.filter((course) => {
      const matchesLevel = level === "all" || course.level === level;
      const haystack = `${course.title} ${course.provider} ${course.description} ${(course.skills || []).join(" ")}`.toLowerCase();
      return matchesLevel && (!needle || haystack.includes(needle));
    });
  }, [courses, query, level]);

  return (
    <div className="flex min-h-screen flex-col bg-neutral-50">
      <Navbar />
      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-12 sm:px-6 lg:px-8">
        <div className="max-w-2xl">
          <span className="inline-flex items-center gap-2 rounded-full border border-neutral-200 bg-white px-3 py-1 text-xs font-semibold text-black">
            <BookOpen size={13} /> Course catalog
          </span>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-neutral-900">
            Learn the skills employers ask for
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-neutral-600">
            These are the courses used by the RAG advisor. Recommendations only reference this
            catalog — TalentMatch does not create courses, sell them, or issue certificates.
          </p>
        </div>

        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-400" />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search skills, providers or topics…"
              className="input pl-10"
              aria-label="Search courses"
            />
          </div>
          <select
            value={level}
            onChange={(event) => setLevel(event.target.value)}
            className="input sm:w-48"
            aria-label="Filter by level"
          >
            {LEVELS.map((item) => (
              <option key={item} value={item}>
                {item === "all" ? "All levels" : item.charAt(0).toUpperCase() + item.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {error ? <Alert className="mt-6" variant="error">{error}</Alert> : null}

        {loading ? (
          <PageLoader label="Loading the course catalog…" />
        ) : filtered.length ? (
          <>
            <p className="mt-6 text-sm text-neutral-500">
              {filtered.length} course{filtered.length === 1 ? "" : "s"}
            </p>
            <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filtered.map((course) => (
                <CourseCard key={course.id} course={course} showRelevance={false} />
              ))}
            </div>
          </>
        ) : (
          <div className="mt-8">
            <EmptyState
              icon={BookOpen}
              title="No courses match your filters"
              description="Try a different skill, provider or level."
            />
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
