import re
from functools import lru_cache

SKILL_ALIASES: dict[str, list[str]] = {
    "Python": ["python", "python3"],
    "JavaScript": ["javascript", "js", "ecmascript"],
    "TypeScript": ["typescript", "ts"],
    "React": ["react", "react.js", "reactjs"],
    "Next.js": ["next.js", "nextjs"],
    "Vue.js": ["vue", "vue.js", "vuejs"],
    "Angular": ["angular", "angularjs"],
    "Node.js": ["node.js", "nodejs", "node"],
    "Express": ["express.js", "expressjs", "express"],
    "FastAPI": ["fastapi"],
    "Django": ["django"],
    "Flask": ["flask"],
    "REST APIs": ["rest api", "rest apis", "restful", "restful apis"],
    "GraphQL": ["graphql"],
    "SQL": ["sql"],
    "PostgreSQL": ["postgresql", "postgres", "psql"],
    "MySQL": ["mysql", "mariadb"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Docker": ["docker", "containers"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure", "microsoft azure"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration", "continuous delivery"],
    "Git": ["git", "github", "gitlab", "version control"],
    "Linux": ["linux", "unix", "bash"],
    "Terraform": ["terraform", "infrastructure as code"],
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "neural networks"],
    "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision", "opencv"],
    "PyTorch": ["pytorch"],
    "TensorFlow": ["tensorflow", "keras"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Data Analysis": ["data analysis", "data analytics", "analytics"],
    "Data Visualization": ["data visualization", "data visualisation", "matplotlib", "plotly"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    "Excel": ["excel", "microsoft excel", "spreadsheets"],
    "Statistics": ["statistics", "statistical analysis"],
    "A/B Testing": ["a/b testing", "ab testing", "split testing"],
    "Product Management": ["product management", "product manager"],
    "Agile": ["agile"],
    "Scrum": ["scrum"],
    "Project Management": ["project management", "project manager"],
    "Communication": ["communication", "communication skills"],
    "Leadership": ["leadership", "team leadership"],
    "Teamwork": ["teamwork", "collaboration", "team player"],
    "Problem Solving": ["problem solving", "problem-solving"],
    "Critical Thinking": ["critical thinking"],
    "Figma": ["figma"],
    "UI Design": ["ui design", "interface design"],
    "UX Design": ["ux design", "user experience", "ux research"],
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],
    "Tailwind CSS": ["tailwind", "tailwind css"],
    "SASS": ["sass", "scss"],
    "Java": ["java"],
    "Spring Boot": ["spring boot", "spring"],
    "C#": ["c#", "csharp", ".net c#"],
    ".NET": [".net", "dotnet", "asp.net"],
    "C++": ["c++", "cpp"],
    "PHP": ["php"],
    "Laravel": ["laravel"],
    "Ruby": ["ruby"],
    "Ruby on Rails": ["ruby on rails", "rails"],
    "Swift": ["swift", "swiftui"],
    "Kotlin": ["kotlin"],
    "Flutter": ["flutter", "dart"],
    "React Native": ["react native"],
    "Android": ["android", "android development"],
    "iOS": ["ios", "ios development"],
    "Go": ["golang", "go language"],
    "Rust": ["rust"],
    "Cybersecurity": ["cybersecurity", "cyber security", "information security", "infosec"],
    "Penetration Testing": ["penetration testing", "pen testing", "ethical hacking"],
    "Networking": ["networking", "tcp/ip", "network administration"],
    "Cloud Security": ["cloud security"],
    "Salesforce": ["salesforce"],
    "SAP": ["sap"],
    "HubSpot": ["hubspot"],
    "SEO": ["seo", "search engine optimization"],
    "Content Marketing": ["content marketing", "content strategy"],
    "Digital Marketing": ["digital marketing", "online marketing"],
    "Email Marketing": ["email marketing", "mailchimp"],
    "Copywriting": ["copywriting", "content writing"],
    "Social Media Marketing": ["social media marketing", "social media"],
    "Accounting": ["accounting", "bookkeeping"],
    "Financial Analysis": ["financial analysis", "financial modeling", "finance"],
    "QuickBooks": ["quickbooks"],
    "Risk Management": ["risk management"],
    "HR": ["human resources", "hr", "people operations"],
    "Recruiting": ["recruiting", "recruitment", "talent acquisition"],
    "Payroll": ["payroll"],
    "Customer Service": ["customer service", "customer support"],
    "Sales": ["sales", "business development"],
    "Negotiation": ["negotiation", "negotiating"],
    "Business Analysis": ["business analysis", "business analyst"],
    "Data Engineering": ["data engineering", "data pipelines"],
    "Apache Spark": ["apache spark", "spark", "pyspark"],
    "Kafka": ["kafka", "apache kafka"],
    "Airflow": ["airflow", "apache airflow"],
    "ETL": ["etl", "elt", "data extraction"],
    "DevOps": ["devops", "site reliability"],
    "Ansible": ["ansible"],
    "Jenkins": ["jenkins"],
    "GitHub Actions": ["github actions"],
    "Microservices": ["microservices", "microservice architecture"],
    "System Design": ["system design", "distributed systems"],
    "Unit Testing": ["unit testing", "pytest", "jest", "junit"],
    "Selenium": ["selenium"],
    "Playwright": ["playwright", "cypress"],
    "Test Automation": ["test automation", "automated testing", "qa automation"],
    "Generative AI": ["generative ai", "genai", "gen ai"],
    "LLM": ["llm", "llms", "large language models"],
    "Prompt Engineering": ["prompt engineering", "prompt design"],
    "RAG": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
    "Vector Databases": ["vector database", "vector databases", "chromadb", "pinecone", "pgvector"],
    "MLOps": ["mlops", "model deployment", "model monitoring"],
    "Databricks": ["databricks"],
    "Snowflake": ["snowflake"],
    "dbt": ["dbt", "data build tool"],
    "Looker": ["looker"],
    "Photoshop": ["photoshop", "adobe photoshop"],
    "Illustrator": ["illustrator", "adobe illustrator"],
    "Adobe XD": ["adobe xd", "xd"],
    "Sketch": ["sketch"],
    "Presentation Skills": ["presentation skills", "public speaking"],
    "Writing": ["technical writing", "writing"],
    "Customer Relationship Management": ["crm", "customer relationship management"],
    "Supply Chain": ["supply chain", "logistics"],
    "Operations": ["operations management", "operations"],
}


