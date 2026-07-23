"""
app.py — NGX Intelligence Workspace (controller / entry point).

Single-controller Streamlit app: global config + CSS, a sidebar navigator, and
routing to view modules. Run with:  streamlit run app.py
"""
from __future__ import annotations
import streamlit as st

from ngx import config, state
from ngx.config import THEME
from ngx.views import home, company, compare, rankings, glossary_view

st.set_page_config(page_title=config.APP_NAME, page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")


def _css() -> None:
    st.markdown(
        f"""<style>
        .stApp {{ background:{THEME['bg']}; }}
        .block-container {{ padding-top:2.4rem; padding-bottom:3rem; max-width:1180px; }}
        section[data-testid="stSidebar"] {{ background:{THEME['panel']}; border-right:1px solid {THEME['border']}; }}
        h1,h2,h3,h4 {{ color:{THEME['text']}; }}
        /* list-style buttons */
        .stButton > button {{
            background:transparent; border:1px solid transparent; color:{THEME['text']};
            text-align:left; justify-content:flex-start; padding:4px 8px; font-size:13.5px;
            border-radius:6px; font-weight:400;
        }}
        .stButton > button:hover {{ background:{THEME['panel2']}; border-color:{THEME['border']}; color:{THEME['text']}; }}
        div[data-testid="stExpander"] {{ border:1px solid {THEME['border']}; border-radius:8px; background:{THEME['panel']}; }}
        .stTabs [data-baseweb="tab-list"] {{ gap:4px; }}
        .stTabs [data-baseweb="tab"] {{ color:{THEME['muted']}; }}
        [data-testid="stMetricValue"] {{ color:{THEME['text']}; }}
        </style>""",
        unsafe_allow_html=True,
    )


def _sidebar() -> None:
    with st.sidebar:
        st.markdown(f"<div style='font-size:18px;font-weight:800;color:{THEME['text']}'>📊 NGX</div>"
                    f"<div style='color:{THEME['muted']};font-size:12px;margin-bottom:14px'>"
                    "Intelligence Workspace</div>", unsafe_allow_html=True)
        st.radio("Navigate", state.PAGES, key="nav_radio", label_visibility="collapsed")

        if st.session_state.get("company"):
            st.markdown("---")
            st.caption("Current company")
            st.markdown(f"**{config.display_name(st.session_state['company'])}**")

        st.markdown("---")
        st.caption("35 companies · 12 sectors · 2021–2025 · offline dataset. "
                   "Educational prototype, not investment advice.")


def main() -> None:
    state.init()
    state.apply_pending()   # consume queued navigation before any widget exists
    _css()
    _sidebar()

    from ngx import ui
    ui.disclaimer()

    router = {
        "Home": home.render,
        "Company": company.render,
        "Compare": compare.render,
        "Rankings": rankings.render,
        "Glossary": glossary_view.render,
    }
    router.get(state.current_page(), home.render)()


if __name__ == "__main__":
    main()
