"""Seed TalentMatch AI with demo users, jobs and a 50-course catalog.

Usage:
    python seed.py            # create missing data, refresh vector index
    python seed.py --reset    # drop all tables first (destructive)
"""

import argparse
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import (
    Application,
    Course,
    CV,
    EmployerProfile,
    Job,
    JobSeekerProfile,
    User,
    UserRole,
)
from app.security import hash_password
from app.services.embeddings import cv_embedding_text, embedder, job_embedding_text
from app.services.skills import extract_skills, normalize_skills

DEMO_PASSWORD = "Password123!"

COURSES = [
    {
        "title": "Python for Everybody",
        "provider": "University of Michigan (Coursera)",
        "description": "A beginner-friendly specialization covering Python programming, data structures, web scraping and data handling.",
        "skills": ["Python", "Data Analysis", "REST APIs"],
        "level": "beginner",
        "duration": "8 weeks",
        "url": "https://www.coursera.org/specializations/python",
    },
    {
        "title": "Modern JavaScript from the Beginning",
        "provider": "Udemy",
        "description": "Learn modern JavaScript, ES6+, asynchronous programming and the DOM through hands-on projects.",
        "skills": ["JavaScript", "HTML", "CSS"],
        "level": "beginner",
        "duration": "20 hours",
        "url": "https://www.udemy.com/course/modern-javascript-from-the-beginning/",
    },
    {
        "title": "TypeScript Fundamentals",
        "provider": "Pluralsight",
        "description": "Master TypeScript types, generics, interfaces and tooling for large JavaScript applications.",
        "skills": ["TypeScript", "JavaScript"],
        "level": "intermediate",
        "duration": "6 hours",
        "url": "https://www.pluralsight.com/courses/typescript-fundamentals",
    },
    {
        "title": "React - The Complete Guide",
        "provider": "Udemy",
        "description": "Build modern React applications with hooks, routing, state management and API integration.",
        "skills": ["React", "JavaScript", "HTML", "CSS", "REST APIs"],
        "level": "intermediate",
        "duration": "40 hours",
        "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/",
    },
    {
        "title": "Next.js 15 Complete Guide",
        "provider": "Udemy",
        "description": "Full-stack React with Next.js: server components, routing, data fetching and deployment.",
        "skills": ["Next.js", "React", "TypeScript", "REST APIs"],
        "level": "intermediate",
        "duration": "25 hours",
        "url": "https://www.udemy.com/course/nextjs-react-the-complete-guide/",
    },
    {
        "title": "Tailwind CSS From Scratch",
        "provider": "Udemy",
        "description": "Design responsive interfaces quickly with Tailwind CSS utility patterns and components.",
        "skills": ["Tailwind CSS", "HTML", "CSS", "UI Design"],
        "level": "beginner",
        "duration": "10 hours",
        "url": "https://www.udemy.com/course/tailwind-from-scratch/",
    },
    {
        "title": "Node.js, Express and MongoDB Bootcamp",
        "provider": "Udemy",
        "description": "Build production REST APIs with Node.js, Express, MongoDB, authentication and deployment.",
        "skills": ["Node.js", "Express", "MongoDB", "REST APIs", "JavaScript"],
        "level": "intermediate",
        "duration": "30 hours",
        "url": "https://www.udemy.com/course/nodejs-express-mongodb-bootcamp/",
    },
    {
        "title": "FastAPI - The Complete Course",
        "provider": "Udemy",
        "description": "Create typed, high-performance Python APIs with FastAPI, SQLAlchemy, authentication and testing.",
        "skills": ["FastAPI", "Python", "REST APIs", "SQL", "PostgreSQL"],
        "level": "intermediate",
        "duration": "18 hours",
        "url": "https://www.udemy.com/course/fastapi-modern-python-apis/",
    },
    {
        "title": "Django for Beginners",
        "provider": "Django Software Foundation",
        "description": "Build database-backed Python web applications with Django models, views, templates and admin.",
        "skills": ["Django", "Python", "PostgreSQL", "SQL"],
        "level": "beginner",
        "duration": "12 weeks",
        "url": "https://djangoforbeginners.com/",
    },
    {
        "title": "SQL for Data Science",
        "provider": "UC Davis (Coursera)",
        "description": "Query relational databases and analyze business data with practical SQL exercises.",
        "skills": ["SQL", "MySQL", "Data Analysis"],
        "level": "beginner",
        "duration": "4 weeks",
        "url": "https://www.coursera.org/learn/sql-for-data-science",
    },
    {
        "title": "PostgreSQL Bootcamp",
        "provider": "Udemy",
        "description": "Learn PostgreSQL administration, advanced queries, indexes, transactions and database design.",
        "skills": ["PostgreSQL", "SQL"],
        "level": "intermediate",
        "duration": "22 hours",
        "url": "https://www.udemy.com/course/postgresqlbootcamp/",
    },
    {
        "title": "Docker and Kubernetes: The Practical Guide",
        "provider": "Udemy",
        "description": "Containerize applications with Docker and orchestrate them on Kubernetes in production scenarios.",
        "skills": ["Docker", "Kubernetes", "DevOps", "Linux", "CI/CD"],
        "level": "intermediate",
        "duration": "24 hours",
        "url": "https://www.udemy.com/course/docker-kubernetes-the-practical-guide/",
    },
    {
        "title": "AWS Certified Solutions Architect - Associate",
        "provider": "A Cloud Guru",
        "description": "Design resilient, secure and cost-optimized architectures on Amazon Web Services.",
        "skills": ["AWS", "Cloud Security", "Networking", "DevOps"],
        "level": "intermediate",
        "duration": "30 hours",
        "url": "https://www.pluralsight.com/cloud-guru/courses/aws-certified-solutions-architect-associate",
    },
    {
        "title": "Microsoft Azure Fundamentals (AZ-900)",
        "provider": "Microsoft Learn",
        "description": "Introduction to Azure cloud concepts, core services, security and pricing.",
        "skills": ["Azure", "Cloud Security", "Networking"],
        "level": "beginner",
        "duration": "8 hours",
        "url": "https://learn.microsoft.com/training/courses/az-900t00",
    },
    {
        "title": "Google Cloud Digital Leader",
        "provider": "Google Cloud",
        "description": "Understand Google Cloud products, data strategy, security and digital transformation.",
        "skills": ["GCP", "Cloud Security", "Networking"],
        "level": "beginner",
        "duration": "10 hours",
        "url": "https://cloud.google.com/learn/certification/cloud-digital-leader",
    },
    {
        "title": "Terraform: Infrastructure as Code",
        "provider": "Udemy",
        "description": "Provision and manage cloud infrastructure repeatably with Terraform modules and state.",
        "skills": ["Terraform", "AWS", "DevOps", "CI/CD"],
        "level": "intermediate",
        "duration": "16 hours",
        "url": "https://www.udemy.com/course/terraform-beginner-to-advanced/",
    },
    {
        "title": "CI/CD with GitHub Actions",
        "provider": "Pluralsight",
        "description": "Automate builds, tests and deployments with GitHub Actions workflows and reusable components.",
        "skills": ["CI/CD", "GitHub Actions", "Docker", "DevOps", "Git"],
        "level": "intermediate",
        "duration": "5 hours",
        "url": "https://www.pluralsight.com/courses/github-actions-building-cicd-pipelines",
    },
    {
        "title": "Machine Learning Specialization",
        "provider": "DeepLearning.AI (Coursera)",
        "description": "Foundational machine learning with Python: regression, classification, clustering and recommender systems.",
        "skills": ["Machine Learning", "Python", "NumPy", "scikit-learn", "Data Analysis"],
        "level": "beginner",
        "duration": "10 weeks",
        "url": "https://www.coursera.org/specializations/machine-learning-introduction",
    },
    {
        "title": "Deep Learning Specialization",
        "provider": "DeepLearning.AI (Coursera)",
        "description": "Neural networks, CNNs, sequence models and practical deep learning with TensorFlow.",
        "skills": ["Deep Learning", "TensorFlow", "NLP", "Computer Vision", "Python"],
        "level": "advanced",
        "duration": "12 weeks",
        "url": "https://www.coursera.org/specializations/deep-learning",
    },
    {
        "title": "Natural Language Processing with Python",
        "provider": "Udemy",
        "description": "Process and model text with spaCy, transformers and modern NLP techniques.",
        "skills": ["NLP", "Python", "Deep Learning", "Machine Learning"],
        "level": "intermediate",
        "duration": "14 hours",
        "url": "https://www.udemy.com/course/natural-language-processing-with-python/",
    },
    {
        "title": "PyTorch for Deep Learning",
        "provider": "Udemy",
        "description": "Build, train and evaluate neural networks with PyTorch for vision and language tasks.",
        "skills": ["PyTorch", "Deep Learning", "Python", "Computer Vision"],
        "level": "intermediate",
        "duration": "20 hours",
        "url": "https://www.udemy.com/course/pytorch-for-deep-learning/",
    },
    {
        "title": "Data Analysis with Pandas and NumPy",
        "provider": "Udemy",
        "description": "Clean, transform and analyze tabular data with the Python data stack.",
        "skills": ["Pandas", "NumPy", "Data Analysis", "Python"],
        "level": "beginner",
        "duration": "12 hours",
        "url": "https://www.udemy.com/course/data-analysis-with-pandas/",
    },
    {
        "title": "Data Visualization with Tableau",
        "provider": "Coursera",
        "description": "Create interactive dashboards and communicate insights effectively with Tableau.",
        "skills": ["Tableau", "Data Visualization", "Data Analysis"],
        "level": "beginner",
        "duration": "6 weeks",
        "url": "https://www.coursera.org/specializations/data-visualization",
    },
    {
        "title": "Power BI Complete Guide",
        "provider": "Udemy",
        "description": "Model data, write DAX and build business dashboards in Microsoft Power BI.",
        "skills": ["Power BI", "Data Visualization", "Excel", "Data Analysis"],
        "level": "intermediate",
        "duration": "18 hours",
        "url": "https://www.udemy.com/course/power-bi-complete-guide/",
    },
    {
        "title": "Statistics for Data Science",
        "provider": "Coursera",
        "description": "Probability, inference, hypothesis testing and experiment design for data-driven decisions.",
        "skills": ["Statistics", "Data Analysis", "A/B Testing"],
        "level": "intermediate",
        "duration": "8 weeks",
        "url": "https://www.coursera.org/specializations/statistics",
    },
    {
        "title": "Google Data Analytics",
        "provider": "Google (Coursera)",
        "description": "End-to-end data analytics program covering spreadsheets, SQL, R and Tableau.",
        "skills": ["Data Analysis", "SQL", "Excel", "Tableau", "Data Visualization"],
        "level": "beginner",
        "duration": "6 months",
        "url": "https://www.coursera.org/professional-certificates/google-data-analytics",
    },
    {
        "title": "Data Engineering Foundations",
        "provider": "IBM (Coursera)",
        "description": "Relational databases, ETL, data pipelines and warehouse concepts for data engineers.",
        "skills": ["Data Engineering", "SQL", "ETL", "Python", "PostgreSQL"],
        "level": "beginner",
        "duration": "10 weeks",
        "url": "https://www.coursera.org/professional-certificates/ibm-data-engineer",
    },
    {
        "title": "Apache Spark and Kafka for Data Engineering",
        "provider": "Udemy",
        "description": "Build streaming and batch data pipelines with Spark, Kafka and Airflow.",
        "skills": ["Apache Spark", "Kafka", "Airflow", "ETL", "Data Engineering", "Python"],
        "level": "advanced",
        "duration": "28 hours",
        "url": "https://www.udemy.com/course/spark-and-kafka/",
    },
    {
        "title": "MLOps Fundamentals",
        "provider": "Coursera",
        "description": "Deploy, monitor and operate machine learning models reliably in production.",
        "skills": ["MLOps", "Docker", "CI/CD", "Machine Learning", "DevOps"],
        "level": "intermediate",
        "duration": "6 weeks",
        "url": "https://www.coursera.org/learn/mlops-fundamentals",
    },
    {
        "title": "Generative AI with Large Language Models",
        "provider": "DeepLearning.AI (Coursera)",
        "description": "How LLMs work, how to fine-tune them and how to build generative AI applications responsibly.",
        "skills": ["Generative AI", "LLM", "Prompt Engineering", "Python"],
        "level": "intermediate",
        "duration": "3 weeks",
        "url": "https://www.coursera.org/learn/generative-ai-with-llms",
    },
    {
        "title": "Building RAG Applications",
        "provider": "LangChain Academy",
        "description": "Build retrieval-augmented generation systems with vector stores, chunking and grounded answers.",
        "skills": ["RAG", "LLM", "Vector Databases", "Python", "Generative AI"],
        "level": "intermediate",
        "duration": "8 hours",
        "url": "https://academy.langchain.com/courses/intro-to-langgraph",
    },
    {
        "title": "Prompt Engineering for Developers",
        "provider": "DeepLearning.AI",
        "description": "Design reliable prompts, iterate systematically and evaluate LLM outputs.",
        "skills": ["Prompt Engineering", "LLM", "Generative AI"],
        "level": "beginner",
        "duration": "2 hours",
        "url": "https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/",
    },
    {
        "title": "UX/UI Design Fundamentals",
        "provider": "Google (Coursera)",
        "description": "User research, wireframing, prototyping and usability testing for digital products.",
        "skills": ["UX Design", "UI Design", "Figma", "Communication", "Critical Thinking"],
        "level": "beginner",
        "duration": "6 months",
        "url": "https://www.coursera.org/professional-certificates/google-ux-design",
    },
    {
        "title": "Figma UI Design",
        "provider": "Udemy",
        "description": "Design responsive interfaces and design systems in Figma from wireframe to prototype.",
        "skills": ["Figma", "UI Design", "UX Design"],
        "level": "beginner",
        "duration": "14 hours",
        "url": "https://www.udemy.com/course/figma-ui-design/",
    },
    {
        "title": "Agile Project Management",
        "provider": "Google (Coursera)",
        "description": "Run Agile teams with Scrum, Kanban, stakeholder communication and delivery planning.",
        "skills": ["Agile", "Scrum", "Project Management", "Communication", "Leadership"],
        "level": "beginner",
        "duration": "6 months",
        "url": "https://www.coursera.org/professional-certificates/google-project-management",
    },
    {
        "title": "PMP Exam Prep",
        "provider": "Project Management Institute",
        "description": "Prepare for PMP certification with predictive, agile and hybrid project management practices.",
        "skills": ["Project Management", "Leadership", "Risk Management", "Agile", "Communication"],
        "level": "advanced",
        "duration": "35 hours",
        "url": "https://www.pmi.org/certifications/project-management-pmp",
    },
    {
        "title": "Digital Marketing Specialization",
        "provider": "Google (Coursera)",
        "description": "Digital marketing strategy, SEO, social media, email and analytics for modern brands.",
        "skills": [
            "Digital Marketing",
            "SEO",
            "Social Media Marketing",
            "Email Marketing",
            "Content Marketing",
            "Data Analysis",
        ],
        "level": "beginner",
        "duration": "8 weeks",
        "url": "https://www.coursera.org/specializations/digital-marketing",
    },
    {
        "title": "SEO Foundations",
        "provider": "Semrush Academy",
        "description": "Keyword research, on-page optimization and technical SEO for organic growth.",
        "skills": ["SEO", "Content Marketing", "Copywriting", "Digital Marketing"],
        "level": "beginner",
        "duration": "4 hours",
        "url": "https://www.semrush.com/academy/courses/seo-foundations/",
    },
    {
        "title": "HubSpot Inbound Marketing",
        "provider": "HubSpot Academy",
        "description": "Inbound methodology, CRM fundamentals, lead nurturing and marketing automation.",
        "skills": [
            "HubSpot",
            "Digital Marketing",
            "Email Marketing",
            "Customer Relationship Management",
            "Sales",
        ],
        "level": "beginner",
        "duration": "6 hours",
        "url": "https://academy.hubspot.com/courses/inbound-marketing",
    },
    {
        "title": "Financial Analysis and Modeling",
        "provider": "Corporate Finance Institute",
        "description": "Build three-statement financial models, valuation and scenario analysis in Excel.",
        "skills": ["Financial Analysis", "Excel", "Accounting", "Statistics"],
        "level": "intermediate",
        "duration": "20 hours",
        "url": "https://corporatefinanceinstitute.com/course/financial-modeling-fundamentals/",
    },
    {
        "title": "Accounting Fundamentals",
        "provider": "Corporate Finance Institute",
        "description": "Financial statements, bookkeeping, accruals and accounting principles for analysts.",
        "skills": ["Accounting", "Financial Analysis", "QuickBooks", "Excel"],
        "level": "beginner",
        "duration": "12 hours",
        "url": "https://corporatefinanceinstitute.com/course/accounting-fundamentals/",
    },
    {
        "title": "Cybersecurity Essentials",
        "provider": "Cisco Networking Academy",
        "description": "Security principles, network defense, cryptography and cyber threat awareness.",
        "skills": ["Cybersecurity", "Networking", "Cloud Security", "Linux"],
        "level": "beginner",
        "duration": "8 weeks",
        "url": "https://www.netacad.com/courses/cybersecurity",
    },
    {
        "title": "Ethical Hacking and Penetration Testing",
        "provider": "Udemy",
        "description": "Practice offensive security, reconnaissance, exploitation and reporting in lab environments.",
        "skills": ["Penetration Testing", "Cybersecurity", "Networking", "Linux"],
        "level": "intermediate",
        "duration": "22 hours",
        "url": "https://www.udemy.com/course/learn-ethical-hacking-from-scratch/",
    },
    {
        "title": "Java Spring Boot Microservices",
        "provider": "Udemy",
        "description": "Build production microservices with Spring Boot, REST, messaging and Docker.",
        "skills": ["Java", "Spring Boot", "Microservices", "Docker", "REST APIs"],
        "level": "advanced",
        "duration": "26 hours",
        "url": "https://www.udemy.com/course/spring-boot-microservices-and-spring-cloud/",
    },
    {
        "title": "C# and .NET Full Stack",
        "provider": "Udemy",
        "description": "Develop modern web APIs and applications with C#, ASP.NET Core and SQL Server.",
        "skills": ["C#", ".NET", "SQL", "REST APIs"],
        "level": "intermediate",
        "duration": "28 hours",
        "url": "https://www.udemy.com/course/complete-csharp-masterclass/",
    },
    {
        "title": "Flutter and Dart - The Complete Guide",
        "provider": "Udemy",
        "description": "Build cross-platform mobile apps for Android and iOS with Flutter and Dart.",
        "skills": ["Flutter", "Android", "iOS", "UI Design"],
        "level": "intermediate",
        "duration": "30 hours",
        "url": "https://www.udemy.com/course/learn-flutter-dart-to-build-ios-android-apps/",
    },
    {
        "title": "React Native - The Practical Guide",
        "provider": "Udemy",
        "description": "Ship mobile apps for iOS and Android using React Native and JavaScript.",
        "skills": ["React Native", "JavaScript", "Android", "iOS", "React"],
        "level": "intermediate",
        "duration": "24 hours",
        "url": "https://www.udemy.com/course/react-native-the-practical-guide/",
    },
    {
        "title": "Selenium WebDriver with Python",
        "provider": "Udemy",
        "description": "Automate browser testing with Selenium, pytest and maintainable page objects.",
        "skills": ["Selenium", "Test Automation", "Python", "Unit Testing", "Git"],
        "level": "intermediate",
        "duration": "18 hours",
        "url": "https://www.udemy.com/course/selenium-python/",
    },
    {
        "title": "Playwright End-to-End Testing",
        "provider": "Udemy",
        "description": "Write reliable end-to-end tests with Playwright, TypeScript and CI pipelines.",
        "skills": ["Playwright", "Test Automation", "JavaScript", "CI/CD", "TypeScript"],
        "level": "intermediate",
        "duration": "10 hours",
        "url": "https://www.udemy.com/course/playwright-tutorials-automation-testing/",
    },
    {
        "title": "System Design Interview",
        "provider": "Educative",
        "description": "Design scalable distributed systems with caching, queues, databases and microservices.",
        "skills": ["System Design", "Microservices", "SQL", "Kubernetes", "Communication"],
        "level": "advanced",
        "duration": "20 hours",
        "url": "https://www.educative.io/courses/grokking-the-system-design-interview",
    },
]

