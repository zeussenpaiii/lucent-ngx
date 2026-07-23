"""
state.py — Session state + navigation.

Streamlit reruns the whole script on every interaction and keeps widget state
under the widget's key. The sidebar navigator is an `st.radio` bound to the key
`nav_radio`, so it IS the source of truth for the current page.

Programmatic navigation (clicking a company, "add to compare", suggested
questions) can't write `nav_radio` directly from a button handler, because by
then the radio widget already exists this run. Instead handlers stash a
`_pending_nav` dict and rerun; `apply_pending()` runs at the very top of the
next run — before the radio is created — and writes the target in safely.
"""
from __future__ import annotations
import streamlit as st

PAGES = ["Home", "Company", "Compare", "Sectors", "Screener", "Rankings", "Glossary"]


def init() -> None:
    ss = st.session_state
    ss.setdefault("nav_radio", "Home")
    ss.setdefault("company", None)
    ss.setdefault("compare_set", [])


def apply_pending() -> None:
    """Consume a queued navigation before any widget is instantiated."""
    pending = st.session_state.pop("_pending_nav", None)
    if not pending:
        return
    if "page" in pending:
        st.session_state["nav_radio"] = pending["page"]
    if "company" in pending:
        st.session_state["company"] = pending["company"]


def current_page() -> str:
    return st.session_state.get("nav_radio", "Home")


def _navigate(**changes) -> None:
    st.session_state["_pending_nav"] = changes
    st.rerun()


def goto(page: str) -> None:
    _navigate(page=page)


def open_company(company: str) -> None:
    _navigate(page="Company", company=company)


def add_to_compare(company: str) -> None:
    cs = st.session_state.get("compare_set", [])
    if company not in cs:
        cs.append(company)
    st.session_state["compare_set"] = cs  # plain key — safe to set anytime
    _navigate(page="Compare")
