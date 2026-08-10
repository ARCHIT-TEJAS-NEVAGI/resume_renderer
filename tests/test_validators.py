import pytest

from app.schemas.models import GenerateRequest
from app.utils.validators import validate_resume_content, validate_template_name
from tests.helpers import full_resume_payload


def test_valid_template_names():
    for name in ("classic", "modern", "executive"):
        assert validate_template_name(name) == name


def test_invalid_template_name_raises():
    with pytest.raises(ValueError, match="Unsupported template"):
        validate_template_name("fancy")


def test_validate_resume_content_ok():
    request = GenerateRequest(**full_resume_payload())
    validate_resume_content(request.resume)  # should not raise
