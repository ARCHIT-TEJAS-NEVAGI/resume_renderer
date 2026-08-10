# resume-renderer

A standalone, production-grade microservice that renders **verified resume
JSON** into full **HTML documents** and **A4 PDFs**.

It is one service in an AI Resume Builder ecosystem. It does **only** HTML and
PDF rendering — nothing else.

| Responsibility | In scope | Out of scope |
| --- | --- | --- |
| Resume parsing / OCR / JD parsing | — | `resume-parser` |
| Frontend | — | Lovable app |
| MongoDB schema | — | separate project |
| API contracts / prompt library | — | separate projects |
| **HTML generation** | ✅ `POST /generate/html` | |
| **PDF generation** | ✅ `POST /generate/pdf` | |

---

## Rendering rules

- Resume content is **never modified**: no rewriting, optimizing, inferring,
  or verifying.
- No AI, no external APIs (no Cloudflare, no OpenAI).
- Templates are **ATS-friendly**: single column, no tables, no icons, no
  images, no SVG, no charts, no skill ratings.
- Empty sections are **automatically hidden**.
- Generated documents are fully self-contained (inline CSS + optional
  self-hosted fonts) so they render identically in a browser, when printed,
  and in the Playwright-generated PDF.

---

## Architecture

```
resume-renderer/
├── app/
│   ├── main.py                 # FastAPI app, lifespan, CORS, static mount
│   ├── config.py               # Settings (env / .env), path constants
│   ├── routes/
│   │   ├── generate_html.py    # POST /generate/html
│   │   └── generate_pdf.py     # POST /generate/pdf
│   ├── services/
│   │   ├── template_manager.py # Jinja2 env, base CSS, self-hosted fonts
│   │   ├── html_renderer.py    # resume → normalized context → HTML
│   │   └── pdf_renderer.py     # HTML → Playwright Chromium → PDF
│   ├── schemas/
│   │   └── models.py           # Pydantic request models (the contract)
│   ├── utils/
│   │   └── validators.py       # template + resume validation
│   └── templates/
│       ├── classic.html
│       ├── modern.html
│       ├── executive.html
│       └── partials/_entries.html
├── static/
│   ├── css/base.css            # shared ATS-friendly base styles
│   └── fonts/                  # optional self-hosted fonts (see README)
├── tests/                      # unit + API tests
├── requirements.txt
├── render.yaml                 # Render deployment
└── .env.example
```

Layering follows SOLID: routing (HTTP) → services (rendering) → schema
(contract) → validation, with a single template manager owning Jinja2.

---

## Quick start (local)

Requires Python 3.11+.

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install the Playwright Chromium browser (once)
playwright install chromium

# 3. Copy the environment template
cp .env.example .env

# 4. Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Swagger UI: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

> On Windows, run the Playwright install from the same Python environment.
> On Render/containers keep `PLAYWRIGHT_NO_SANDBOX=true` (default).

---

## API

### `POST /generate/html`

Returns a complete standalone HTML document (`text/html; charset=utf-8`).

```bash
curl -X POST http://localhost:8000/generate/html \
  -H "Content-Type: application/json" \
  -d @resume.json \
  -o resume.html
```

### `POST /generate/pdf`

Renders the same HTML and converts it to an A4 PDF via Playwright Chromium.
Returns `application/pdf`.

```bash
curl -X POST http://localhost:8000/generate/pdf \
  -H "Content-Type: application/json" \
  -d @resume.json \
  -o resume.pdf
```

### Request body

```jsonc
{
  "template": "classic",                 // classic | modern | executive
  "resume": {
    "contact": {
      "name": "Alex Doe",                // required, non-empty
      "title": "Senior Software Engineer",
      "email": "alex.doe@example.com",
      "phone": "+1 555 010 0199",
      "location": "London, UK",
      "website": "https://alexdoe.dev",
      "linkedin": "linkedin.com/in/alexdoe",
      "github": "github.com/alexdoe",
      "links": [{ "label": "Portfolio", "url": "https://portfolio.dev" }]
    },
    "summary": "First paragraph.\n\nSecond paragraph.",
    "skills": ["Python", "FastAPI", "AWS"],   // strings or {"name": "..."} objects
    "experience": [{
      "title": "Staff Engineer",
      "company": "Acme Corp",
      "location": "Remote",
      "start": "2021-01",
      "end": "Present",                  // or omit end and set "current": true
      "bullets": ["Led a platform team."],
      "description": "Optional free text; used as bullets when bullets are empty."
    }],
    "projects": [{
      "name": "resume-renderer",
      "role": "Creator",
      "url": "https://github.com/example/resume-renderer",
      "technologies": ["FastAPI", "Playwright"],
      "description": "A production-grade rendering service.",
      "bullets": []
    }],
    "education": [{
      "institution": "University of London",
      "degree": "MSc",
      "field": "Computer Science",
      "location": "London, UK",
      "start": "2013", "end": "2015",
      "gpa": "Distinction"
    }],
    "certifications": [{ "name": "AWS Solutions Architect", "issuer": "AWS", "date": "2023" }],
    "languages": [{ "name": "English", "proficiency": "Native" }],
    "awards": [{ "title": "Engineering Excellence", "issuer": "Acme", "date": "2023", "description": "" }],
    "volunteer": [{ "role": "Mentor", "organization": "CodeFirst", "bullets": ["..."], "start": "2022-01", "current": true }],
    "publications": [{ "title": "Reliable Systems", "venue": "Example Journal", "authors": ["Alex Doe"], "date": "2024", "url": "" }],
    "additional_sections": [{ "title": "Speaking", "items": ["Talk at ExampleConf 2024."] }]
  }
}
```

