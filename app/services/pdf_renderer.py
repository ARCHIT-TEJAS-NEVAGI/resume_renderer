"""PDF rendering via Playwright + Chromium.

The generated PDF reuses the same standalone HTML produced by
``html_renderer``, so HTML and PDF output are always identical in layout.

A single Chromium browser is launched lazily and reused across requests;
page.pdf() only works in headless Chromium, which is what we use.
"""
import asyncio

from loguru import logger
from playwright.async_api import async_playwright

from app.config import get_settings


class PDFRenderError(RuntimeError):
    """Raised when a document cannot be converted to PDF."""


class PDFRenderer:
    """Converts standalone HTML documents into PDF bytes."""

    def __init__(self) -> None:
        self._playwright = None
        self._browser = None
        self._lock = asyncio.Lock()

    async def render_pdf(self, html: str) -> bytes:
        """Render an HTML document string into PDF bytes."""
        settings = get_settings()
        browser = await self._get_browser()
        page = await browser.new_page()
        try:
            await page.set_content(
                html,
                wait_until="load",
                timeout=settings.playwright_render_timeout_ms,
            )
            pdf = await page.pdf(
                format=settings.pdf_format,
                print_background=settings.pdf_print_background,
                prefer_css_page_size=settings.pdf_prefer_css_page_size,
            )
        except Exception as exc:
            raise PDFRenderError(f"Failed to generate PDF: {exc}") from exc
        finally:
            await page.close()

        if not pdf:
            raise PDFRenderError("Chromium returned an empty PDF document.")
        return pdf

    async def _get_browser(self):
        settings = get_settings()
        async with self._lock:
            if self._browser is not None and self._browser.is_connected():
                return self._browser
            if self._playwright is None:
                self._playwright = await async_playwright().start()

            launch_args = ["--disable-dev-shm-usage"]
            if settings.playwright_no_sandbox:
                launch_args.extend(["--no-sandbox", "--disable-setuid-sandbox"])

            launch_kwargs: dict = {"headless": True, "args": launch_args}
            if settings.playwright_browser_path:
                launch_kwargs["executable_path"] = settings.playwright_browser_path

            try:
                self._browser = await self._playwright.chromium.launch(
                    **launch_kwargs
                )
            except Exception as exc:
                raise PDFRenderError(
                    "Could not launch Playwright Chromium. Ensure the browser "
                    "is installed (`playwright install chromium`). "
                    f"Detail: {exc}"
                ) from exc
            logger.info("Playwright Chromium launched (headless).")
            return self._browser

    async def close(self) -> None:
        """Release the browser and the Playwright driver."""
        async with self._lock:
            if self._browser is not None:
                try:
                    await self._browser.close()
                finally:
                    self._browser = None
            if self._playwright is not None:
                try:
                    await self._playwright.stop()
                finally:
                    self._playwright = None
            logger.info("Playwright Chromium shut down.")


pdf_renderer = PDFRenderer()