JOBS = [
    {
        "employer": "Northstar Labs",
        "title": "Senior Full Stack Engineer",
        "description": (
            "Design and ship customer-facing features across our React front end and Node.js services. "
            "You will own APIs, improve PostgreSQL performance, containerize services with Docker and "
            "deploy to AWS. Collaborate closely with product and design in a small agile team."
        ),
        "required_skills": ["React", "TypeScript", "Node.js", "PostgreSQL", "REST APIs", "Docker", "AWS", "Git"],
        "location": "Remote (EU)",
        "job_type": "full_time",
        "salary_min": 90000,
        "salary_max": 125000,
        "currency": "EUR",
        "days": 45,
    },
    {
        "employer": "Northstar Labs",
        "title": "Data Scientist",
        "description": (
            "Turn product and customer data into decisions. Build predictive models with Python and "
            "scikit-learn, run experiments, and communicate insights with dashboards. Experience with "
            "NLP and SQL warehouses is a plus."
        ),
        "required_skills": ["Python", "Machine Learning", "SQL", "Pandas", "scikit-learn", "Statistics", "Data Visualization"],
        "location": "Berlin, Germany (Hybrid)",
        "job_type": "full_time",
        "salary_min": 70000,
        "salary_max": 95000,
        "currency": "EUR",
        "days": 30,
    },
    {
        "employer": "Northstar Labs",
        "title": "AI/ML Engineer",
        "description": (
            "Build retrieval-augmented generation services and production LLM features. You will work with "
            "Python, FastAPI, vector databases and PyTorch, evaluate model quality and deploy services with Docker."
        ),
        "required_skills": ["Python", "LLM", "RAG", "Vector Databases", "FastAPI", "PyTorch", "Docker", "Generative AI"],
        "location": "Remote",
        "job_type": "full_time",
        "salary_min": 95000,
        "salary_max": 140000,
        "currency": "EUR",
        "days": 60,
    },
    {
        "employer": "Northstar Labs",
        "title": "DevOps Engineer",
        "description": (
            "Own our cloud infrastructure and developer experience. Automate AWS environments with Terraform, "
            "operate Kubernetes, build CI/CD pipelines and improve observability and security."
        ),
        "required_skills": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "Linux", "Git"],
        "location": "Remote (EU)",
        "job_type": "full_time",
        "salary_min": 85000,
        "salary_max": 115000,
        "currency": "EUR",
        "days": 40,
    },
    {
        "employer": "Northstar Labs",
        "title": "Data Engineer",
        "description": (
            "Build reliable batch and streaming data pipelines with Python, Spark, Kafka and Airflow. "
            "Model warehouse data, improve data quality and partner with analytics teams."
        ),
        "required_skills": ["Python", "SQL", "Apache Spark", "Kafka", "Airflow", "ETL", "AWS", "Data Engineering"],
        "location": "Amsterdam, Netherlands",
        "job_type": "full_time",
        "salary_min": 80000,
        "salary_max": 110000,
        "currency": "EUR",
        "days": 50,
    },
    {
        "employer": "Cobalt Health",
        "title": "Product Designer",
        "description": (
            "Lead end-to-end product design for patient-facing experiences. Conduct research, create "
            "wireframes and prototypes in Figma and collaborate with engineers to ship accessible interfaces."
        ),
        "required_skills": ["UX Design", "UI Design", "Figma", "Communication", "Teamwork", "Critical Thinking"],
        "location": "London, UK (Hybrid)",
        "job_type": "full_time",
        "salary_min": 60000,
        "salary_max": 80000,
        "currency": "GBP",
        "days": 35,
    },
    {
        "employer": "Cobalt Health",
        "title": "Digital Marketing Manager",
        "description": (
            "Own our acquisition strategy across SEO, content, social and email. Use HubSpot and analytics "
            "to run campaigns, report on performance and improve conversion."
        ),
        "required_skills": ["Digital Marketing", "SEO", "Content Marketing", "Social Media Marketing", "Email Marketing", "HubSpot", "Communication"],
        "location": "Remote (UK)",
        "job_type": "full_time",
        "salary_min": 50000,
        "salary_max": 68000,
        "currency": "GBP",
        "days": 25,
    },
    {
        "employer": "Cobalt Health",
        "title": "Financial Analyst",
        "description": (
            "Build financial models, analyze revenue drivers and support planning. Strong Excel and "
            "accounting fundamentals are essential; experience with data visualization is welcome."
        ),
        "required_skills": ["Excel", "Financial Analysis", "Accounting", "Data Analysis", "Communication"],
        "location": "London, UK",
        "job_type": "full_time",
        "salary_min": 52000,
        "salary_max": 70000,
        "currency": "GBP",
        "days": 30,
    },
    {
        "employer": "Cobalt Health",
        "title": "Frontend Engineer",
        "description": (
            "Build accessible, responsive interfaces in React and TypeScript. Work with designers on a "
            "shared component library and integrate REST APIs."
        ),
        "required_skills": ["React", "TypeScript", "JavaScript", "HTML", "CSS", "REST APIs", "Git"],
        "location": "Remote",
        "job_type": "contract",
        "salary_min": 50000,
        "salary_max": 75000,
        "currency": "GBP",
        "days": 20,
    },
    {
        "employer": "Cobalt Health",
        "title": "Cybersecurity Analyst",
        "description": (
            "Monitor threats, investigate security incidents and harden cloud workloads. Knowledge of "
            "networking, Linux and penetration testing techniques is valuable."
        ),
        "required_skills": ["Cybersecurity", "Networking", "Linux", "Cloud Security", "Penetration Testing"],
        "location": "Manchester, UK (Hybrid)",
        "job_type": "full_time",
        "salary_min": 55000,
        "salary_max": 75000,
        "currency": "GBP",
        "days": 45,
    },
]

