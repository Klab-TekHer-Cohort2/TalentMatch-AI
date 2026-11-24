import json
import logging
import re
from typing import Any

from ..config import settings
from .skills import extract_skills, merge_skills, normalize_skills

logger = logging.getLogger(__name__)

TITLE_HINTS = [
    "software engineer",
    "senior software engineer",
    "frontend developer",
    "front-end developer",
    "backend developer",
    "back-end developer",
    "full stack developer",
    "full-stack developer",
    "data scientist",
    "data analyst",
    "data engineer",
    "machine learning engineer",
    "ai engineer",
    "devops engineer",
    "cloud engineer",
    "product manager",
    "project manager",
    "ux designer",
    "ui designer",
    "product designer",
    "business analyst",
    "marketing manager",
    "digital marketing specialist",
    "sales manager",
    "accountant",
    "financial analyst",
    "hr specialist",
    "recruiter",
    "customer success manager",
    "qa engineer",
    "test engineer",
    "cybersecurity analyst",
    "security engineer",
    "mobile developer",
    "ios developer",
    "android developer",
]


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _parse_json(text: str | None) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = _strip_code_fences(text)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _string_list(value: Any, limit: int = 40) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            items.append(item.strip()[:160])
        elif isinstance(item, dict):
            label = item.get("name") or item.get("title") or item.get("degree")
            if isinstance(label, str) and label.strip():
                items.append(label.strip()[:160])
    return list(dict.fromkeys(items))[:limit]


def _dict_list(value: Any, keys: tuple[str, ...], limit: int = 12) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append({keys[0]: "", keys[1]: "", keys[2]: item.strip()[:500]})
            continue
        if not isinstance(item, dict):
            continue
        cleaned: dict[str, Any] = {}
        for key in keys:
            raw = item.get(key)
            if isinstance(raw, (str, int, float)):
                cleaned[key] = str(raw)[:500]
        if cleaned:
            result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def _heuristic_titles(text: str) -> list[str]:
    lowered = text.lower()
    found = [title for title in TITLE_HINTS if title in lowered]
    if not found:
        for line in text.splitlines()[:25]:
            line = line.strip()
            if 4 <= len(line) <= 70 and any(
                word in line.lower()
                for word in ("engineer", "developer", "manager", "analyst", "designer", "specialist")
            ):
                found.append(line)
    return list(dict.fromkeys(found))[:8]


def _heuristic_experience(text: str) -> list[dict[str, Any]]:
    lines = [line.strip(" \t•-*") for line in text.splitlines() if line.strip()]
    items: list[dict[str, Any]] = []
    for line in lines:
        if re.search(r"(19|20)\d{2}\s*[-–—to]+\s*((19|20)\d{2}|present|current)", line, re.IGNORECASE):
            if 8 <= len(line) <= 220:
                items.append({"title": "", "company": "", "start": "", "end": "", "description": line})
        if len(items) >= 8:
            break
    return items


def _heuristic_education(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"(bachelor|master|ph\.?d|b\.?sc|m\.?sc|mba|degree|university|college|institute|diploma)",
        re.IGNORECASE,
    )
    items: list[dict[str, Any]] = []
    for line in text.splitlines():
        cleaned = line.strip(" \t•-*")
        if cleaned and pattern.search(cleaned) and len(cleaned) <= 220:
            items.append({"degree": cleaned, "institution": "", "year": ""})
        if len(items) >= 6:
            break
    return items


