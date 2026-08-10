"""Template management.

Responsibilities:
- discover and compile the Jinja2 templates shipped in ``app/templates``;
- load the shared base stylesheet (``static/css/base.css``) and inline it so
  every generated document is fully self-contained (works offline, in a plain
  browser, and when printed to PDF via Playwright);
- optionally self-host fonts dropped into ``static/fonts`` by inlining them as
  base64 data URIs (convention: ``FamilyName-Weight.woff2``, e.g.
  ``Inter-Bold.woff2``, ``PlayfairDisplay-BoldItalic.woff2``).

The manager renders HTML only. It never touches resume content.
"""
import base64
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined
from jinja2 import Template as JinjaTemplate
from markupsafe import Markup
from loguru import logger

from app.config import CSS_DIR, FONTS_DIR, TEMPLATES_DIR, get_settings

# Default system font stacks. Custom self-hosted fonts, if present, are
# prepended automatically.
DEFAULT_SANS_STACK = (
    "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
    "'Helvetica Neue', Arial, sans-serif"
)
DEFAULT_SERIF_STACK = "Georgia, 'Times New Roman', Times, serif"

# CSS font-weight mapping used by the self-hosted font convention.
_FONT_WEIGHTS = {
    "thin": 100,
    "extralight": 200,
    "light": 300,
    "regular": 400,
    "medium": 500,
    "semibold": 600,
    "bold": 700,
    "extrabold": 800,
    "black": 900,
}

_FONT_EXTENSIONS = {
    ".woff2": ("woff2", "font/woff2"),
    ".woff": ("woff", "font/woff"),
    ".ttf": ("truetype", "font/ttf"),
    ".otf": ("opentype", "font/otf"),
}

_FONT_FILE_RE = re.compile(
    r"^(?P<family>[A-Za-z0-9]+(?:[ -][A-Za-z0-9]+)*?)-(?P<weight>[A-Za-z]+)$"
)


class TemplateManager:
    """Loads templates and CSS once and renders resume documents to HTML."""

    def __init__(self) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=True,
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        self._loaded = False
        self._base_css = ""
        self._font_faces = Markup("")
        self._font_stack_sans = DEFAULT_SANS_STACK
        self._font_stack_serif = DEFAULT_SERIF_STACK

    # -- lifecycle ----------------------------------------------------------

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()

    def load(self) -> None:
        """Compile templates and inline shared CSS/fonts. Fails fast on errors."""
        settings = get_settings()

        css_path = CSS_DIR / "base.css"
        if not css_path.exists():
            raise RuntimeError(f"Missing base stylesheet: {css_path}")
        raw_css = css_path.read_text(encoding="utf-8")

        fonts = self._discover_fonts()
        if fonts:
            family = fonts[0][0]
            self._font_stack_sans = f"'{family}', {DEFAULT_SANS_STACK}"
            self._font_stack_serif = f"'{family}', {DEFAULT_SERIF_STACK}"
            self._font_faces = Markup(
                "\n".join(self._font_face_css(font, family) for font in fonts)
            )

        # Render the CSS placeholders (plain text render — no HTML escaping).
        self._base_css = JinjaTemplate(raw_css).render(
            font_stack_sans=self._font_stack_sans,
            font_stack_serif=self._font_stack_serif,
        )

        # Fail fast if a declared template is missing or fails to compile.
        for name in settings.template_list:
            self._env.get_template(f"{name}.html")

        self._loaded = True
        logger.info(
            "Template manager loaded: templates={} fonts={}",
            settings.template_list,
            len(fonts),
        )

    # -- public API ---------------------------------------------------------

    def template_names(self) -> tuple[str, ...]:
        return get_settings().template_list

    def render(self, template_name: str, context: dict) -> str:
        """Render ``context`` with the named template into a full HTML string."""
        settings = get_settings()
        if template_name not in settings.template_list:
            supported = ", ".join(settings.template_list)
            raise ValueError(
                f"Unsupported template '{template_name}'. "
                f"Supported templates: {supported}."
            )
        self.ensure_loaded()

        template = self._env.get_template(f"{template_name}.html")
        render_context = dict(context)
        render_context["base_css"] = Markup(self._base_css)
        render_context["font_faces"] = self._font_faces
        render_context["contact_separator"] = " | "
        return template.render(**render_context)

    # -- fonts --------------------------------------------------------------

    def _discover_fonts(self) -> list[tuple[str, int, bool, str, Path]]:
        """Return ``(family, weight, italic, format, path)`` tuples.

        Filename convention: ``FamilyName-Weight.woff2`` where ``Weight`` is
        one of ``Regular``, ``Medium``, ``SemiBold``, ``Bold``, ``Black``,
        ``Light``, ``Thin``, ``Italic``, or a combination like
        ``BoldItalic``. Files that do not match are skipped with a warning.
        """
        fonts = []
        for path in sorted(FONTS_DIR.glob("*")):
            if path.suffix.lower() not in _FONT_EXTENSIONS or not path.is_file():
                continue
            parsed = self._parse_font_filename(path)
            if parsed is None:
                logger.warning("Skipping font file with unrecognized name: {}", path)
                continue
            family, weight, italic = parsed
            fonts.append((family, weight, italic, path))
        return fonts

    @staticmethod
    def _parse_font_filename(path: Path):
        stem = path.stem
        match = _FONT_FILE_RE.match(stem)
        if match is None:
            # A bare family name (e.g. "Inter.woff2") defaults to regular.
            if any(char.isalpha() for char in stem):
                return stem, 400, False
            return None
        family = match.group("family").strip()
        token = match.group("weight").lower()
        italic = "italic" in token
        weight_token = token.replace("italic", "")
        weight = _FONT_WEIGHTS.get(weight_token, 400)
        if weight_token and weight_token not in _FONT_WEIGHTS:
            logger.warning(
                "Font '{}' uses unknown weight '{}'; assuming 400.",
                path.name,
                match.group("weight"),
            )
        return family, weight, italic

    @staticmethod
    def _font_face_css(font: tuple[str, int, bool, Path], family: str) -> str:
        _, weight, italic, path = font
        ext = path.suffix.lower()
        fmt, mime = _FONT_EXTENSIONS[ext]
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return (
            f"@font-face {{\n"
            f"  font-family: '{family}';\n"
            f"  font-style: {'italic' if italic else 'normal'};\n"
            f"  font-weight: {weight};\n"
            f"  src: url(data:{mime};base64,{data}) format('{fmt}');\n"
            f"}}"
        )


template_manager = TemplateManager()
