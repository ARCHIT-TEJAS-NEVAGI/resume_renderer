"""Validation helpers for render requests.

These enforce the contract of this service:
- the requested template must be one of the supported templates;
- the resume must contain at least a contact name.

They only validate; they never rewrite, verify, or enrich resume content.
"""
from app.config import get_settings
from app.schemas.models import Resume


def validate_template_name(template: str) -> str:
    """Return the template name if supported, else raise ``ValueError``."""
    settings = get_settings()
    if template not in settings.template_list:
        supported = ", ".join(settings.template_list)
        raise ValueError(
            f"Unsupported template '{template}'. "
            f"Supported templates: {supported}."
        )
    return template


def validate_resume_content(resume: Resume) -> None:
    """Raise ``ValueError`` if the resume has no usable contact name."""
    contact = resume.contact
    if contact is None or not contact.name or not contact.name.strip():
        raise ValueError(
            "The resume must include a contact with a non-empty name."
        )
