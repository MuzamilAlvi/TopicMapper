from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


ASSETS_DIR = Path(__file__).resolve().parent / "assets"


# -----------------------------
# Minimal SVG building blocks
# -----------------------------

def _svg_header(width: int, height: int) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'fill="none" xmlns="http://www.w3.org/2000/svg">\n'
    )


def _svg_defs() -> str:
    # Fluent-ish: purple->cyan->green gradient.
    return """  <defs>
    <linearGradient id="grad" x1="20" y1="10" x2="110" y2="120" gradientUnits="userSpaceOnUse">
      <stop stop-color="#6D5EFC"/>
      <stop offset="0.55" stop-color="#28C7F7"/>
      <stop offset="1" stop-color="#20C997"/>
    </linearGradient>

    <linearGradient id="grad2" x1="80" y1="20" x2="220" y2="260" gradientUnits="userSpaceOnUse">
      <stop stop-color="#6D5EFC"/>
      <stop offset="0.45" stop-color="#28C7F7"/>
      <stop offset="1" stop-color="#20C997"/>
    </linearGradient>

    <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="14" stdDeviation="16" flood-color="#000" flood-opacity="0.25"/>
    </filter>
  </defs>
"""


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _write_if_changed(path: Path, content: str) -> None:
    """Idempotent: write only if different."""
    _ensure_dir(path.parent)
    if path.exists():
        try:
            existing = path.read_text(encoding="utf-8", errors="ignore")
            if existing == content:
                return
        except Exception:
            # If read fails, fall back to write.
            pass
    path.write_text(content, encoding="utf-8")


def _rounded_rect(x: int, y: int, w: int, h: int, r: int, fill: str, stroke: str, stroke_width: int = 2) -> str:
    return (
        f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    )


def _png_from_svg(_svg_path: Path, _png_path: Path) -> None:
    """Optional PNG export.

    We avoid hard dependency on cairosvg; generator will skip PNG export if
    not available.
    """
    try:
        import cairosvg  # type: ignore

        _png_path.parent.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2png(url=str(_svg_path), write_to=str(_png_path), output_width=None)
    except Exception:
        # Skip PNG export gracefully.
        pass


# -----------------------------
# Asset catalog
# -----------------------------


@dataclass(frozen=True)
class SvgAsset:
    rel_path: str
    width: int
    height: int
    svg_builder: callable


def _build_logo_svg(width: int, height: int, variant: str) -> str:
    # variant: "dark" | "light"
    if variant == "dark":
        bg_fill = "rgba(10,16,30,0.45)"
        bg_stroke = "rgba(255,255,255,0.18)"
        inner_fill = "rgba(255,255,255,0.04)"
        inner_stroke = "rgba(255,255,255,0.28)"
        number_fill = "url(#grad2)"
        number_opacity = "0.45"
        outline_fill = "rgba(255,255,255,0.55)"
    else:
        bg_fill = "url(#grad2)"
        bg_stroke = "rgba(0,0,0,0.10)"
        inner_fill = "rgba(255,255,255,0.65)"
        inner_stroke = "rgba(0,0,0,0.10)"
        number_fill = "url(#grad)"
        number_opacity = "0.18"
        outline_fill = "rgba(0,0,0,0.18)"

    w = width
    h = height
    # Main background
    return (
        _svg_header(w, h)
        + "  "
        + _svg_defs()
        + "  \\n"
        + (
            f'  <rect x="{int(w*0.07)}" y="{int(h*0.07)}" width="{int(w*0.86)}" height="{int(h*0.86)}" '
            f'rx="{int(w*0.18)}" fill="{bg_fill}" stroke="{bg_stroke}" filter="url(#shadow)"/>'
        )
        + (
            "  <path d=\"M14 0\" fill=\"none\"/>\n"
        )
        + (
            # Video window
            f'  <rect x="{int(w*0.22)}" y="{int(h*0.40)}" width="{int(w*0.35)}" height="{int(h*0.28)}" '
            f'rx="{int(w*0.055)}" fill="{inner_fill}" stroke="{inner_stroke}"/>'
        )
        + (
            # Play triangle
            f'  <path d="M{int(w*0.29)} {int(h*0.51)} L{int(w*0.34)} {int(h*0.47)} V{int(h*0.57)} L{int(w*0.29)} {int(h*0.51)} Z" fill="url(#grad)"/>'
        )
        + (
            # Rename stroke
            f'  <path d="M{int(w*0.27)} {int(h*0.50)}C{int(w*0.27)} {int(h*0.41)} {int(w*0.33)} {int(h*0.35)} {int(w*0.41)} {int(h*0.35)}H{int(w*0.48)} '
            f'C{int(w*0.52)} {int(h*0.35)} {int(w*0.54)} {int(h*0.38)} {int(w*0.54)} {int(h*0.41)} '
            f'C{int(w*0.54)} {int(h*0.44)} {int(w*0.52)} {int(h*0.46)} {int(w*0.48)} {int(h*0.46)} '
            f'H{int(w*0.43)} C{int(w*0.41)} {int(h*0.46)} {int(w*0.39)} {int(h*0.48)} {int(w*0.39)} {int(h*0.51)} '
            f'C{int(w*0.39)} {int(h*0.54)} {int(w*0.41)} {int(h*0.56)} {int(w*0.43)} {int(h*0.56)}H{int(w*0.46)}" '
            f'stroke="url(#grad2)" stroke-width="{int(w*0.04)}" stroke-linecap="round"/>'
        )
        + (
            f'  <rect x="{int(w*0.275)}" y="{int(h*0.355)}" width="{int(w*0.22)}" height="{int(h*0.04)}" fill="transparent"/>'
        )
        + (
            # TM text
            f'  <text x="{int(w*0.66)}" y="{int(h*0.43)}" text-anchor="middle" font-family="ui-sans-serif, system-ui" '
            f'font-size="{int(w*0.045)}" font-weight="800" fill="url(#grad2)" fill-opacity="0.95">TM</text>'
        )
        + "</svg>\n"
    )


