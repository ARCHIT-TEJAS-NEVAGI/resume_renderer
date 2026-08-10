"""POST /generate/pdf — render a resume to an A4 PDF.

Pipeline: validate request -> render HTML -> load into Playwright Chromium ->
print to PDF -> return ``application/pdf`` bytes.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from loguru import logger

from app.schemas.models import GenerateRequest
from app.services.html_renderer import render_html
from app.services.pdf_renderer import PDFRenderError, pdf_renderer

router = APIRouter(tags=["generation"])


@router.post(
    "/generate/pdf",
    summary="Render a resume to an A4 PDF",
    description=(
        "Renders the resume HTML with the selected template and converts it "
        "to a print-ready A4 PDF via Playwright Chromium. The response is a "
        "binary PDF file."
    ),
    responses={
        200: {"description": "PDF document (application/pdf)"},
        400: {"description": "Unsupported template or invalid resume content"},
        422: {"description": "Request body failed schema validation"},
        500: {"description": "HTML or PDF rendering failed"},
    },
)
async def generate_pdf(payload: GenerateRequest) -> Response:
    try:
        html = render_html(payload)
        pdf_bytes = await pdf_renderer.render_pdf(html)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PDFRenderError as exc:
        logger.error("PDF rendering failed: {}", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception:
        logger.exception("Unexpected error while rendering resume to PDF")
        raise HTTPException(
            status_code=500,
            detail="Internal server error while rendering PDF.",
        )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="resume.pdf"',
            "Cache-Control": "no-store",
        },
    )
