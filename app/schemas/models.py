"""Request schemas for the resume-renderer service.

These models define the contract this service accepts: a verified resume
document plus the name of the template to render. Fields map 1:1 to the
resume sections produced by the resume-parser pipeline.

Notes:
- Unknown/extra fields are ignored so the service stays forward-compatible
  with the surrounding ecosystem without silently accepting typos in the
  fields it does know.
- String whitespace is stripped during validation; the wording of the resume
  itself is never altered.
- Skill ratings are intentionally not modeled here: templates are ATS-friendly
  and never render skill ratings.
"""
from typing import List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class BaseResumeModel(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        validate_default=True,
    )


class Link(BaseResumeModel):
    label: Optional[str] = None
    url: Optional[str] = None


class ContactInfo(BaseResumeModel):
    name: str = Field(min_length=1, description="Full name of the candidate.")
    title: Optional[str] = Field(default=None, description="Headline or current job title.")
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    links: List[Link] = Field(default_factory=list, description="Additional labeled links.")


class DateRange(BaseResumeModel):
    """Optional nested date range; mapped onto the flat date fields below."""

    start: Optional[str] = None
    end: Optional[str] = None
    current: bool = False


class EntryModel(BaseResumeModel):
    """Common fields shared by experience-style sections."""

    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    current: bool = False
    date_range: Optional[DateRange] = None
    description: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _apply_date_range(self) -> "EntryModel":
        if self.date_range is not None:
            self.start = self.start or self.date_range.start
            self.end = self.end or self.date_range.end
            self.current = self.current or self.date_range.current
        return self


class ExperienceEntry(EntryModel):
    pass


class VolunteerEntry(EntryModel):
    organization: Optional[str] = None


class ProjectEntry(BaseResumeModel):
    name: Optional[str] = None
    role: Optional[str] = None
    url: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    start: Optional[str] = None
    end: Optional[str] = None
    current: bool = False
    date_range: Optional[DateRange] = None
    description: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)

    @field_validator("technologies", mode="before")
    @classmethod
    def _coerce_technologies(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def _apply_date_range(self) -> "ProjectEntry":
        if self.date_range is not None:
            self.start = self.start or self.date_range.start
            self.end = self.end or self.date_range.end
            self.current = self.current or self.date_range.current
        return self


class EducationEntry(BaseResumeModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    location: Optional[str] = None
    gpa: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    current: bool = False
    date_range: Optional[DateRange] = None
    description: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _apply_date_range(self) -> "EducationEntry":
        if self.date_range is not None:
            self.start = self.start or self.date_range.start
            self.end = self.end or self.date_range.end
            self.current = self.current or self.date_range.current
        return self


class CertificationEntry(BaseResumeModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None


class LanguageEntry(BaseResumeModel):
    name: Optional[str] = None
    proficiency: Optional[str] = None


class AwardEntry(BaseResumeModel):
    title: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = None


class PublicationEntry(BaseResumeModel):
    title: Optional[str] = None
    venue: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    date: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None

    @field_validator("authors", mode="before")
    @classmethod
    def _coerce_authors(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value


class AdditionalSection(BaseResumeModel):
    title: str = Field(min_length=1)
    items: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class Resume(BaseResumeModel):
    """The verified resume document to render."""

    contact: ContactInfo
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceEntry] = Field(default_factory=list)
    projects: List[ProjectEntry] = Field(default_factory=list)
    education: List[EducationEntry] = Field(default_factory=list)
    certifications: List[CertificationEntry] = Field(default_factory=list)
    languages: List[LanguageEntry] = Field(default_factory=list)
    awards: List[AwardEntry] = Field(default_factory=list)
    volunteer: List[VolunteerEntry] = Field(default_factory=list)
    publications: List[PublicationEntry] = Field(default_factory=list)
    additional_sections: List[AdditionalSection] = Field(default_factory=list)

    @field_validator("skills", mode="before")
    @classmethod
    def _coerce_skills(cls, value):
        """Accept plain strings or objects with a ``name`` field.

        Ratings (e.g. ``level``) are intentionally dropped: skill ratings are
        never rendered.
        """
        if value is None:
            return []
        coerced = []
        for item in value:
            if isinstance(item, str):
                coerced.append(item)
            else:
                name = item.get("name") if isinstance(item, dict) else getattr(item, "name", None)
                if name:
                    coerced.append(str(name))
        return coerced

    @field_validator("summary", mode="before")
    @classmethod
    def _coerce_summary(cls, value):
        if isinstance(value, list):
            return "\n".join(str(part) for part in value if part is not None)
        return value


class GenerateRequest(BaseResumeModel):
    """POST /generate/html and POST /generate/pdf request body."""

    resume: Resume
    template: str = Field(
        default="classic",
        description="Template name. Supported: classic, modern, executive.",
    )
