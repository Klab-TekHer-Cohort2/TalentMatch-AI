import {
  ArrowRight,
  BadgeCheck,
  BookOpen,
  BrainCircuit,
  BriefcaseBusiness,
  CheckCircle2,
  FileSearch,
  GraduationCap,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";
import Footer from "../components/Footer";
import Navbar from "../components/Navbar";
import ScoreRing from "../components/ScoreRing";
import SkillTag from "../components/SkillTag";

const STEPS = [
  {
    icon: FileSearch,
    title: "Upload your CV",
    text: "A text-based PDF or DOCX up to 5 MB. We validate the file before anything is processed.",
  },
  {
    icon: BrainCircuit,
    title: "AI reads the signal",
    text: "Skills, education, experience and job titles are extracted into a structured profile.",
  },
  {
    icon: Target,
    title: "Hybrid matching",
    text: "60% semantic similarity and 40% required-skill overlap, with an explanation for every role.",
  },
  {
    icon: GraduationCap,
    title: "Close the gaps",
    text: "RAG retrieves real catalog courses for your missing skills and writes a personal plan.",
  },
];

const SEEKER_FEATURES = [
  "Upload or replace your CV and keep a structured skill profile",
  "See ranked jobs with match scores, matched skills and gaps",
  "Apply with an optional note and track every application",
  "Get course advice that only references the real catalog",
];

const EMPLOYER_FEATURES = [
  "Post roles and let skills auto-extract from the description",
  "See only your own jobs; close or delete them at any time",
  "Rank the candidate pool by explainable hybrid scores",
  "Spot skills gaps and share relevant course suggestions",
];

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      <main>
        <section className="relative overflow-hidden bg-neutral-50">
          <div className="pointer-events-none absolute -left-24 top-10 h-72 w-72 rounded-full bg-neutral-200/40 blur-3xl" />
          <div className="pointer-events-none absolute -right-16 top-40 h-80 w-80 rounded-full bg-neutral-200/40 blur-3xl" />
          <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:px-8 lg:py-24">
            <div className="animate-fade-in">
              <span className="inline-flex items-center gap-2 rounded-full border border-neutral-200 bg-white px-3 py-1.5 text-xs font-semibold text-black shadow-sm">
                <Sparkles size={14} /> AI matching + grounded course advice
              </span>
              <h1 className="mt-5 text-4xl font-extrabold leading-tight tracking-tight text-neutral-900 sm:text-5xl">
                Match the role.
                <br />
                <span className="bg-gradient-to-r from-neutral-900 to-neutral-700 bg-clip-text text-transparent">
                  Close the skill gap.
                </span>
              </h1>
              <p className="mt-5 max-w-xl text-lg leading-relaxed text-neutral-600">
                TalentMatch AI analyses CVs and job descriptions, explains every match in plain
                language, and recommends courses from a real catalog to help candidates qualify.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Link to="/register?role=job_seeker" className="btn-primary !px-6 !py-3">
                  Find my next role <ArrowRight size={18} />
                </Link>
                <Link to="/register?role=employer" className="btn-secondary !px-6 !py-3">
                  I&apos;m hiring <Users size={18} />
                </Link>
              </div>
              <p className="mt-4 flex items-center gap-2 text-xs font-medium text-neutral-500">
                <ShieldCheck size={14} className="text-neutral-600" />
                
              </p>
              <dl className="mt-10 grid max-w-md grid-cols-3 gap-4 border-t border-neutral-200 pt-6">
                <div>
                  <dt className="text-2xl font-bold text-neutral-900">60/40</dt>
                  <dd className="text-xs text-neutral-500">Semantic + skill score</dd>
                </div>
                <div>
                  <dt className="text-2xl font-bold text-neutral-900">50</dt>
                  <dd className="text-xs text-neutral-500">Seed catalog courses</dd>
                </div>
                <div>
                  <dt className="text-2xl font-bold text-neutral-900">2</dt>
                  <dd className="text-xs text-neutral-500">Purpose-built dashboards</dd>
                </div>
              </dl>
            </div>

            <div className="relative animate-fade-in lg:justify-self-end">
              <div className="card w-full max-w-md p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wide text-neutral-900">
                      Recommended role
                    </p>
                    <h2 className="mt-1 text-xl font-bold text-neutral-900">Senior Full Stack Engineer</h2>
                    <p className="mt-1 text-sm text-neutral-500">Northstar Labs · Remote (EU)</p>
                  </div>
                  <ScoreRing score={87} showLabel />
                </div>

                <div className="mt-5 rounded-xl border border-neutral-200 bg-neutral-100/60 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-neutral-800">
                    Matched skills
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {["React", "TypeScript", "Node.js", "PostgreSQL"].map((skill) => (
                      <SkillTag key={skill} variant="matched">
                        {skill}
                      </SkillTag>
                    ))}
                  </div>
                </div>

                <div className="mt-3 rounded-xl border border-neutral-100 bg-neutral-100/60 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-neutral-600">Gap</p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    <SkillTag variant="missing">AWS</SkillTag>
                    <SkillTag variant="missing">Docker</SkillTag>
                  </div>
                </div>

                <div className="mt-4 flex items-start gap-2 rounded-xl bg-neutral-900 p-3.5 text-xs leading-relaxed text-neutral-200">
                  <GraduationCap size={16} className="mt-0.5 shrink-0 text-neutral-300" />
                  <p>
                    <span className="font-semibold text-white">Next step:</span> AWS Certified
                    Solutions Architect covers the cloud gap, while Docker & Kubernetes closes the
                    container gap.
                  </p>
                </div>
              </div>
              <div className="absolute -bottom-5 -left-4 hidden rounded-xl border border-neutral-200 bg-white px-3 py-2 text-xs font-medium text-neutral-600 shadow-lg sm:flex sm:items-center sm:gap-2">
                <BadgeCheck size={15} className="text-neutral-600" />
                Explanation for every match
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-widest text-neutral-900">How it works</p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-neutral-900">
              Four steps from CV to a plan
            </h2>
            <p className="mt-3 text-neutral-600">
              Retrieval-augmented generation keeps advice honest: the LLM may only recommend courses
              that were retrieved from the TalentMatch catalog.
            </p>
          </div>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              return (
                <div key={step.title} className="card p-5">
                  <div className="flex items-center justify-between">
                    <span className="grid h-10 w-10 place-items-center rounded-xl bg-neutral-100 text-neutral-900">
                      <Icon size={19} />
                    </span>
                    <span className="text-xs font-bold text-neutral-300">0{index + 1}</span>
                  </div>
                  <h3 className="mt-4 font-semibold text-neutral-900">{step.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-neutral-500">{step.text}</p>
                </div>
              );
            })}
          </div>
        </section>

        <section className="border-y border-neutral-200 bg-neutral-50">
          <div className="mx-auto grid max-w-7xl gap-6 px-4 py-16 sm:px-6 lg:grid-cols-2 lg:px-8">
            <div className="card p-7">
              <div className="flex items-center gap-3">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-neutral-900 text-white">
                  <Search size={20} />
                </span>
                <div>
                  <h2 className="text-xl font-bold text-neutral-900">For job seekers</h2>
                  <p className="text-sm text-neutral-500">Find fit, understand gaps, prepare better.</p>
                </div>
              </div>
              <ul className="mt-6 space-y-3">
                {SEEKER_FEATURES.map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5 text-sm text-neutral-600">
                    <CheckCircle2 size={17} className="mt-0.5 shrink-0 text-neutral-600" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Link to="/register?role=job_seeker" className="btn-primary mt-6 w-full">
                Create a job seeker account
              </Link>
            </div>

            <div className="card p-7">
              <div className="flex items-center gap-3">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-neutral-900 text-white">
                  <BriefcaseBusiness size={20} />
                </span>
                <div>
                  <h2 className="text-xl font-bold text-neutral-900">For employers</h2>
                  <p className="text-sm text-neutral-500">Shortlist with transparent evidence.</p>
                </div>
              </div>
              <ul className="mt-6 space-y-3">
                {EMPLOYER_FEATURES.map((feature) => (
                  <li key={feature} className="flex items-start gap-2.5 text-sm text-neutral-600">
                    <CheckCircle2 size={17} className="mt-0.5 shrink-0 text-neutral-600" />
                    {feature}
                  </li>
                ))}
              </ul>
              <Link to="/register?role=employer" className="btn-secondary mt-6 w-full">
                Create an employer account
              </Link>
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="grid items-center gap-8 rounded-3xl border border-neutral-200 bg-gradient-to-br from-neutral-900 to-neutral-950 p-8 text-white sm:p-10 lg:grid-cols-[1.2fr_0.8fr]">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold">
                <BookOpen size={13} /> RAG course advisor
              </span>
              <h2 className="mt-4 text-3xl font-bold tracking-tight">
                Advice grounded in a real catalog — never invented.
              </h2>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-neutral-300">
                We compare your CV skills with each job&apos;s requirements, retrieve the most
                relevant courses per gap from ChromaDB, then ask Claude to write advice using only
                those retrieved courses. No hallucinated providers, no fake certificates.
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-5 text-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-neutral-300">Scope</p>
              <p className="mt-2 leading-relaxed text-neutral-300">
                TalentMatch supports recruitment only. It does not hire automatically, does not
                guarantee jobs, and does not issue certificates. Employers always make the final
                hiring decision.
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="rounded-full bg-white/10 px-2.5 py-1 text-xs text-neutral-200">Explainable</span>
                <span className="rounded-full bg-white/10 px-2.5 py-1 text-xs text-neutral-200">Fair</span>
                <span className="rounded-full bg-white/10 px-2.5 py-1 text-xs text-neutral-200">Grounded</span>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
