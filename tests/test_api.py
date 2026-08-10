from tests.helpers import full_resume_payload, minimal_resume_payload


# --------------------------------------------------------------------------
# System
# --------------------------------------------------------------------------

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "resume-renderer"


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


def test_swagger_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


# --------------------------------------------------------------------------
# POST /generate/html
# --------------------------------------------------------------------------

def test_generate_html_returns_full_document(client):
    response = client.post("/generate/html", json=full_resume_payload())
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")

    html = response.text
    assert html.strip().lower().startswith("<!doctype html>")
    assert "Alex Doe" in html
    assert "Professional Summary" in html
    assert "Skills" in html
    assert "Experience" in html
    assert "Staff Engineer" in html
    assert "Acme Corp" in html
    assert "Education" in html
    assert "Languages" in html
    assert "Speaking" in html
    # Empty sections are automatically hidden.
    assert "Certifications" not in html
    assert "Volunteer" not in html


def test_generate_html_minimal_resume(client):
    response = client.post("/generate/html", json=minimal_resume_payload())
    assert response.status_code == 200
    html = response.text
    assert "Jane Q. Engineer" in html
    for section in (
        "Professional Summary",
        "Skills",
        "Experience",
        "Education",
        "Certifications",
        "Languages",
        "Awards",
        "Publications",
        "Volunteer",
    ):
        assert section not in html


def test_generate_html_unsupported_template(client):
    response = client.post(
        "/generate/html", json=full_resume_payload(template="fancy")
    )
    assert response.status_code == 400
    assert "Unsupported template" in response.json()["detail"]


def test_generate_html_invalid_resume(client):
    response = client.post(
        "/generate/html", json={"template": "classic", "resume": {"contact": {}}}
    )
    assert response.status_code == 422


def test_generate_html_escapes_content(client):
    payload = minimal_resume_payload()
    payload["resume"]["summary"] = "<script>alert(1)</script>"
    response = client.post("/generate/html", json=payload)
    assert response.status_code == 200
    assert "<script>alert" not in response.text


# --------------------------------------------------------------------------
# POST /generate/pdf
# --------------------------------------------------------------------------

async def _fake_render_pdf(html):
    assert html.strip().lower().startswith("<!doctype html>")
    return b"%PDF-1.4 fake-pdf-payload"


def test_generate_pdf_returns_pdf(client, monkeypatch):
    from app.routes import generate_pdf as route_module

    monkeypatch.setattr(route_module.pdf_renderer, "render_pdf", _fake_render_pdf)
    response = client.post("/generate/pdf", json=full_resume_payload())
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF-1.4")
    assert "attachment" in response.headers.get("content-disposition", "")


def test_generate_pdf_unsupported_template(client, monkeypatch):
    from app.routes import generate_pdf as route_module

    async def _should_not_run(html):
        raise AssertionError("PDF renderer must not be called for bad templates")

    monkeypatch.setattr(route_module.pdf_renderer, "render_pdf", _should_not_run)
    response = client.post(
        "/generate/pdf", json=full_resume_payload(template="nope")
    )
    assert response.status_code == 400


def test_generate_pdf_invalid_resume(client, monkeypatch):
    from app.routes import generate_pdf as route_module

    monkeypatch.setattr(route_module.pdf_renderer, "render_pdf", _fake_render_pdf)
    response = client.post(
        "/generate/pdf", json={"template": "classic", "resume": {}}
    )
    assert response.status_code == 422


def test_generate_pdf_render_failure_returns_500(client, monkeypatch):
    from app.routes import generate_pdf as route_module

    async def _failing(html):
        raise route_module.PDFRenderError("Chromium crashed")

    monkeypatch.setattr(route_module.pdf_renderer, "render_pdf", _failing)
    response = client.post("/generate/pdf", json=full_resume_payload())
    assert response.status_code == 500
    assert "Chromium crashed" in response.json()["detail"]