@lru_cache
def _alias_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, aliases in SKILL_ALIASES.items():
        lookup[canonical.lower()] = canonical
        for alias in aliases:
            lookup[alias.lower()] = canonical
    return lookup


@lru_cache
def _skill_pattern() -> re.Pattern[str]:
    aliases = sorted(_alias_lookup().keys(), key=len, reverse=True)
    escaped = "|".join(re.escape(alias) for alias in aliases)
    return re.compile(rf"(?<![\w+#.])(?:{escaped})(?![\w+#]|\.\w)", re.IGNORECASE)


def canonicalize(skill: str) -> str:
    cleaned = re.sub(r"\s+", " ", skill.strip())
    if not cleaned:
        return ""
    lookup = _alias_lookup()
    direct = lookup.get(cleaned.lower())
    if direct:
        return direct
    if cleaned.lower() in ("js", "ts"):
        return "JavaScript" if cleaned.lower() == "js" else "TypeScript"
    return cleaned[:80]


def extract_skills(text: str) -> list[str]:
    if not text:
        return []
    found = {canonicalize(match.group(0)) for match in _skill_pattern().finditer(text)}
    return sorted(skill for skill in found if skill)


def normalize_skills(skills: list[str] | None) -> list[str]:
    if not skills:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for skill in skills:
        canonical = canonicalize(str(skill))
        key = canonical.lower()
        if canonical and key not in seen:
            seen.add(key)
            result.append(canonical)
    return sorted(result)


def merge_skills(*skill_lists: list[str] | None) -> list[str]:
    merged: set[str] = set()
    for skills in skill_lists:
        merged.update(normalize_skills(skills))
    return sorted(merged)


def skill_overlap(candidate_skills: list[str], required_skills: list[str]) -> tuple[list[str], list[str], float]:
    candidate = set(normalize_skills(candidate_skills))
    required_list = normalize_skills(required_skills)
    if not required_list:
        return [], [], 0.0
    matched = [skill for skill in required_list if skill in candidate]
    missing = [skill for skill in required_list if skill not in candidate]
    overlap = len(matched) / len(required_list)
    return matched, missing, round(overlap, 4)
