from __future__ import annotations

import json
import streamlit as st

from devready.diagnostics import run_diagnostics, summarize
from devready.llm_explainer import explain_report

st.set_page_config(page_title="DevReady AI", page_icon="🩺", layout="wide")
st.title("🩺 DevReady AI")
st.caption("A Python and Linux development-environment diagnostic assistant.")

if "report" not in st.session_state:
    st.session_state.report = None

if st.button("Run diagnostics", type="primary"):
    with st.spinner("Checking your environment..."):
        st.session_state.report = run_diagnostics()

report = st.session_state.report

if report:
    summary = summarize(report)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Missing dependencies", summary["missing_dependencies"])
    c2.metric("Missing project files", summary["missing_project_files"])
    c3.metric("Failed network checks", summary["failed_network_checks"])
    c4.metric("Permission issues", summary["file_permission_issues"])

    st.subheader("Environment")
    st.json({"python": report["python"], "system": report["system"]})

    st.subheader("Dependencies")
    st.dataframe(report["dependencies"], use_container_width=True)

    st.subheader("File permissions")
    st.json(report["file_permissions"])

    st.subheader("Project files")
    st.dataframe(report["project_files"], use_container_width=True)

    st.subheader("Disk space")
    st.json(report["disk"])

    st.subheader("Network")
    st.dataframe(report["network"], use_container_width=True)

    st.subheader("Linux administration")
    st.json(report["linux"])

    st.download_button(
        "Download JSON report",
        data=json.dumps(report, indent=2),
        file_name="devready_report.json",
        mime="application/json",
    )

    if st.button("Explain findings"):
        with st.spinner("Preparing explanation..."):
            st.session_state.explanation = explain_report(report)
    if st.session_state.get("explanation"):
        st.subheader("Explanation")
        st.write(st.session_state.explanation)
else:
    st.info("Click **Run diagnostics** to scan the current environment.")

st.warning(
    "Safety: DevReady AI reports findings only. It does not automatically change permissions, "
    "install packages, mount NFS shares, or execute commands suggested by an LLM."
)