SEEKERS = [
    {
        "email": "alex@talentmatch.ai",
        "name": "Alex Rivera",
        "headline": "Senior Full Stack Engineer",
        "location": "Lisbon, Portugal",
        "bio": "Full stack engineer with 6 years building React and Node.js products.",
        "manual_skills": ["Communication", "Teamwork"],
        "cv_text": (
            "Alex Rivera - Senior Full Stack Engineer\n"
            "Lisbon, Portugal\n\n"
            "Summary: Full stack engineer with six years of experience building web platforms.\n\n"
            "Experience:\n"
            "2019 - Present Senior Full Stack Engineer at Brightline\n"
            "2017 - 2019 Frontend Developer at Nimbus Studio\n\n"
            "Skills: TypeScript, React, Node.js, Express, PostgreSQL, REST APIs, Docker, AWS, Git, CI/CD\n\n"
            "Education:\n"
            "Bachelor of Science in Computer Science, University of Lisbon, 2017"
        ),
        "job_titles": ["Senior Full Stack Engineer", "Frontend Developer"],
        "education": [
            {"degree": "BSc Computer Science", "institution": "University of Lisbon", "year": "2017"}
        ],
        "experience": [
            {
                "title": "Senior Full Stack Engineer",
                "company": "Brightline",
                "start": "2019",
                "end": "Present",
                "description": "Built React and Node.js platforms on AWS; led PostgreSQL performance work.",
            },
            {
                "title": "Frontend Developer",
                "company": "Nimbus Studio",
                "start": "2017",
                "end": "2019",
                "description": "Delivered responsive React interfaces and design system components.",
            },
        ],
        "apply_to": "Senior Full Stack Engineer",
    },
    {
        "email": "priya@talentmatch.ai",
        "name": "Priya Sharma",
        "headline": "Data Scientist",
        "location": "Berlin, Germany",
        "bio": "Data scientist focused on experimentation, forecasting and NLP.",
        "manual_skills": ["Communication"],
        "cv_text": (
            "Priya Sharma - Data Scientist\n"
            "Berlin, Germany\n\n"
            "Summary: Data scientist with four years of experience in product analytics and NLP.\n\n"
            "Experience:\n"
            "2021 - Present Data Scientist at Helio Analytics\n"
            "2019 - 2021 Data Analyst at Kite Retail\n\n"
            "Skills: Python, Machine Learning, Pandas, NumPy, SQL, scikit-learn, Statistics, "
            "Data Visualization, Tableau, NLP, A/B Testing, Git\n\n"
            "Education:\n"
            "Master of Science in Data Science, TU Berlin, 2019"
        ),
        "job_titles": ["Data Scientist", "Data Analyst"],
        "education": [
            {"degree": "MSc Data Science", "institution": "TU Berlin", "year": "2019"}
        ],
        "experience": [
            {
                "title": "Data Scientist",
                "company": "Helio Analytics",
                "start": "2021",
                "end": "Present",
                "description": "Built churn models and NLP classifiers; ran A/B tests for product teams.",
            },
            {
                "title": "Data Analyst",
                "company": "Kite Retail",
                "start": "2019",
                "end": "2021",
                "description": "Created Tableau dashboards and SQL reporting for commercial teams.",
            },
        ],
        "apply_to": "Data Scientist",
    },
    {
        "email": "marcus@talentmatch.ai",
        "name": "Marcus Chen",
        "headline": "Digital Marketing Manager",
        "location": "Manchester, UK",
        "bio": "Growth marketer with B2B SaaS experience across SEO, content and lifecycle campaigns.",
        "manual_skills": ["Leadership", "Presentation Skills"],
        "cv_text": (
            "Marcus Chen - Digital Marketing Manager\n"
            "Manchester, United Kingdom\n\n"
            "Summary: Growth marketer with five years of B2B SaaS experience.\n\n"
            "Experience:\n"
            "2020 - Present Digital Marketing Manager at Loop Software\n"
            "2018 - 2020 Marketing Specialist at Beacon Media\n\n"
            "Skills: Digital Marketing, SEO, Content Marketing, Social Media Marketing, "
            "Email Marketing, HubSpot, Copywriting, Data Analysis, Communication\n\n"
            "Education:\n"
            "Bachelor of Arts in Marketing, University of Manchester, 2018"
        ),
        "job_titles": ["Digital Marketing Manager", "Marketing Specialist"],
        "education": [
            {"degree": "BA Marketing", "institution": "University of Manchester", "year": "2018"}
        ],
        "experience": [
            {
                "title": "Digital Marketing Manager",
                "company": "Loop Software",
                "start": "2020",
                "end": "Present",
                "description": "Owned SEO, content and email programs; grew organic pipeline by 60%.",
            },
            {
                "title": "Marketing Specialist",
                "company": "Beacon Media",
                "start": "2018",
                "end": "2020",
                "description": "Ran social campaigns and HubSpot lifecycle automation.",
            },
        ],
        "apply_to": "Digital Marketing Manager",
    },
]


