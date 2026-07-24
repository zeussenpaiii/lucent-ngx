"""
app.py — Lucent · NGX Financial Intelligence (controller / entry point).

Single-controller Streamlit app: global design system, a branded sidebar
navigator, and routing to view modules. Run with:  streamlit run app.py
"""
from __future__ import annotations
import streamlit as st

from ngx import config, state, brand
from ngx.config import THEME
from ngx.views import home, company, compare, rankings, screener, sector, dividends, glossary_view

st.set_page_config(page_title=f"{config.BRAND} · {config.APP_DESCRIPTOR}",
                   page_icon="◆", layout="wide", initial_sidebar_state="expanded")


def _sidebar() -> None:
    with st.sidebar:
        st.markdown(brand.wordmark(20), unsafe_allow_html=True)
        st.markdown(f"<div style='color:{THEME['faint']};font-size:11.5px;letter-spacing:.3px;"
                    f"text-transform:uppercase;margin:2px 0 16px 2px'>{config.APP_DESCRIPTOR}</div>",
                    unsafe_allow_html=True)

        st.radio("Navigate", state.PAGES, key="nav_radio", label_visibility="collapsed")

        if st.session_state.get("company"):
            comp = st.session_state["company"]
            st.markdown(f"<div style='margin-top:14px;padding:10px 12px;background:{THEME['panel']};"
                        f"border:1px solid {THEME['border']};border-radius:10px'>"
                        f"<div style='font-size:10.5px;text-transform:uppercase;letter-spacing:.4px;"
                        f"color:{THEME['faint']}'>Viewing</div>"
                        f"<div style='color:{THEME['text']};font-weight:600;font-size:14px;margin-top:2px'>"
                        f"{config.display_name(comp)}</div></div>", unsafe_allow_html=True)

        st.markdown(
            f"<div style='position:relative;margin-top:22px;padding-top:14px;border-top:1px solid {THEME['border']};"
            f"color:{THEME['faint']};font-size:11px;line-height:1.5'>"
            f"35 companies · 12 sectors · 2021–2025<br>Offline dataset · figures from filings<br>"
            f"<span style='color:{THEME['muted']}'>Educational tool — not investment advice.</span><br>"
            f"<span style='color:{THEME['faint']}'>© {config.BRAND_YEAR} {config.BRAND}</span></div>",
            unsafe_allow_html=True)


def main() -> None:
    state.init()
    state.apply_pending()   # consume queued navigation before any widget exists
    st.markdown(brand.global_css(), unsafe_allow_html=True)
    _sidebar()

    router = {
        "Home": home.render,
        "Company": company.render,
        "Compare": compare.render,
        "Sectors": sector.render,
        "Screener": screener.render,
        "Dividends": dividends.render,
        "Rankings": rankings.render,
        "Glossary": glossary_view.render,
    }
    router.get(state.current_page(), home.render)()


if __name__ == "__main__":
    main()
