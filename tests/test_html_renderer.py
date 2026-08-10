from app.schemas.models import GenerateRequest
from app.services.html_renderer import build_context, render_html
from tests.helpers import full_resume_payload, minimal_resume_payload


def test_build_context_contact_lines():
    request = GenerateRequest(**full_resume_payload())
    context = build_context(request.resume)
    assert context["contact"]["name"] == "Alex Doe"
    assert context["contact"]["title"] == "Senior Software Engineer"
    assert context["contact"]["lines"] == [
        "alex.doe@example.com",
        "+1 555 010 0199",
        "London, UK",
        "https://alexdoe.dev",
        "linkedin.com/in/alexdoe",
        "github.com/alexdoe",
        "Portfolio",
    ]


def test_build_context_sections():
    request = GenerateRequest(**full_resume_payload())
    context = build_context(request.resume)

    assert context["summary"] == [
        "Distributed systems engineer with ten years of experience.",
        "Focused on reliability and observability.",
    ]
    assert context["skills"] == ["Python", "FastAPI", "PostgreSQL", "AWS", "Kubernetes"]

    assert context["experience"][0]["title"] == "Staff Engineer"
    assert context["experience"][0]["meta"] == "Acme Corp — Remote"
    assert context["experience"][0]["dates"] == "2021-01 – Present"
    assert context["experience"][0]["bullets"] == [
        "Led a 12-person platform team.",
        "Reduced p99 latency by 40%.",
    ]

    # Description-only entry becomes bullets; no invented paragraphs.
    assert context["experience"][1]["bullets"] == [
        "Owned the payments pipeline.",
        "Built the billing microservice.",
    ]
    assert context["experience"][1]["paragraphs"] is None

    assert context["projects"][0]["title"] == "resume-renderer"
    assert context["projects"][0]["tech"] == "FastAPI, Playwright"

    assert context["education"][0]["title"] == "University of London"
    assert context["education"][0]["meta"] == (
        "MSc — Computer Science — Distinction — London, UK"
    )

    assert context["languages"] == [
        {"name": "English", "proficiency": "Native"},
        {"name": "German", "proficiency": "Professional"},
    ]
    assert context["publications"][0]["meta"] == "Alex Doe, Jane Smith; Example Journal"
    assert context["additional_sections"] == [
        {
            "title": "Speaking",
            "bullets": ["Guest lecture on observability at ExampleConf 2024."],
        }
    ]


def test_empty_sections_are_hidden():
    request = GenerateRequest(**full_resume_payload())
    context = build_context(request.resume)
    assert context["certifications"] is None
    assert context["volunteer"] is None


def test_build_context_volunteer_entry_with_title():
    """Volunteer entries use ``title`` (not ``role``), matching the optimizer
    prompt and the VolunteerEntry model. Regression: html_renderer previously
    read ``raw.role`` and crashed with AttributeError."""
    payload = full_resume_payload()
    payload["resume"]["volunteer"] = [
        {
            "organization": "Code Tutors",
            "title": "Mentor",
            "start": "2020-01",
            "end": "Present",
            "bullets": ["Taught web development to 30 students."],
        }
    ]
    request = GenerateRequest(**payload)
    context = build_context(request.resume)
    assert context["volunteer"] == [
        {
            "title": "Mentor",
            "meta": "Code Tutors",
            "dates": "2020-01 – Present",
            "tech": None,
            "bullets": ["Taught web development to 30 students."],
            "paragraphs": None,
        }
    ]


def test_render_html_volunteer_with_title():
    payload = full_resume_payload()
    payload["resume"]["volunteer"] = [
        {
            "organization": "Code Tutors",
            "title": "Mentor",
            "start": "2020-01",
            "end": "Present",
            "bullets": ["Taught web development to 30 students."],
        }
    ]
    html = render_html(GenerateRequest(**payload))
    assert "Code Tutors" in html
    assert "Mentor" in html


def test_render_html_full_document():
    request = GenerateRequest(**full_resume_payload("classic"))
    html = render_html(request)
    assert html.lower().startswith("<!doctype html>")
    assert "<html" in html.lower()
    assert "<head>" in html.lower()
    assert "<body>" in html.lower()
    assert "Alex Doe" in html
    assert "Professional Summary" in html
    assert "Staff Engineer" in html
    assert "Acme Corp" in html
    assert "Speaking" in html


def test_render_html_hides_empty_sections():
    request = GenerateRequest(**minimal_resume_payload("modern"))
    html = render_html(request)
    assert "Jane Q. Engineer" in html
    for section in (
        "Professional Summary",
        "Skills",
        "Experience",
        "Education",
        "Certifications",
        "Languages",
        "Awards",
        "Publications",
        "Volunteer",
    ):
        assert section not in html


def test_render_html_escapes_user_content():
    payload = minimal_resume_payload()
    payload["resume"]["contact"]["name"] = "<b>Jane</b>"
    payload["resume"]["summary"] = "<script>alert('xss')</script>"
    request = GenerateRequest(**payload)
    html = render_html(request)
    assert "<script>alert" not in html
    assert "<b>Jane</b>" not in html
    assert "&lt;script&gt;" in html
    assert "&lt;b&gt;Jane&lt;/b&gt;" in html


def test_render_html_is_ats_friendly_markup():
    """No tables, images, icons, SVG, or skill ratings in any template."""
    for template in ("classic", "modern", "executive"):
        request = GenerateRequest(**full_resume_payload(template))
        html = render_html(request)
        assert "<table" not in html
        assert "<img" not in html
        assert "<svg" not in html
        assert "font-awesome" not in html.lower()
        assert "skill rating" not in html.lower()


def test_render_html_unsupported_template_raises():
    payload = full_resume_payload("fancy")
    request = GenerateRequest(**payload)
    try:
        render_html(request)
    except ValueError as exc:
        assert "Unsupported template" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unsupported template")