def _build_simple_icon(width: int, height: int, glyph: str, extra: str = "") -> str:
    # glyph is a path or shapes.
    return (
        _svg_header(width, height)
        + "  "
        + _svg_defs()
        + (
            f'  <rect x="{int(width*0.08)}" y="{int(height*0.08)}" width="{int(width*0.84)}" height="{int(height*0.84)}" rx="{int(width*0.27)}" '
            'fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.28)"/>'
        )
        + f"{extra}\n"
        + f"{glyph}\n"
        + "</svg>\n"
    )


def _icons() -> List[Tuple[str, str]]:
    # Returns (filename, svg content) but built on-demand in generator.
    return []


def generate_all_assets(*, png: bool = True) -> None:
    # Create folders
    for rel in [
        "logo",
        "icons",
        "favicon",
        "splash",
        "loading",
        "toolbar",
        "sidebar",
        "notifications",
        "themes",
        "illustrations/",
        "illustrations",
    ]:
        _ensure_dir(ASSETS_DIR / rel)

    # -----------------
    # Logo
    # -----------------
    logo_svg = _build_logo_svg(512, 512, "dark")
    _write_if_changed(ASSETS_DIR / "logo" / "logo.svg", logo_svg)

    logo_dark_svg = _build_logo_svg(512, 512, "dark")
    _write_if_changed(ASSETS_DIR / "logo" / "logo-dark.svg", logo_dark_svg)

    logo_light_svg = _build_logo_svg(512, 512, "light")
    _write_if_changed(ASSETS_DIR / "logo" / "logo-light.svg", logo_light_svg)

    logo_small_svg = _build_logo_svg(256, 256, "dark")
    _write_if_changed(ASSETS_DIR / "logo" / "logo-small.svg", logo_small_svg)

    # -----------------
    # Favicon SVG (simple)
    # -----------------
    fav = (
        _svg_header(512, 512)
        + "  "
        + _svg_defs()
        + _rounded_rect(64, 64, 384, 384, 96, "rgba(255,255,255,0.05)", "rgba(255,255,255,0.25)", 2)
        + "\n"
        + (
            '  <path d="M190 260C190 200 236 152 296 152H350C386 152 416 182 416 216C416 250 386 280 350 280H302C273 280 250 303 250 332C250 361 273 384 302 384H320" '
            'stroke="url(#grad2)" stroke-width="28" stroke-linecap="round"/>'
        )
        + (
            '  <rect x="206" y="288" width="88" height="62" rx="18" fill="rgba(10,16,30,0.18)" stroke="rgba(255,255,255,0.35)"/>'
        )
        + (
            '  <path d="M236 318L268 299V337L236 318Z" fill="url(#grad)"/>'
        )
        + "</svg>\n"
    )
    _write_if_changed(ASSETS_DIR / "favicon" / "favicon.svg", fav)

    # -----------------
    # Splash
    # -----------------
    splash = (
        _svg_header(1200, 600)
        + "  "
        + _svg_defs()
        + (
            '  <rect x="0" y="0" width="1200" height="600" fill="url(#grad2)" opacity="0.12"/>'
        )
        + (
            '  <rect x="80" y="80" width="1040" height="440" rx="48" fill="rgba(10,16,30,0.25)" stroke="rgba(255,255,255,0.22)"/>'
        )
        + (
            '  <path d="M380 310C380 220 448 152 538 152H630C690 152 740 202 740 262C740 322 690 372 630 372H560C520 372 490 402 490 442C490 482 520 512 560 512H610" '
            'stroke="url(#grad)" stroke-width="28" stroke-linecap="round"/>'
        )
        + (
            '  <text x="880" y="300" font-family="ui-sans-serif, system-ui" font-size="58" font-weight="900" fill="url(#grad)">TopicMapper</text>'
        )
        + (
            '  <text x="880" y="370" font-family="ui-sans-serif, system-ui" font-size="24" font-weight="700" fill="rgba(231,238,252,0.75)">Intelligent Batch Renaming</text>'
        )
        + "</svg>\n"
    )
    _write_if_changed(ASSETS_DIR / "splash" / "splash.svg", splash)

    # -----------------
    # Loading assets
    # -----------------
    loading_svg = (
        _svg_header(512, 512)
        + "  "
        + _svg_defs()
        + (
            '  <rect x="64" y="64" width="384" height="384" rx="96" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.22)"/>'
        )
        + (
            '  <circle cx="256" cy="256" r="96" stroke="rgba(255,255,255,0.18)" stroke-width="18" fill="none"/>'
        )
        + (
            '  <path d="M352 256a96 96 0 0 1-96 96" stroke="url(#grad)" stroke-width="22" stroke-linecap="round"/>'
        )
        + (
            '  <animateTransform attributeName="transform" type="rotate" from="0 256 256" to="360 256 256" dur="1.1s" repeatCount="indefinite"/>'
        )
        + "</svg>\n"
    )
    _write_if_changed(ASSETS_DIR / "loading" / "loading.svg", loading_svg)

    spinner_svg = (
        _svg_header(512, 512)
        + "  "
        + _svg_defs()
        + (
            '  <circle cx="256" cy="256" r="118" stroke="rgba(255,255,255,0.18)" stroke-width="18" fill="none"/>'
        )
        + (
            '  <path d="M374 256a118 118 0 0 1-118 118" stroke="url(#grad2)" stroke-width="22" stroke-linecap="round"/>'
        )
        + (
            '  <animateTransform attributeName="transform" type="rotate" from="0 256 256" to="360 256 256" dur="0.9s" repeatCount="indefinite"/>'
        )
        + "</svg>\n"
    )
    _write_if_changed(ASSETS_DIR / "loading" / "spinner.svg", spinner_svg)

    # -----------------
    # Theme assets (CSS-like swatches as SVG)
    # -----------------
    dark_theme = (
        _svg_header(600, 320)
        + "  "
        + _svg_defs()
        + '  <rect x="0" y="0" width="600" height="320" fill="#0b1220"/>'
        + '  <rect x="50" y="60" width="220" height="200" rx="32" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.12)"/>'
        + '  <rect x="310" y="60" width="240" height="200" rx="32" fill="url(#grad2)" opacity="0.14" stroke="rgba(255,255,255,0.18)"/>'
        + '  <text x="70" y="125" font-family="ui-sans-serif, system-ui" font-size="22" font-weight="800" fill="rgba(231,238,252,0.85)">Dark</text>'
        + '  <text x="330" y="125" font-family="ui-sans-serif, system-ui" font-size="22" font-weight="800" fill="rgba(231,238,252,0.85)">Fluent</text>'
        + "</svg>\n"
    )
    _write_if_changed(ASSETS_DIR / "themes" / "dark-mode.svg", dark_theme)

    light_theme = (
        _svg_header(600, 320)
        + "  "
        + _svg_defs()
        + '  <rect x="0" y="0" width="600" height="320" fill="#f6f8ff"/>'
        + '  <rect x="50" y="60" width="220" height="200" rx="32" fill="rgba(0,0,0,0.05)" stroke="rgba(0,0,0,0.10)"/>'
        + '  <rect x="310" y="60" width="240" height="200" rx="32" fill="url(#grad2)" opacity="0.16" stroke="rgba(0,0,0,0.12)"/>'
        + '  <text x="70" y="125" font-family="ui-sans-serif, system-ui" font-size="22" font-weight="800" fill="rgba(22,35,61,0.85)">Light</text>'
        + '  <text x="330" y="125" font-family="ui-sans-serif, system-ui" font-size="22" font-weight="800" fill="rgba(22,35,61,0.85)">Fluent</text>'
        + "</svg>\n"
    )
    _write_if_changed(ASSETS_DIR / "themes" / "light-mode.svg", light_theme)

    # -----------------
    # Illustrations
    # -----------------
    empty_state = (
        _svg_header(900, 520)
        + "  "
        + _svg_defs()
        + '  <rect x="0" y="0" width="900" height="520" fill="rgba(255,255,255,0.04)"/>'
        + '  <rect x="80" y="80" width="740" height="360" rx="48" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.12)"/>'
        + (
            '  <path d="M240 250c0-70 56-126 126-126h72c50 0 90 40 90 90s-40 90-90 90h-64c-36 0-66 30-66 66s30 66 66 66h44" '
            'stroke="url(#grad)" stroke-width="20" stroke-linecap="round" fill="none"/>'
        )
        + '  <text x="460" y="300" text-anchor="middle" font-family="ui-sans-serif, system-ui" font-size="26" font-weight="900" fill="rgba(231,238,252,0.82)">Nothing to preview yet</text>'
        + '  <text x="460" y="340" text-anchor="middle" font-family="ui-sans-serif, system-ui" font-size="16" font-weight="700" fill="rgba(231,238,252,0.62)">Select a videos folder and import topics</text>'
        + "</svg>\n"
    )
    _write_if_changed(ASSETS_DIR / "illustrations" / "empty-state.svg", empty_state)

    no_files = (
        _svg_header(900, 520)
        + "  "
        + _svg_defs()
        + '  <rect x="0" y="0" width="900" height="520" fill="rgba(255,255,255,0.04)"/>'
        + '  <rect x="140" y="130" width="620" height="260" rx="40" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.12)"/>'
        + '  <rect x="220" y="190" width="460" height="130" rx="26" fill="rgba(10,16,30,0.18)" stroke="rgba(255,255,255,0.25)"/>'
        + '  <path d="M300 260h300" stroke="url(#grad2)" stroke-width="18" stroke-linecap="round"/>'
        + '  <text x="450" y="375" text-anchor="middle" font-family="ui-sans-serif, system-ui" font-size="18" font-weight="800" fill="rgba(231,238,252,0.62)">No matching video files found</text>'
        + "</svg>\n"
    )
    _write_if_changed(ASSETS_DIR / "illustrations" / "no-files-found.svg", no_files)

    drag_drop = (
        _svg_header(900, 520)
        + "  "
        + _svg_defs()
        + '  <rect x="0" y="0" width="900" height="520" fill="rgba(255,255,255,0.04)"/>'
        + '  <rect x="120" y="120" width="660" height="280" rx="50" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.16)" stroke-dasharray="10 10"/>'
        + '  <path d="M450 210l-90 90h60v80h60v-80h60l-90-90z" fill="url(#grad)" opacity="0.9"/>'
        + '  <text x="450" y="330" text-anchor="middle" font-family="ui-sans-serif, system-ui" font-size="24" font-weight="900" fill="rgba(231,238,252,0.82)">Drag & Drop</text>'
        + '  <text x="450" y="365" text-anchor="middle" font-family="ui-sans-serif, system-ui" font-size="16" font-weight="700" fill="rgba(231,238,252,0.62)">Folder + Topics file</text>'
        + "</svg>\n"
    )
    _write_if_changed(ASSETS_DIR / "illustrations" / "drag-drop.svg", drag_drop)

    rename_complete = (
        _svg_header(900, 520)
        + "  "
        + _svg_defs()
        + '  <rect x="0" y="0" width="900" height="520" fill="rgba(255,255,255,0.04)"/>'
        + '  <circle cx="450" cy="250" r="150" fill="rgba(32,201,151,0.12)" stroke="rgba(32,201,151,0.40)" stroke-width="10"/>'
        + '  <path d="M360 255l55 55 130-155" stroke="url(#grad)" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>'
        + '  <text x="450" y="395" text-anchor="middle" font-family="ui-sans-serif, system-ui" font-size="22" font-weight="900" fill="rgba(231,238,252,0.82)">Renaming complete</text>'
        + "</svg>\n"
    )
    _write_if_changed(ASSETS_DIR / "illustrations" / "rename-complete.svg", rename_complete)

    error_state = (
        _svg_header(900, 520)
        + "  "
        + _svg_defs()
        + '  <rect x="0" y="0" width="900" height="520" fill="rgba(255,255,255,0.04)"/>'
        + '  <rect x="240" y="120" width="420" height="280" rx="50" fill="rgba(255,77,109,0.12)" stroke="rgba(255,77,109,0.35)" stroke-width="8"/>'
        + '  <path d="M450 200L560 380H340L450 200Z" fill="rgba(255,77,109,0.22)" stroke="url(#grad2)" stroke-width="10"/>'
        + '  <rect x="420" y="250" width="60" height="72" rx="30" fill="rgba(11,18,32,0.35)"/>'
        + '  <circle cx="450" cy="360" r="14" fill="rgba(11,18,32,0.35)"/>'
        + '  <text x="450" y="420" text-anchor="middle" font-family="ui-sans-serif, system-ui" font-size="20" font-weight="900" fill="rgba(231,238,252,0.82)">An error occurred</text>'
        + "</svg>\n"
    )
    _write_if_changed(ASSETS_DIR / "illustrations" / "error-state.svg", error_state)

    # -----------------
    # Status icons / file type / sidebar / toolbar / notifications
    # -----------------
    def status_icon(name: str, color: str) -> str:
        # circle + symbol
        return (
            _svg_header(128, 128)
            + "  "
            + _svg_defs()
            + (
                f'  <rect x="14" y="14" width="100" height="100" rx="34" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.28)"/>'
            )
            + f'  <circle cx="64" cy="64" r="26" fill="{color}" opacity="0.22" stroke="{color}" stroke-width="6"/>'
            + "</svg>\n"
        )

    _write_if_changed(ASSETS_DIR / "notifications" / "success.svg", status_icon("success", "#20C997"))
    _write_if_changed(ASSETS_DIR / "notifications" / "error.svg", status_icon("error", "#FF4D6D"))
    _write_if_changed(ASSETS_DIR / "notifications" / "warning.svg", status_icon("warning", "#FFB020"))
    _write_if_changed(ASSETS_DIR / "notifications" / "info.svg", status_icon("info", "#28C7F7"))
    _write_if_changed(ASSETS_DIR / "notifications" / "loading.svg", status_icon("loading", "#6D5EFC"))

    # File type icons
    def file_icon(kind: str) -> str:
        # Simple document + corner fold + glyph.
        glyph = ""
        if kind == "video":
            glyph = '  <path d="M60 44L86 60L60 76V44Z" fill="url(#grad)"/>'
        elif kind == "text":
            glyph = '  <path d="M52 42h52M52 58h44M52 74h36" stroke="url(#grad2)" stroke-width="6" stroke-linecap="round"/>'
        elif kind == "folder":
            glyph = '  <path d="M38 44h30l10 10h22v40H38V44Z" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.28)" stroke-width="4"/>'
        elif kind == "report":
            glyph = '  <path d="M50 42h50v46H50V42Z" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.28)" stroke-width="4"/>'
            glyph += '  <path d="M60 62h30M60 74h22" stroke="url(#grad)" stroke-width="6" stroke-linecap="round"/>'
        else:  # config
            glyph = '  <path d="M56 44h16l6 20-6 20H56l-6-20 6-20Z" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.28)" stroke-width="4"/>'

        return (
            _svg_header(128, 128)
            + "  "
            + _svg_defs()
            + '  <rect x="26" y="34" width="76" height="86" rx="18" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.28)" stroke-width="4"/>'
            + '  <path d="M76 34l26 26h-26V34Z" fill="rgba(109,94,252,0.18)"/>'
            + glyph
            + "</svg>\n"
        )

    _write_if_changed(ASSETS_DIR / "icons" / "type-video.svg", file_icon("video"))
    _write_if_changed(ASSETS_DIR / "icons" / "type-text.svg", file_icon("text"))
    _write_if_changed(ASSETS_DIR / "icons" / "type-folder.svg", file_icon("folder"))
    _write_if_changed(ASSETS_DIR / "icons" / "type-report.svg", file_icon("report"))
    _write_if_changed(ASSETS_DIR / "icons" / "type-config.svg", file_icon("config"))

    # Toolbar icons (12)
    toolbar_names = [
        ("open-folder", "M38 44h38l8 10h22v52H38V44Z"),
        ("import-topics", "M64 42v44M42 64h44"),
        ("preview", "M32 64c12-18 28-28 32-28s20 10 32 28c-12 18-28 28-32 28s-20-10-32-28Z"),
        ("rename", "M44 74l-6 16 16-6 46-46-10-10-46 46Z"),
        ("undo", "M70 52H44v-16L18 66l26 30V80h30c16 0 32 12 32 28 0-22-18-36-36-36Z"),
        ("export", "M64 42v40m0 0l16-16m-16 16L48 66"),
        ("settings", "M52 44h24l4 18-12 18-12-18 4-18Z"),
        ("search", "M50 74a24 24 0 1 1 34 0"),
        ("refresh", "M88 52c-6-10-18-16-30-16-22 0-40 18-40 40s18 40 40 40c18 0 34-12 38-28"),
        ("report", "M44 40h52v68H44V40Z"),
        ("help", "M64 44a22 22 0 1 0 0 44c0-10-9-14-9-22"),
        ("about", "M64 44a22 22 0 1 0 0 44a22 22 0 1 0 0-44Z"),
    ]

    for fname, path_d in toolbar_names:
        svg = (
            _svg_header(128, 128)
            + "  "
            + _svg_defs()
            + '  <rect x="14" y="14" width="100" height="100" rx="34" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.28)"/>'
            + (
                f'  <path d="{path_d}" stroke="url(#grad)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>'
                if "h" in path_d or "M" in path_d
                else f'  <path d="{path_d}" fill="none"/>'
            )
            + "</svg>\n"
        )
        _write_if_changed(ASSETS_DIR / "toolbar" / f"{fname}.svg", svg)

    # Sidebar icons
    sidebar_names = [
        ("dashboard", "M40 64h20v28H40V64Z"),
        ("files", "M44 44h40v40H44V44Z"),
        ("preview", "M32 64c12-18 28-28 32-28s20 10 32 28c-12 18-28 28-32 28s-20-10-32-28Z"),
        ("reports", "M44 40h52v68H44V40Z"),
        ("history", "M78 36c-20 0-36 16-36 36s16 36 36 36 36-16 36-36"),
        ("settings", "M52 44h24l4 18-12 18-12-18 4-18Z"),
    ]
    for fname, path_d in sidebar_names:
        svg = (
            _svg_header(128, 128)
            + "  "
            + _svg_defs()
            + '  <rect x="14" y="14" width="100" height="100" rx="34" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.28)"/>'
            + f'  <path d="{path_d}" fill="rgba(255,255,255,0.06)" stroke="url(#grad2)" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
            + "</svg>\n"
        )
        _write_if_changed(ASSETS_DIR / "sidebar" / f"{fname}.svg", svg)

    # Search icon also as dedicated status style

    # -----------------
    # Theme assets (PNG export optional)
    # -----------------

    if png:
        # Only attempt PNG exports for the most important assets (logo/splash/favicon). 
        # Others can remain SVG; app can use SVG.
        exports: List[Tuple[Path, Path]] = []
        exports.append((ASSETS_DIR / "logo" / "logo.svg", ASSETS_DIR / "logo" / "logo.png"))
        exports.append((ASSETS_DIR / "logo" / "logo.svg", ASSETS_DIR / "logo" / "logo-dark.png"))
        exports.append((ASSETS_DIR / "favicon" / "favicon.svg", ASSETS_DIR / "favicon" / "favicon.ico.png"))
        exports.append((ASSETS_DIR / "splash" / "splash.svg", ASSETS_DIR / "splash" / "splash.png"))

        # Create some launcher icon PNG sizes if cairosvg is available.
        sizes = [16, 32, 64, 128, 256, 512]
        for s in sizes:
            exports.append((ASSETS_DIR / "logo" / "logo-small.svg", ASSETS_DIR / "app" / f"app-{s}.png"))

        for src, dst in exports:
            try:
                _png_from_svg(src, dst)
            except Exception:
                pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate TopicMapper assets (SVG + optional PNG).")
    parser.add_argument("--no-png", action="store_true", help="Skip PNG exports (SVG remains).")
    args = parser.parse_args()

    generate_all_assets(png=not args.no_png)