def derive_key_points(analysis: dict[str, Any], limit: int = 5) -> list[str]:
    summary = str(analysis.get("summary") or "").strip()
    skills = [s for s in (analysis.get("skills") or []) if isinstance(s, str) and s.strip()]
    titles = [t for t in (analysis.get("job_titles") or []) if isinstance(t, str) and t.strip()]
    experience = analysis.get("experience") or []
    education = analysis.get("education") or []
    points: list[str] = []
    if titles:
        points.append(f"Target/experienced roles: {', '.join(titles[:3])}")
    if skills:
        points.append(f"Core skills: {', '.join(skills[:6])}")
    if experience and isinstance(experience[0], dict):
        exp = experience[0]
        role = str(exp.get("title") or "").strip()
        company = str(exp.get("company") or "").strip()
        desc = str(exp.get("description") or "").strip()
        label = role if role else desc[:80]
        if company and role:
            label = f"{role} at {company}"
        elif company and label:
            label = f"{label} ({company})"
        if label:
            compact_label = re.sub(r"\s+", " ", label).strip()[:140]
            points.append(f"Experience highlight: {compact_label}")
    if education and isinstance(education[0], dict):
        edu = education[0]
        degree = str(edu.get("degree") or edu.get("institution") or "").strip()
        if degree:
            compact_degree = re.sub(r"\s+", " ", degree).strip()[:140]
            points.append(f"Education: {compact_degree}")
    if summary:
        compact = re.sub(r"\s+", " ", summary).strip()
        if compact and len(points) < limit:
            points.append(f"Profile summary: {compact[:140]}")
    if len(points) < 3 and len(skills) > 6:
        points.append(f"Additional strengths: {', '.join(skills[6:10])}")
    while len(points) < 3:
        points.append("CV analysed and ready for job matching and skill-gap course recommendations.")
    deduped = list(dict.fromkeys(p for p in points if p))
    return deduped[:limit] if deduped else ["CV analysed for matching."] * 3


