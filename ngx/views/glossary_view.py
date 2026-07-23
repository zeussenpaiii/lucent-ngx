"""Glossary — plain-language definitions of every metric, for the educational layer."""
from __future__ import annotations
import streamlit as st

from .. import glossary
from ..config import THEME, METRICS

GROUP_LABELS = {"income": "Income statement", "balance": "Balance sheet",
                "cashflow": "Cash flow", "ratio": "Ratios", "market": "Per share / market"}


def render() -> None:
    st.markdown("## Glossary")
    st.markdown(f"<div style='color:{THEME['muted']};margin-bottom:10px'>"
                "What each metric means, how it's calculated, and how to read it.</div>",
                unsafe_allow_html=True)

    q = st.text_input("Filter", placeholder="Search a metric… (e.g. ROE, margin, debt)")
    ql = q.strip().lower()

    for group, glabel in GROUP_LABELS.items():
        keys = [k for k, m in METRICS.items() if m["group"] == group and glossary.define(k)]
        shown = []
        for k in keys:
            d = glossary.define(k)
            hay = f"{METRICS[k]['label']} {k} {d['definition']}".lower()
            if not ql or ql in hay:
                shown.append((k, d))
        if not shown:
            continue
        st.markdown(f"### {glabel}")
        for k, d in shown:
            with st.expander(METRICS[k]["label"]):
                st.markdown(f"{d['definition']}")
                st.markdown(f"<span style='color:{THEME['muted']};font-size:13px'>"
                            f"<b>Formula:</b> {d['formula']}</span>", unsafe_allow_html=True)
                st.markdown(f"<span style='color:{THEME['accent']};font-size:13px'>"
                            f"<b>How to read it:</b> {d['reading']}</span>", unsafe_allow_html=True)
