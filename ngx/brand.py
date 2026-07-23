"""
brand.py — Lucent visual identity: logo mark + global design system (CSS).

Kept in one place so the look is consistent and the brand is easy to evolve.
The CSS leans on the research-backed premium pattern: dark-first deep charcoal,
one restrained accent (warm gold), editorial serif for headline numbers, Inter
for UI, generous spacing, and Streamlit's default chrome stripped away.
"""
from __future__ import annotations
from .config import THEME, BRAND


def logo_mark(size: int = 22, color: str | None = None, glow: bool = True) -> str:
    """A luminous 4-point spark — the Lucent mark."""
    c = color or THEME["accent"]
    gid = f"lux{size}"
    flt = (f"<filter id='{gid}g' x='-50%' y='-50%' width='200%' height='200%'>"
           f"<feGaussianBlur stdDeviation='1.4' result='b'/>"
           f"<feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter>") if glow else ""
    fltref = f"filter='url(#{gid}g)'" if glow else ""
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 24 24' fill='none' "
        f"xmlns='http://www.w3.org/2000/svg' style='vertical-align:middle'>"
        f"<defs>{flt}</defs>"
        f"<path d='M12 1.5 C12 6.6 12.4 9.6 14.4 11.6 C16.4 13.6 17.4 12 22.5 12 "
        f"C17.4 12 16.4 10.4 14.4 12.4 C12.4 14.4 12 17.4 12 22.5 "
        f"C12 17.4 11.6 14.4 9.6 12.4 C7.6 10.4 6.6 12 1.5 12 "
        f"C6.6 12 7.6 13.6 9.6 11.6 C11.6 9.6 12 6.6 12 1.5 Z' "
        f"fill='{c}' {fltref}/></svg>"
    )


def wordmark(size: int = 20) -> str:
    """Logo mark + 'Lucent' wordmark for the sidebar / hero."""
    return (
        f"<div style='display:flex;align-items:center;gap:9px;'>"
        f"{logo_mark(size + 4)}"
        f"<span style=\"font-family:'Fraunces',serif;font-weight:600;font-size:{size}px;"
        f"letter-spacing:.2px;color:{THEME['text']}\">{BRAND}</span></div>"
    )


