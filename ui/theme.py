"""FLASH_DOCK visual identity — a light, precise *scientific-instrument* theme.

Design rationale (frontend-design): the subject is a sequential docking pipeline
(prepare → detect pocket → dock → score) whose outputs are quantitative
(coordinates, scores, job IDs). So the identity leans into that:

* **pipeline-stage headers** — an honest "STAGE 0N" eyebrow (it really is a
  sequence) over a Space Grotesk title;
* **monospace for data** — JetBrains Mono on every metric/coordinate/score, so
  the numbers themselves carry the look;
* a cool, restrained palette — lab off-white, deep-slate ink, an electric
  cyan-teal "flash" accent and a warm amber (the ⚡ / fpocket pocket color).

`inject_theme()` is called once at app start; `page_header()` / `status_badge()`
/ `sidebar_brand()` are reusable components.
"""

from __future__ import annotations

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  --fd-bg: #F7F9FB;
  --fd-surface: #FFFFFF;
  --fd-border: #E3E8EF;
  --fd-ink: #0F1B2D;
  --fd-muted: #5B6B7F;
  --fd-primary: #06B6D4;
  --fd-primary-deep: #0E7490;
  --fd-amber: #F59E0B;
  --fd-success: #10B981;
  --fd-running: #3B82F6;
  --fd-failed: #F43F5E;
  --fd-radius: 14px;
  --fd-shadow: 0 1px 2px rgba(15,27,45,.04), 0 10px 30px -16px rgba(15,27,45,.18);
  --font-display: 'Space Grotesk', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', ui-monospace, 'SF Mono', monospace;
}

/* base typography */
.stApp { background: var(--fd-bg); }
.stApp, [data-testid="stMarkdownContainer"], .stApp p, .stApp li, .stApp label,
.stApp .stRadio, .stApp .stSelectbox { font-family: var(--font-body); color: var(--fd-ink); }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
  font-family: var(--font-display); color: var(--fd-ink);
  letter-spacing: -0.02em; font-weight: 600;
}
.block-container { padding-top: 2.4rem; max-width: 1180px; }

/* numbers in JetBrains Mono — the signature data treatment */
[data-testid="stMetricValue"] { font-family: var(--font-mono); font-weight: 600; }
[data-testid="stMetricLabel"] { font-family: var(--font-mono); text-transform: uppercase;
  letter-spacing: .08em; font-size: .68rem; color: var(--fd-muted); }
[data-testid="stMetric"] {
  background: var(--fd-surface); border: 1px solid var(--fd-border);
  border-radius: var(--fd-radius); padding: 14px 16px; box-shadow: var(--fd-shadow);
}

/* page header component */
.fd-header { margin: 0 0 1.4rem 0; padding-bottom: 1.0rem;
  border-bottom: 1px solid var(--fd-border); }
.fd-eyebrow { font-family: var(--font-mono); font-size: .72rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: .18em; color: var(--fd-primary-deep);
  display: inline-flex; align-items: center; gap: .5rem; }
.fd-eyebrow::before { content: ""; width: 22px; height: 2px; border-radius: 2px;
  background: linear-gradient(90deg, var(--fd-primary), var(--fd-amber)); }
.fd-title { font-family: var(--font-display); font-size: 2.0rem; font-weight: 700;
  line-height: 1.1; margin: .35rem 0 .25rem 0; color: var(--fd-ink); letter-spacing: -0.025em; }
.fd-sub { color: var(--fd-muted); font-size: .98rem; margin: 0; max-width: 60ch; }

/* sidebar */
[data-testid="stSidebar"] { background: var(--fd-surface); border-right: 1px solid var(--fd-border); }
.fd-brand { font-family: var(--font-display); font-weight: 700; font-size: 1.45rem;
  letter-spacing: -0.02em; line-height: 1; margin: .2rem 0 .1rem 0; }
.fd-brand .bolt { background: linear-gradient(120deg, var(--fd-primary), var(--fd-amber));
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; }
.fd-brand-tag { font-family: var(--font-mono); font-size: .66rem; text-transform: uppercase;
  letter-spacing: .16em; color: var(--fd-muted); margin-bottom: .4rem; }

/* sidebar radio -> nav menu */
[data-testid="stSidebar"] .stRadio > label { display: none; }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] { gap: 2px; }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label {
  width: 100%; padding: 9px 12px; border-radius: 10px; cursor: pointer;
  font-weight: 500; color: var(--fd-ink); transition: background .12s ease, color .12s ease; }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:hover { background: #EEF4F7; }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label > div:first-child { display: none; }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > label:has(input:checked) {
  background: rgba(6,182,212,.10); color: var(--fd-primary-deep); font-weight: 600;
  box-shadow: inset 3px 0 0 var(--fd-primary); }

/* buttons */
.stButton > button, .stDownloadButton > button {
  border-radius: 10px; font-weight: 600; border: 1px solid var(--fd-border);
  transition: transform .05s ease, box-shadow .12s ease, border-color .12s ease; }
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: var(--fd-primary); box-shadow: var(--fd-shadow); }
.stButton > button[kind="primary"] {
  background: linear-gradient(120deg, var(--fd-primary), var(--fd-primary-deep));
  border: none; color: white; }

/* tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid var(--fd-border); }
.stTabs [data-baseweb="tab"] { font-family: var(--font-display); font-weight: 600; }
.stTabs [aria-selected="true"] { color: var(--fd-primary-deep); }

/* expanders & inputs */
[data-testid="stExpander"] { border: 1px solid var(--fd-border); border-radius: var(--fd-radius);
  background: var(--fd-surface); }
[data-testid="stFileUploaderDropzone"] { border-radius: var(--fd-radius); }

/* status badge */
.fd-badge { display: inline-flex; align-items: center; gap: .45rem; font-family: var(--font-mono);
  font-size: .76rem; font-weight: 600; padding: 3px 10px; border-radius: 999px;
  border: 1px solid var(--fd-border); background: var(--fd-surface); }
.fd-badge .dot { width: 8px; height: 8px; border-radius: 50%; }

/* home hero + pipeline */
.fd-hero { padding: .4rem 0 1.4rem 0; }
.fd-hero-title { font-family: var(--font-display); font-weight: 700; font-size: 2.9rem;
  line-height: 1.04; letter-spacing: -0.035em; margin: .45rem 0 .5rem; color: var(--fd-ink);
  max-width: 18ch; }
.fd-hero-sub { color: var(--fd-muted); font-size: 1.12rem; max-width: 56ch; margin: 0; }
.fd-section-label { font-family: var(--font-mono); font-size: .72rem; font-weight: 600;
  text-transform: uppercase; letter-spacing: .16em; color: var(--fd-muted); margin: 1.4rem 0 .6rem; }
.fd-pipeline { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.fd-step { background: var(--fd-surface); border: 1px solid var(--fd-border);
  border-radius: var(--fd-radius); padding: 16px 16px 18px; box-shadow: var(--fd-shadow);
  position: relative; overflow: hidden; }
.fd-step::before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
  background: linear-gradient(180deg, var(--fd-primary), var(--fd-amber)); }
.fd-step .num { font-family: var(--font-mono); font-size: .68rem; font-weight: 600;
  letter-spacing: .14em; color: var(--fd-primary-deep); }
.fd-step .ic { font-size: 1.5rem; line-height: 1; margin-top: .35rem; }
.fd-step .nm { font-family: var(--font-display); font-weight: 600; font-size: 1.04rem; margin-top: .35rem; }
.fd-step .ds { color: var(--fd-muted); font-size: .82rem; margin-top: .25rem; line-height: 1.35; }
.fd-algos { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.fd-algo { background: var(--fd-surface); border: 1px solid var(--fd-border);
  border-radius: var(--fd-radius); padding: 14px 16px; }
.fd-algo .role { font-family: var(--font-mono); font-size: .64rem; text-transform: uppercase;
  letter-spacing: .12em; color: var(--fd-muted); }
.fd-algo .nm { font-family: var(--font-display); font-weight: 600; margin-top: .25rem; font-size: 1.0rem; }
.fd-algo a { color: var(--fd-primary-deep); text-decoration: none; }
@media (max-width: 900px) {
  .fd-pipeline { grid-template-columns: repeat(2, 1fr); }
  .fd-algos { grid-template-columns: 1fr; }
  .fd-hero-title { font-size: 2.2rem; }
}
</style>
"""


def inject_theme() -> None:
    """Inject fonts + design-system CSS. Call once, early, on every page."""
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(eyebrow: str, title: str, subtitle: str | None = None) -> None:
    """Pipeline-stage page header: mono eyebrow + display title + muted subtitle."""
    sub = f'<p class="fd-sub">{subtitle}</p>' if subtitle else ""
    eb = f'<div class="fd-eyebrow">{eyebrow}</div>' if eyebrow else ""
    st.markdown(
        f'<div class="fd-header">{eb}'
        f'<div class="fd-title">{title}</div>{sub}</div>',
        unsafe_allow_html=True,
    )


_BADGE_COLORS = {
    "completed": "var(--fd-success)",
    "running": "var(--fd-running)",
    "failed": "var(--fd-failed)",
    "unknown": "var(--fd-muted)",
}


def status_badge(state: str, label: str | None = None) -> str:
    """Return HTML for a colored status pill (use with unsafe_allow_html)."""
    color = _BADGE_COLORS.get(state, "var(--fd-muted)")
    text = label or state.upper()
    return (
        f'<span class="fd-badge"><span class="dot" style="background:{color}"></span>'
        f'{text}</span>'
    )


def sidebar_brand(tagline: str) -> None:
    """Render the FLASH_DOCK wordmark + tagline at the top of the sidebar."""
    st.sidebar.markdown(
        f'<div class="fd-brand">FLASH<span class="bolt">_</span>DOCK '
        f'<span class="bolt">⚡</span></div>'
        f'<div class="fd-brand-tag">{tagline}</div>',
        unsafe_allow_html=True,
    )