**Behavior notes**

- Every section that has no content is hidden automatically.
- `"current": true` renders the end date as `Present`; a missing end date is
  never invented.
- Multi-line `description` without `bullets` is rendered as bullet lines.
- Extra/unknown JSON fields are ignored (forward compatible); schema errors
  return `422`, bad template names return `400`.
- All user-provided text is HTML-escaped before rendering.

### Error responses

| Code | Meaning |
| --- | --- |
| `400` | Unsupported template name or invalid resume content (no contact name) |
| `422` | Request body failed Pydantic schema validation |
| `500` | HTML rendering failure, or PDF failure (e.g. Chromium missing) |

---

## Templates

| Template | Character | Typeface |
| --- | --- | --- |
| `classic` | traditional, centered header, rules under sections | serif |
| `modern` | contemporary, accent bar, left-aligned header | sans-serif |
| `executive` | refined, small-caps name, generous spacing | serif |

All three are single-column, A4-ready (`@page`), print-ready (`@media print`),
responsive (`@media screen`), and use only semantic HTML.

---

## Environment variables

See `.env.example` for the full list. Key ones:

| Variable | Default | Purpose |
| --- | --- | --- |
| `LOG_LEVEL` | `INFO` | Loguru level |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `SUPPORTED_TEMPLATES` | `classic,modern,executive` | Templates allowed |
| `PLAYWRIGHT_NO_SANDBOX` | `true` | Adds `--no-sandbox` (required on Render) |
| `PLAYWRIGHT_BROWSER_PATH` | *(empty)* | Custom Chromium executable path |
| `PLAYWRIGHT_RENDER_TIMEOUT_MS` | `30000` | Page load timeout before printing |
| `PDF_FORMAT` | `A4` | PDF page format |
| `PDF_PRINT_BACKGROUND` | `true` | Print background colors |
| `PDF_PREFER_CSS_PAGE_SIZE` | `true` | Honor `@page` size/margins from CSS |

---

## Deploying to Render

`render.yaml` is included. Render deploys it as a **native Python web service**
(no Docker required).

1. Push this repository to GitHub/GitLab.
2. In Render, **New → Blueprint** and select the repo, or create a **Web
   Service** and pick this repo — Render auto-detects `render.yaml`.
3. The build runs:
   ```bash
   pip install -r requirements.txt
   playwright install --with-deps chromium
   ```
   which installs the browser and its system libraries into the same image
   that runs the service.
4. The start command is:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
5. Render health-checks `/health`.

Troubleshooting: if PDF requests return `Could not launch Playwright
Chromium`, confirm `PLAYWRIGHT_NO_SANDBOX=true` and that the deploy log shows
a successful `playwright install`.

---

## Running tests

```bash
pip install -r requirements.txt
playwright install chromium   # only needed for real (non-mocked) PDF tests
pytest
```

The PDF renderer tests use a mocked Playwright driver, so the suite runs
without a browser installed.

---

## Design decisions

- **Single source of truth for layout**: `/generate/pdf` reuses the exact HTML
  from `/generate/html`, so both outputs always match.
- **Self-contained documents**: shared CSS and (optionally) fonts are inlined,
  so a generated HTML file works anywhere without extra assets.
- **Content safety**: user text is escaped; the service's own CSS/fonts are
  injected as trusted `Markup`.
- **Lazy browser**: Playwright Chromium launches on the first PDF request and
  is reused, with clean shutdown on app exit.
- **Config over code**: templates, limits, and Playwright options are env
  driven (`pydantic-settings`).
