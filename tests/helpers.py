"""Shared fixtures for the test suite."""


def full_resume_payload(template: str = "classic") -> dict:
    """A realistic resume exercising every section except the intentionally
    empty ones (certifications, volunteer), which must be hidden."""
    return {
        "template": template,
        "resume": {
            "contact": {
                "name": "Alex Doe",
                "title": "Senior Software Engineer",
                "email": "alex.doe@example.com",
                "phone": "+1 555 010 0199",
                "location": "London, UK",
                "website": "https://alexdoe.dev",
                "linkedin": "linkedin.com/in/alexdoe",
                "github": "github.com/alexdoe",
                "links": [
                    {"label": "Portfolio", "url": "https://portfolio.alexdoe.dev"}
                ],
            },
            "summary": (
                "Distributed systems engineer with ten years of experience.\n\n"
                "Focused on reliability and observability."
            ),
            "skills": ["Python", "FastAPI", "PostgreSQL", "AWS", "Kubernetes"],
            "experience": [
                {
                    "title": "Staff Engineer",
                    "company": "Acme Corp",
                    "location": "Remote",
                    "start": "2021-01",
                    "end": "Present",
                    "bullets": [
                        "Led a 12-person platform team.",
                        "Reduced p99 latency by 40%.",
                    ],
                },
                {
                    "title": "Senior Engineer",
                    "company": "Globex",
                    "start": "2017-06",
                    "end": "2020-12",
                    "description": (
                        "Owned the payments pipeline.\n"
                        "Built the billing microservice."
                    ),
                },
            ],
            "projects": [
                {
                    "name": "resume-renderer",
                    "role": "Creator",
                    "url": "https://github.com/example/resume-renderer",
                    "technologies": ["FastAPI", "Playwright"],
                    "description": "A production-grade resume rendering service.",
                }
            ],
            "education": [
                {
                    "institution": "University of London",
                    "degree": "MSc",
                    "field": "Computer Science",
                    "location": "London, UK",
                    "start": "2013",
                    "end": "2015",
                    "gpa": "Distinction",
                }
            ],
            "certifications": [],
            "languages": [
                {"name": "English", "proficiency": "Native"},
                {"name": "German", "proficiency": "Professional"},
            ],
            "awards": [
                {
                    "title": "Engineering Excellence Award",
                    "issuer": "Acme Corp",
                    "date": "2023",
                }
            ],
            "volunteer": [],
            "publications": [
                {
                    "title": "Reliable Systems at Scale",
                    "venue": "Example Journal",
                    "authors": ["Alex Doe", "Jane Smith"],
                    "date": "2024",
                }
            ],
            "additional_sections": [
                {
                    "title": "Speaking",
                    "items": [
                        "Guest lecture on observability at ExampleConf 2024."
                    ],
                }
            ],
        },
    }


def minimal_resume_payload(template: str = "classic") -> dict:
    """A resume with only a contact name — every section must be hidden."""
    return {
        "template": template,
        "resume": {"contact": {"name": "Jane Q. Engineer", "email": "jane@example.com"}},
    }