def _user(db, email: str, full_name: str, role: UserRole) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        if not existing.email_verified:
            existing.email_verified = True
            existing.email_verified_at = datetime.now(timezone.utc)
        return existing
    user = User(
        full_name=full_name,
        email=email,
        hashed_password=hash_password(DEMO_PASSWORD),
        role=role,
        email_verified=True,
        email_verified_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.flush()
    return user


def load_seed_data() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        employer_users: dict[str, User] = {}
        for company in ("Northstar Labs", "Cobalt Health"):
            email = f"employer+{company.split()[0].lower()}@talentmatch.ai"
            user = _user(db, email, f"{company} Hiring Team", UserRole.EMPLOYER)
            if user.employer_profile is None:
                user.employer_profile = EmployerProfile(
                    company_name=company,
                    location="Remote / Europe",
                    website="https://example.com",
                    description=f"{company} is a demo employer on TalentMatch AI.",
                )
            employer_users[company] = user
        db.flush()

        for job_data in JOBS:
            existing = db.scalar(
                select(Job).where(
                    Job.title == job_data["title"],
                    Job.employer_id == employer_users[job_data["employer"]].employer_profile.id,
                )
            )
            if existing:
                continue
            skills = normalize_skills(job_data["required_skills"])
            description = job_data["description"]
            db.add(
                Job(
                    employer_id=employer_users[job_data["employer"]].employer_profile.id,
                    title=job_data["title"],
                    description=description,
                    required_skills=skills,
                    location=job_data["location"],
                    job_type=job_data["job_type"],
                    salary_min=job_data["salary_min"],
                    salary_max=job_data["salary_max"],
                    currency=job_data["currency"],
                    deadline=date.today() + timedelta(days=job_data["days"]),
                    status="open",
                    embedding=embedder.embed(
                        job_embedding_text(job_data["title"], description, skills, job_data["location"])
                    ),
                )
            )
        db.flush()

        for course_data in COURSES:
            if db.scalar(select(Course).where(Course.title == course_data["title"])):
                continue
            payload = dict(course_data)
            payload["skills"] = normalize_skills(payload["skills"])
            db.add(Course(**payload))
        db.flush()

        for seeker_data in SEEKERS:
            user = _user(db, seeker_data["email"], seeker_data["name"], UserRole.JOB_SEEKER)
            if user.seeker_profile is None:
                user.seeker_profile = JobSeekerProfile(
                    headline=seeker_data["headline"],
                    location=seeker_data["location"],
                    bio=seeker_data["bio"],
                    manual_skills=normalize_skills(seeker_data["manual_skills"]),
                )
                db.flush()
            profile = user.seeker_profile
            if not profile.cvs:
                skills = normalize_skills(extract_skills(seeker_data["cv_text"]))
                db.add(
                    CV(
                        seeker_id=profile.id,
                        filename=f"{seeker_data['name'].lower().replace(' ', '_')}_cv.docx",
                        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        file_path=None,
                        size_bytes=len(seeker_data["cv_text"].encode("utf-8")),
                        raw_text=seeker_data["cv_text"],
                        summary=seeker_data["bio"],
                        skills=skills,
                        education=seeker_data["education"],
                        experience=seeker_data["experience"],
                        job_titles=seeker_data["job_titles"],
                        embedding=embedder.embed(
                            cv_embedding_text(
                                skills,
                                seeker_data["job_titles"],
                                seeker_data["bio"],
                                seeker_data["cv_text"],
                            )
                        ),
                        is_active=True,
                    )
                )
        db.flush()

        priya = db.scalar(select(User).where(User.email == "priya@talentmatch.ai"))
        data_job = db.scalar(select(Job).where(Job.title == "Data Scientist"))
        if priya and priya.seeker_profile and data_job:
            existing = db.scalar(
                select(Application).where(
                    Application.job_id == data_job.id,
                    Application.seeker_id == priya.seeker_profile.id,
                )
            )
            if not existing:
                profile = priya.seeker_profile
                cv = next((item for item in profile.cvs if item.is_active), None)
                from app.services.matching import compute_match

                match = compute_match(
                    cv.embedding if cv else [],
                    data_job.embedding,
                    cv.skills if cv else [],
                    data_job.required_skills,
                )
                db.add(
                    Application(
                        job_id=data_job.id,
                        seeker_id=profile.id,
                        cv_id=cv.id if cv else None,
                        cover_note="Excited about the experimentation and NLP focus of this role.",
                        match_score=match["score"],
                        matched_skills=match["matched_skills"],
                        missing_skills=match["missing_skills"],
                    )
                )

        db.commit()

        from app.services.course_advisor import index_courses

        indexed = index_courses(db, reset=True)
        print(f"Seeded {len(COURSES)} courses, {len(JOBS)} jobs and {len(SEEKERS)} seekers.")
        print(f"Indexed {indexed} courses in the vector store.")
        print("Demo accounts (password: Password123!):")
        print("  Job seeker:  alex@talentmatch.ai")
        print("  Job seeker:  priya@talentmatch.ai")
        print("  Employer:    employer+northstar@talentmatch.ai")
        print("  Employer:    employer+cobalt@talentmatch.ai")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed TalentMatch AI demo data")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables first")
    args = parser.parse_args()

    if args.reset:
        confirm = input("This deletes all TalentMatch data. Type 'yes' to continue: ")
        if confirm.strip().lower() != "yes":
            print("Aborted.")
            raise SystemExit(1)
        Base.metadata.drop_all(bind=engine)

    load_seed_data()