class AIService:
    def __init__(self) -> None:
        self._client = None
        if settings.anthropic_api_key.strip():
            try:
                from anthropic import Anthropic

                self._client = Anthropic(api_key=settings.anthropic_api_key.strip())
            except Exception as exc:
                logger.warning("Anthropic client could not be initialised: %s", exc)

    @property
    def available(self) -> bool:
        return self._client is not None

    def _complete(self, system: str, prompt: str, max_tokens: int = 900) -> str | None:
        if self._client is None:
            return None
        try:
            message = self._client.messages.create(
                model=settings.anthropic_model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
            return "".join(
                block.text for block in message.content if getattr(block, "type", "") == "text"
            ).strip()
        except Exception as exc:
            logger.warning("Claude request failed: %s", exc)
            return None

    def extract_cv(self, text: str) -> dict[str, Any]:
        heuristic = {
            "summary": re.sub(r"\s+", " ", text[:700]).strip(),
            "skills": extract_skills(text),
            "education": _heuristic_education(text),
            "experience": _heuristic_experience(text),
            "job_titles": _heuristic_titles(text),
        }

        prompt = f"""Extract structured professional information from this CV.
Return ONLY a JSON object with exactly these keys:
- "summary": one short professional summary (max 400 chars)
- "skills": array of up to 40 professional skills
- "education": array of objects with keys "degree", "institution", "year"
- "experience": array of objects with keys "title", "company", "start", "end", "description"
- "job_titles": array of up to 8 job titles held or targeted

Do not include name, gender, age, nationality, photo, marital status, or any other
demographic/personal attribute. Only professional, job-relevant information.

CV:
{text[:12000]}"""

        parsed = _parse_json(
            self._complete(
                "You are a precise CV parsing engine for a fair recruitment platform. "
                "Respond with valid JSON only.",
                prompt,
                max_tokens=1600,
            )
        )
        if not parsed:
            heuristic["key_points"] = derive_key_points(heuristic)
            return heuristic

        result = {
            "summary": str(parsed.get("summary") or heuristic["summary"])[:1000],
            "skills": normalize_skills(merge_skills(_string_list(parsed.get("skills")), heuristic["skills"])),
            "education": _dict_list(parsed.get("education"), ("degree", "institution", "year")) or heuristic["education"],
            "experience": _dict_list(
                parsed.get("experience"), ("title", "company", "start", "end", "description")
            )
            or heuristic["experience"],
            "job_titles": _string_list(parsed.get("job_titles"), limit=8) or heuristic["job_titles"],
        }
        result["key_points"] = derive_key_points(result)
        return result

    def extract_job_skills(self, title: str, description: str) -> list[str]:
        detected = extract_skills(f"{title}\n{description}")
        if self._client is None:
            return normalize_skills(detected)

        prompt = f"""Extract the concrete skills a candidate needs for this job.
Return ONLY a JSON object: {{"skills": ["..."]}} with up to 20 skills.
Ignore company perks, benefits and demographic wording.

Job title: {title}
Job description:
{description[:10000]}"""
        parsed = _parse_json(
            self._complete(
                "You extract job requirements precisely. Respond with valid JSON only.",
                prompt,
                max_tokens=500,
            )
        )
        llm_skills = _string_list(parsed.get("skills") if parsed else None, limit=20)
        return normalize_skills(merge_skills(detected, llm_skills))

    def explain_match(
        self,
        job_title: str,
        score: float,
        matched: list[str],
        missing: list[str],
        candidate_titles: list[str],
        candidate_skills: list[str],
    ) -> str:
        fallback = self._fallback_explanation(job_title, score, matched, missing)
        if self._client is None:
            return fallback

        prompt = f"""Write a concise 2-3 sentence explanation of this job match.
Be factual, encouraging and specific. Never mention or infer name, gender, age,
nationality, ethnicity, disability or any other personal characteristic.

Job title: {job_title}
Match score: {score:.1f}%
Matched skills: {", ".join(matched) or "none"}
Missing skills: {", ".join(missing) or "none"}
Candidate titles: {", ".join(candidate_titles) or "not specified"}
Candidate skills: {", ".join(candidate_skills[:30]) or "not specified"}

Explain the fit and what the candidate could strengthen. Plain text, no markdown."""
        return self._complete(
            "You are a fair, concise career matching assistant.", prompt, max_tokens=260
        ) or fallback

    def course_advice(
        self,
        job_title: str | None,
        gaps: list[str],
        courses: list[dict[str, Any]],
    ) -> tuple[str, str]:
        if not courses:
            return (
                "No catalog course currently covers the identified skill gaps. "
                "Try broadening your search or gaining hands-on project experience in these areas.",
                "fallback",
            )

        fallback_lines = [
            f"To strengthen your fit for {job_title or 'your target roles'}, focus on: {', '.join(gaps) or 'the highlighted skills'}.",
            "",
        ]
        for course in courses:
            skills = ", ".join(course.get("covers") or course.get("skills") or [])
            fallback_lines.append(
                f"- {course['title']} by {course['provider']} ({course.get('level', 'all levels')}, "
                f"{course.get('duration', 'self-paced')}) — builds {skills or 'relevant skills'}. "
                f"Link: {course['url']}"
            )
        fallback_lines.append("")
        fallback_lines.append(
            "These suggestions come only from the TalentMatch course catalog. "
            "Completing a course does not guarantee a job, and TalentMatch does not issue certificates."
        )
        fallback = "\n".join(fallback_lines)

        if self._client is None:
            return fallback, "fallback"

        course_payload = [
            {
                "id": course["id"],
                "title": course["title"],
                "provider": course["provider"],
                "level": course.get("level"),
                "duration": course.get("duration"),
                "url": course["url"],
                "skills": course.get("skills"),
            }
            for course in courses
        ]
        prompt = f"""Write personalized course advice for a job seeker.

Target job: {job_title or "not specified"}
Skill gaps: {", ".join(gaps) or "none identified"}

AVAILABLE COURSES (the ONLY courses you may mention):
{json.dumps(course_payload, indent=2)}

Rules:
- Recommend only courses from the list above. NEVER invent, rename or imply other courses.
- For each recommended course, name the provider and explain which gap it addresses.
- Refer to skills, not demographics.
- Mention that courses do not guarantee a job and TalentMatch does not issue certificates.
- 120-220 words, plain text with short bullet points. No markdown headings."""

        advice = self._complete(
            "You are a course advisor using a strictly grounded retrieval-augmented catalog. "
            "Never mention courses outside the provided list.",
            prompt,
            max_tokens=650,
        )
        return (advice, "claude") if advice else (fallback, "fallback")

    def quick_explanation(
        self, job_title: str, score: float, matched: list[str], missing: list[str]
    ) -> str:
        return self._fallback_explanation(job_title, score, matched, missing)

    @staticmethod
    def _fallback_explanation(
        job_title: str, score: float, matched: list[str], missing: list[str]
    ) -> str:
        matched_text = ", ".join(matched[:6]) if matched else "none of the listed skills"
        if score >= 75:
            opening = f"Strong match for {job_title} ({score:.0f}%)."
        elif score >= 50:
            opening = f"Moderate match for {job_title} ({score:.0f}%)."
        else:
            opening = f"Partial match for {job_title} ({score:.0f}%)."
        if missing:
            closing = f"Developing {', '.join(missing[:4])} would strengthen the application."
        else:
            closing = "All required skills are represented in the profile."
        return f"{opening} Your profile demonstrates {matched_text}. {closing}"


ai_service = AIService()
