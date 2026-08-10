"""HTML rendering.

Builds the template context from a validated resume and delegates the actual
markup to the template manager. This layer owns all presentation decisions:

- which fields belong in the contact line;
- how date ranges are displayed (using only explicitly provided values);
- how multi-line descriptions are split into bullets/paragraphs;
- hiding sections that have no content.

Resume wording is never altered and no values are inferred.
"""
import re
from typing import Any, Callable, Optional

from app.schemas.models import GenerateRequest, Resume
from app.services.template_manager import template_manager
from app.utils.validators import validate_resume_content, validate_template_name


def render_html(request: GenerateRequest) -> str:
    """Render a verified resume into a complete standalone HTML document."""
    validate_resume_content(request.resume)
    template_name = validate_template_name(request.template)
    context = build_context(request.resume)
    return template_manager.render(template_name, context)


# --------------------------------------------------------------------------
# Context building
# --------------------------------------------------------------------------

def build_context(resume: Resume) -> dict[str, Any]:
    """Produce the normalized template context (empty sections -> None)."""
    return {
        "contact": _build_contact(resume.contact),
        "summary": _paragraphs(resume.summary),
        "skills": _clean_list(resume.skills) or None,
        "experience": _render_entries(resume.experience, _experience_entry),
        "projects": _render_entries(resume.projects, _project_entry),
        "education": _render_entries(resume.education, _education_entry),
        "certifications": _render_detail_items(
            resume.certifications, _certification_item
        ),
        "languages": _render_languages(resume.languages) or None,
        "awards": _render_detail_items(resume.awards, _award_item),
        "volunteer": _render_entries(resume.volunteer, _volunteer_entry),
        "publications": _render_detail_items(
            resume.publications, _publication_item
        ),
        "additional_sections": _render_additional_sections(
            resume.additional_sections
        )
        or None,
    }


# --------------------------------------------------------------------------
# Low-level helpers
# --------------------------------------------------------------------------

def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean_list(values) -> list[str]:
    return [item for item in (_clean(v) for v in (values or [])) if item]


def _split_lines(text: Optional[str]) -> list[str]:
    return [line for line in (text or "").splitlines() if line.strip()]


def _paragraphs(text: Optional[str]) -> Optional[list[str]]:
    cleaned = _clean(text)
    if not cleaned:
        return None
    return [
        paragraph.strip()
        for paragraph in re.split(r"\n\s*\n", cleaned)
        if paragraph.strip()
    ] or None


def _non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple, dict)):
        return bool(value)
    return bool(str(value).strip())


def _has_value(mapping: dict) -> bool:
    return any(_non_empty(v) for v in mapping.values())


def _join_meta(*parts: Optional[str]) -> Optional[str]:
    joined = [part for part in (_clean(p) for p in parts) if part]
    return " — ".join(joined) if joined else None


def _dates(start, end, current: bool) -> Optional[str]:
    """Display a date range using only explicitly provided values.

    ``current=True`` is rendered as ``Present``; no end date is ever invented.
    """
    start_c = _clean(start)
    end_c = _clean(end)
    if not start_c and not end_c and not current:
        return None
    left = start_c or ""
    right = end_c or ("Present" if current else "")
    if left and right:
        return f"{left} – {right}"
    return left or right or None


def _entry_body(entry) -> tuple[list[str], Optional[list[str]]]:
    """Normalize description/bullets into ``(bullets, paragraphs)``.

    Explicit bullets win; a bare description is split into bullet lines.
    """
    bullets = _clean_list(getattr(entry, "bullets", None))
    description = _clean(getattr(entry, "description", None))
    paragraphs = None
    if not bullets and description:
        bullets = _split_lines(description)
    elif bullets and description:
        paragraphs = _split_lines(description) or None
    return bullets, paragraphs


# --------------------------------------------------------------------------
# Section normalizers
# --------------------------------------------------------------------------

def _build_contact(contact) -> dict:
    lines = []
    for value in (
        contact.email,
        contact.phone,
        contact.location,
        contact.website,
        contact.linkedin,
        contact.github,
    ):
        cleaned = _clean(value)
        if cleaned:
            lines.append(cleaned)
    for link in contact.links or []:
        url = _clean(link.url)
        if url:
            lines.append(_clean(link.label) or url)
    return {
        "name": _clean(contact.name) or "",
        "title": _clean(contact.title),
        "lines": lines,
    }


