import pytest
from pydantic import ValidationError

from app.schemas.models import GenerateRequest
from tests.helpers import full_resume_payload


def test_full_payload_parses():
    request = GenerateRequest(**full_resume_payload())
    assert request.template == "classic"
    assert request.resume.contact.name == "Alex Doe"
    assert request.resume.contact.title == "Senior Software Engineer"
    assert len(request.resume.experience) == 2
    assert len(request.resume.languages) == 2
    assert len(request.resume.additional_sections) == 1


def test_default_template_is_classic():
    payload = full_resume_payload()
    payload.pop("template")
    request = GenerateRequest(**payload)
    assert request.template == "classic"


def test_skills_accepts_strings_and_objects():
    payload = full_resume_payload()
    payload["resume"]["skills"] = [
        {"name": "Python", "level": 9},
        "AWS",
        {"name": "SQL"},
    ]
    request = GenerateRequest(**payload)
    # Skill ratings are intentionally dropped.
    assert request.resume.skills == ["Python", "AWS", "SQL"]


def test_summary_accepts_list():
    payload = full_resume_payload()
    payload["resume"]["summary"] = ["First line.", "Second line."]
    request = GenerateRequest(**payload)
    assert request.resume.summary == "First line.\nSecond line."


def test_nested_date_range_maps_to_flat_fields():
    payload = full_resume_payload()
    payload["resume"]["experience"][0] = {
        "title": "Intern",
        "company": "Startup",
        "date_range": {"start": "2020-06", "end": "2020-09"},
    }
    request = GenerateRequest(**payload)
    entry = request.resume.experience[0]
    assert entry.start == "2020-06"
    assert entry.end == "2020-09"


def test_current_flag_round_trips():
    payload = full_resume_payload()
    payload["resume"]["experience"][0]["current"] = True
    request = GenerateRequest(**payload)
    assert request.resume.experience[0].current is True


def test_extra_fields_are_ignored():
    payload = full_resume_payload()
    payload["resume"]["unknown_section"] = {"whatever": 1}
    payload["resume"]["contact"]["age"] = 30
    request = GenerateRequest(**payload)
    assert not hasattr(request.resume, "unknown_section")
    assert not hasattr(request.resume.contact, "age")


def test_missing_contact_name_rejected():
    with pytest.raises(ValidationError):
        GenerateRequest(template="classic", resume={"contact": {}})


def test_missing_contact_rejected():
    with pytest.raises(ValidationError):
        GenerateRequest(template="classic", resume={})


def test_whitespace_only_name_rejected():
    with pytest.raises(ValidationError):
        GenerateRequest(template="classic", resume={"contact": {"name": "   "}})
