from pathlib import Path

import pytest

from app.config import TEMPLATES_DIR, get_settings
from app.services.template_manager import template_manager


def minimal_context() -> dict:
    return {
        "contact": {"name": "Test Candidate", "title": None, "lines": []},
        "summary": None,
        "skills": None,
        "experience": None,
        "projects": None,
        "education": None,
        "certifications": None,
        "languages": None,
        "awards": None,
        "volunteer": None,
        "publications": None,
        "additional_sections": None,
    }


def test_supported_templates_exist_on_disk():
    settings = get_settings()
    for name in settings.template_list:
        template_path = TEMPLATES_DIR / f"{name}.html"
        assert template_path.exists(), f"Missing template file: {template_path}"


def test_every_template_renders_a_full_document():
    settings = get_settings()
    for name in settings.template_list:
        html = template_manager.render(name, minimal_context())
        assert html.lower().startswith("<!doctype html>")
        assert "Test Candidate" in html
        assert ".section-title" in html  # shared base CSS is inlined


def test_unknown_template_raises():
    with pytest.raises(ValueError, match="Unsupported template"):
        template_manager.render("not-a-template", minimal_context())


def test_template_files_are_not_placeholders():
    settings = get_settings()
    for name in settings.template_list:
        content = (TEMPLATES_DIR / f"{name}.html").read_text(encoding="utf-8")
        assert "TODO" not in content
        assert "<!-- demo" not in content.lower()
