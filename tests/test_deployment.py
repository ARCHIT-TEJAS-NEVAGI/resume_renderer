"""Deployment-focused test.

Every other PDF test (``test_pdf_renderer.py``, ``test_api.py``) mocks the
Playwright driver, so the suite passes even when no browser is installed.
That is fine for unit tests, but it cannot catch the one failure that matters
on Render: Chromium not actually being available at runtime. A healthy FastAPI
``/health`` check says nothing about whether ``page.pdf()`` works.

This single test launches the *real* installed Chromium through the same
``PDFRenderer`` used by ``POST /generate/pdf`` and asserts it can print a
document to real PDF bytes — mirroring what ``playwright install --with-deps
chromium`` should have made available in the build image.

It skips automatically when Chromium is not installed locally, so a bare
``pytest`` run remains a pure unit-test run for developers who have not run
``playwright install chromium``.
"""
import asyncio

import pytest

pytest.importorskip("playwright")

from app.services.pdf_renderer import PDFRenderer  # noqa: E402

_MINIMAL_HTML = (
    "<!DOCTYPE html><html><head><meta charset='utf-8'>"
    "<style>@page{size:A4;margin:1cm}body{font-family:sans-serif}</style>"
    "</head><body><h1>Deploy probe</h1></body></html>"
)


def test_installed_chromium_renders_a_real_pdf():
    """The configured headless Chromium can launch and print PDF bytes."""

    async def _probe() -> bytes:
        renderer = PDFRenderer()
        try:
            return await renderer.render_pdf(_MINIMAL_HTML)
        finally:
            await renderer.close()

    try:
        pdf = asyncio.run(_probe())
    except Exception as exc:  # browser missing locally -> skip, not fail
        message = str(exc).lower()
        if "executable doesn't exist" in message or "not installed" in message:
            pytest.skip(
                "Chromium is not installed locally; run `playwright install "
                f"chromium` to enable this deployment probe. (reason: {exc})"
            )
        raise

    assert pdf.startswith(b"%PDF"), "Chromium did not return a real PDF document."