def global_css() -> str:
    t = THEME
    return f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,600&display=swap');

    :root {{
      --bg:{t['bg']}; --panel:{t['panel']}; --panel2:{t['panel2']}; --panel3:{t['panel3']};
      --border:{t['border']}; --border2:{t['border2']}; --text:{t['text']}; --muted:{t['muted']};
      --faint:{t['faint']}; --accent:{t['accent']}; --accent-soft:{t['accent_soft']};
      --pos:{t['pos']}; --neg:{t['neg']}; --grid:{t['grid']};
    }}

    /* --- base --- */
    html, body, .stApp, [class*="css"] {{ font-family:'Inter',system-ui,-apple-system,sans-serif; }}
    .stApp {{ background:
        radial-gradient(1200px 600px at 80% -10%, #14161c 0%, rgba(20,22,28,0) 55%),
        {t['bg']}; }}
    .block-container {{ padding-top:1.6rem; padding-bottom:4rem; max-width:1200px; }}
    h1,h2 {{ font-family:'Fraunces',Georgia,serif; font-weight:600; letter-spacing:.2px; color:{t['text']}; }}
    h3,h4,h5 {{ font-family:'Inter',sans-serif; font-weight:600; color:{t['text']}; }}
    a, a:visited {{ color:{t['accent']}; text-decoration:none; }}
    a:hover {{ text-decoration:underline; }}
    hr {{ border-color:{t['border']}; }}
    .lux-num {{ font-family:'Fraunces',Georgia,serif; font-feature-settings:'tnum'; }}

    /* --- strip Streamlit chrome (keep header so the mobile sidebar toggle survives) --- */
    #MainMenu, [data-testid="stMainMenu"], [data-testid="stAppDeployButton"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"], footer {{ display:none !important; }}
    header[data-testid="stHeader"] {{ background:transparent !important; }}
    [data-testid="stAppViewBlockContainer"] {{ padding-top:1.4rem; }}

    /* --- sidebar --- */
    section[data-testid="stSidebar"] {{ background:{t['bg2']}; border-right:1px solid {t['border']}; width:250px !important; }}
    section[data-testid="stSidebar"] .block-container {{ padding-top:1.3rem; }}
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    section[data-testid="stSidebar"] .stCaption, .stCaption, [data-testid="stCaptionContainer"] {{ color:{t['faint']}; }}

    /* nav radio -> menu rows */
    section[data-testid="stSidebar"] div[role="radiogroup"] {{ gap:3px; margin-top:2px; }}
    section[data-testid="stSidebar"] label[data-testid="stRadioOption"] {{
        padding:8px 11px; border-radius:9px; width:100%; margin:0; cursor:pointer;
        transition:background .12s; border:1px solid transparent;
    }}
    section[data-testid="stSidebar"] label[data-testid="stRadioOption"] div[data-testid="stMarkdownContainer"] p {{
        font-size:14px; font-weight:500; color:{t['muted']}; margin:0; }}
    section[data-testid="stSidebar"] label[data-testid="stRadioOption"]:hover {{ background:{t['panel2']}; }}
    section[data-testid="stSidebar"] label[data-testid="stRadioOption"]:hover div[data-testid="stMarkdownContainer"] p {{ color:{t['text']}; }}
    section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] {{
        background:{t['accent_soft']}; border-color:{t['border2']}; }}
    section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] div[data-testid="stMarkdownContainer"] p {{
        color:{t['accent']}; font-weight:600; }}

    /* --- buttons: ghost list style by default --- */
    .stButton > button {{
        background:transparent; border:1px solid transparent; color:{t['text']};
        text-align:left; justify-content:flex-start; padding:6px 10px; font-size:13.5px;
        border-radius:8px; font-weight:500; transition:background .12s,border-color .12s;
    }}
    .stButton > button:hover {{ background:{t['panel2']}; border-color:{t['border']}; color:{t['text']}; }}
    .stButton > button:focus {{ box-shadow:none; color:{t['text']}; }}
    .stButton > button[kind="primary"] {{
        background:{t['accent']}; color:#151208; border:none; font-weight:600; justify-content:center;
    }}
    .stButton > button[kind="primary"]:hover {{ background:#f0c766; color:#151208; }}

    /* --- inputs / selects --- */
    div[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input {{
        background:{t['panel']} !important; border-color:{t['border']} !important; border-radius:9px !important;
        color:{t['text']} !important;
    }}
    div[data-baseweb="select"] > div:hover {{ border-color:{t['border2']} !important; }}
    label, .stSelectbox label, .stMultiSelect label {{ color:{t['muted']} !important; font-size:13px; }}

    /* --- expanders --- */
    details[data-testid="stExpander"], div[data-testid="stExpander"] {{
        border:1px solid {t['border']}; border-radius:10px; background:{t['panel']}; }}
    div[data-testid="stExpander"] summary:hover {{ color:{t['accent']}; }}

    /* --- tabs --- */
    .stTabs [data-baseweb="tab-list"] {{ gap:22px; border-bottom:1px solid {t['border']}; }}
    .stTabs [data-baseweb="tab"] {{ color:{t['muted']}; font-weight:500; padding:8px 2px; }}
    .stTabs [aria-selected="true"] {{ color:{t['text']} !important; }}
    .stTabs [data-baseweb="tab-highlight"] {{ background:{t['accent']} !important; }}

    /* --- misc --- */
    [data-testid="stMetricValue"] {{ color:{t['text']}; }}
    ::-webkit-scrollbar {{ width:10px; height:10px; }}
    ::-webkit-scrollbar-thumb {{ background:{t['border2']}; border-radius:6px; }}
    ::-webkit-scrollbar-track {{ background:transparent; }}
    .stAlert {{ border-radius:10px; }}

    /* responsive: reflow columns and tighten on small screens */
    @media (max-width:680px) {{
        .block-container {{ padding-left:.7rem; padding-right:.7rem; }}
        h1 {{ font-size:1.7rem !important; }}
        /* let Streamlit column rows wrap instead of squeezing */
        [data-testid="stHorizontalBlock"] {{ flex-wrap:wrap !important; gap:.5rem !important; }}
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
            flex:1 1 44% !important; min-width:44% !important; }}
        [data-testid="stMetric"], .lux-num {{ overflow-wrap:anywhere; }}
    }}
    @media (max-width:520px) {{
        [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ flex-basis:100% !important; min-width:100% !important; }}
    }}
    </style>"""
