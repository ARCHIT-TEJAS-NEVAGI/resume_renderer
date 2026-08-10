"""POST /generate/html — render a resume to a standalone HTML document."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from loguru import logger

from app.schemas.models import GenerateRequest
from app.services.html_renderer import render_html

router = APIRouter(tags=["generation"])


@router.post(
    "/generate/html",
    summary="Render a resume to a standalone HTML document",
    description=(
        "Accepts a verified resume JSON document and a template name and "
        "returns a complete, self-contained HTML document (DOCTYPE, head, "
        "inline styles, semantic body). Empty sections are hidden. "
        "The resume content is never modified."
    ),
    response_class=HTMLResponse,
    responses={
        200: {"description": "Full standalone HTML document"},
        400: {"description": "Unsupported template or invalid resume content"},
        422: {"description": "Request body failed schema validation"},
    },
)
def generate_html(payload: GenerateRequest) -> HTMLResponse:
    try:
        html = render_html(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected error while rendering resume to HTML")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while rendering HTML.",
        )
    return HTMLResponse(content=html, media_type="text/html; charset=utf-8")
