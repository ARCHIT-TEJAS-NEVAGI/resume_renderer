import asyncio

import pytest

from app.services import pdf_renderer as module
from app.services.pdf_renderer import PDFRenderer


class FakePage:
    def __init__(self):
        self.closed = False
        self.received_html = None

    async def set_content(self, html, **kwargs):
        self.received_html = html

    async def pdf(self, **kwargs):
        assert self.received_html is not None
        return b"%PDF-1.4 fake"

    async def close(self):
        self.closed = True


class FakeBrowser:
    def __init__(self):
        self.closed = False
        self.pages = []

    def is_connected(self):
        return True

    async def new_page(self):
        page = FakePage()
        self.pages.append(page)
        return page

    async def close(self):
        self.closed = True


class FakePlaywright:
    class chromium:
        @staticmethod
        async def launch(**kwargs):
            return FakeBrowser()

    async def start(self):
        return self

    async def stop(self):
        pass


def fake_async_playwright():
    return FakePlaywright()


def test_render_pdf_returns_pdf_bytes(monkeypatch):
    monkeypatch.setattr(module, "async_playwright", fake_async_playwright)
    renderer = PDFRenderer()
    pdf = asyncio.run(
        renderer.render_pdf("<!DOCTYPE html><html><body><h1>Hi</h1></body></html>")
    )
    assert pdf == b"%PDF-1.4 fake"


def test_render_pdf_closes_page(monkeypatch):
    monkeypatch.setattr(module, "async_playwright", fake_async_playwright)
    renderer = PDFRenderer()
    asyncio.run(renderer.render_pdf("<html><body>x</body></html>"))
    assert renderer._browser is not None
    assert renderer._browser.pages[0].closed is True


def test_render_pdf_reuses_browser(monkeypatch):
    monkeypatch.setattr(module, "async_playwright", fake_async_playwright)
    renderer = PDFRenderer()
    asyncio.run(renderer.render_pdf("<html></html>"))
    first_browser = renderer._browser
    asyncio.run(renderer.render_pdf("<html></html>"))
    assert renderer._browser is first_browser


def test_render_pdf_launch_failure_raises(monkeypatch):
    class BrokenPlaywright:
        class chromium:
            @staticmethod
            async def launch(**kwargs):
                raise RuntimeError("browser executable not found")

        async def start(self):
            return self

        async def stop(self):
            pass

    monkeypatch.setattr(module, "async_playwright", lambda: BrokenPlaywright())
    renderer = PDFRenderer()
    with pytest.raises(module.PDFRenderError, match="Could not launch"):
        asyncio.run(renderer.render_pdf("<html></html>"))


def test_close_releases_browser_and_playwright(monkeypatch):
    monkeypatch.setattr(module, "async_playwright", fake_async_playwright)
    renderer = PDFRenderer()
    asyncio.run(renderer.render_pdf("<html></html>"))
    browser = renderer._browser
    asyncio.run(renderer.close())
    assert browser.closed is True
    assert renderer._browser is None
    assert renderer._playwright is None