def _render_entries(raw_items, mapper: Callable) -> Optional[list[dict]]:
    entries = [entry for raw in (raw_items or []) if (entry := mapper(raw))]
    return entries or None


def _entry_shape(title, meta, dates, tech, bullets, paragraphs) -> Optional[dict]:
    entry = {
        "title": title,
        "meta": meta,
        "dates": dates,
        "tech": tech,
        "bullets": bullets,
        "paragraphs": paragraphs,
    }
    return entry if _has_value(entry) else None


def _experience_entry(raw) -> Optional[dict]:
    bullets, paragraphs = _entry_body(raw)
    return _entry_shape(
        title=_clean(raw.title),
        meta=_join_meta(raw.company, raw.location),
        dates=_dates(raw.start, raw.end, raw.current),
        tech=None,
        bullets=bullets,
        paragraphs=paragraphs,
    )


def _project_entry(raw) -> Optional[dict]:
    bullets, paragraphs = _entry_body(raw)
    tech = ", ".join(_clean_list(raw.technologies)) or None
    return _entry_shape(
        title=_clean(raw.name),
        meta=_join_meta(raw.role, raw.url),
        dates=_dates(raw.start, raw.end, raw.current),
        tech=tech,
        bullets=bullets,
        paragraphs=paragraphs,
    )


def _education_entry(raw) -> Optional[dict]:
    bullets, paragraphs = _entry_body(raw)
    return _entry_shape(
        title=_clean(raw.institution),
        meta=_join_meta(raw.degree, raw.field, raw.gpa, raw.location),
        dates=_dates(raw.start, raw.end, raw.current),
        tech=None,
        bullets=bullets,
        paragraphs=paragraphs,
    )


def _volunteer_entry(raw) -> Optional[dict]:
    bullets, paragraphs = _entry_body(raw)
    return _entry_shape(
        title=_clean(raw.title),
        meta=_join_meta(raw.organization, raw.location),
        dates=_dates(raw.start, raw.end, raw.current),
        tech=None,
        bullets=bullets,
        paragraphs=paragraphs,
    )


def _render_detail_items(raw_items, mapper: Callable) -> Optional[list[dict]]:
    items = [item for raw in (raw_items or []) if (item := mapper(raw))]
    return items or None


def _detail_shape(title, meta, dates, url, description) -> Optional[dict]:
    item = {
        "title": title,
        "meta": meta,
        "dates": dates,
        "url": url,
        "description": description,
    }
    return item if _has_value(item) else None


def _certification_item(raw) -> Optional[dict]:
    return _detail_shape(
        title=_clean(raw.name),
        meta=_clean(raw.issuer),
        dates=_clean(raw.date),
        url=_clean(raw.url),
        description=None,
    )


def _award_item(raw) -> Optional[dict]:
    return _detail_shape(
        title=_clean(raw.title),
        meta=_clean(raw.issuer),
        dates=_clean(raw.date),
        url=None,
        description=_clean(raw.description),
    )


def _publication_item(raw) -> Optional[dict]:
    authors = ", ".join(_clean_list(raw.authors)) or None
    meta = "; ".join(part for part in (authors, _clean(raw.venue)) if part) or None
    return _detail_shape(
        title=_clean(raw.title),
        meta=meta,
        dates=_clean(raw.date),
        url=_clean(raw.url),
        description=_clean(raw.description),
    )


def _render_languages(raw_items) -> Optional[list[dict]]:
    languages = []
    for raw in raw_items or []:
        name = _clean(raw.name)
        if name:
            languages.append(
                {"name": name, "proficiency": _clean(raw.proficiency)}
            )
    return languages or None


def _render_additional_sections(raw_sections) -> Optional[list[dict]]:
    sections = []
    for raw in raw_sections or []:
        items = _clean_list(raw.items)
        if not items and raw.description:
            items = _split_lines(raw.description)
        if not items:
            continue
        # Key is "bullets" (not "items") so Jinja attribute lookup does not
        # collide with dict.items.
        sections.append({"title": raw.title, "bullets": items})
    return sections or None
