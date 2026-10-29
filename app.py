import os, json, re, io
import pandas as pd
import streamlit as st
from utils.document_loader import extract_text
from utils.test_engine import generate_test_cases, analyze_coverage, demo_test_cases

st.set_page_config(page_title="AI TestPilot", page_icon="🧪", layout="wide")
st.title("🧪 AI TestPilot")
st.caption("AI-powered QA Test Case Generator & Analyzer | TCS AI Friday Season 2")

with st.sidebar:
    st.header("Configuration")
    api_key = st.text_input("Google Gemini API key", type="password",
                            value=os.getenv("GOOGLE_API_KEY", ""))
    model_name = st.selectbox("Model", ["gemini-2.5-flash", "gemini-2.0-flash"], index=0)
    use_demo = st.toggle("Use demo mode (no API key)", value=not bool(api_key))
    st.divider()
    st.markdown("**Workflow**")
    st.write("1. Add requirements")
    st.write("2. Generate test cases")
    st.write("3. Analyze coverage")
    st.write("4. Review and export")

tab1, tab2, tab3 = st.tabs(["📄 Requirements", "🧪 Test Cases", "📊 Coverage Analysis"])

with tab1:
    st.subheader("Upload requirements or paste them")
    uploads = st.file_uploader("Upload files", type=["txt","md","pdf","docx","csv","xlsx"], accept_multiple_files=True)
    pasted = st.text_area("Or paste user stories / requirements", height=180,
        placeholder="Example: As a customer, I want to log in using email and password...")
    requirement_text = pasted.strip()
    if uploads:
        extracted = []
        for f in uploads:
            try:
                content = extract_text(f)
                if content.strip():
                    extracted.append(f"### Source: {f.name}\n{content}")
            except Exception as e:
                st.error(f"Could not read {f.name}: {e}")
        if extracted:
            requirement_text = "\n\n".join([requirement_text] + extracted).strip()
    st.session_state["requirements"] = requirement_text
    if requirement_text:
        st.success(f"Requirements ready ({len(requirement_text.split())} words).")
        with st.expander("Preview extracted requirements"):
            st.text(requirement_text[:12000])
    else:
        st.info("Upload a document or paste requirements to begin.")

    col1, col2 = st.columns(2)
    with col1:
        count = st.slider("Target number of test cases", min_value=5, max_value=40, value=15, step=5)
    with col2:
        include_types = st.multiselect("Test types", ["Positive", "Negative", "Boundary", "Functional", "Security", "Usability", "Regression"],
                                       default=["Positive","Negative","Boundary","Functional","Regression"])
    if st.button("✨ Generate test cases", type="primary", disabled=not bool(requirement_text)):
        try:
            if use_demo or not api_key:
                cases = demo_test_cases(requirement_text, count, include_types)
                st.session_state["mode"] = "Demo mode"
            else:
                cases = generate_test_cases(requirement_text, count, include_types, api_key, model_name)
                st.session_state["mode"] = f"Gemini: {model_name}"
            st.session_state["cases"] = cases
            st.session_state["analysis"] = analyze_coverage(requirement_text, cases)
            st.success(f"Generated {len(cases)} test cases using {st.session_state['mode']}.")
        except Exception as e:
            st.error(f"Generation failed: {e}")
            st.info("Try demo mode or check your API key and network access.")

with tab2:
    st.subheader("Review and edit generated test cases")
    cases = st.session_state.get("cases", [])
    if cases:
        df = pd.DataFrame(cases)
        edited = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic",
                                column_config={
                                    "priority": st.column_config.SelectboxColumn(options=["Critical","High","Medium","Low"]),
                                    "test_type": st.column_config.SelectboxColumn(options=["Positive","Negative","Boundary","Functional","Security","Usability","Regression","Other"]),
                                    "status": st.column_config.SelectboxColumn(options=["Not Run","Pass","Fail","Blocked"])
                                })
        st.session_state["cases"] = edited.fillna("").to_dict(orient="records")
        c1, c2 = st.columns(2)
        with c1:
            csv_bytes = edited.to_csv(index=False).encode("utf-8")
            st.download_button("⬇️ Download CSV", csv_bytes, "ai_testpilot_test_cases.csv", "text/csv")
        with c2:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                edited.to_excel(writer, index=False, sheet_name="Test Cases")
            st.download_button("⬇️ Download Excel", output.getvalue(), "ai_testpilot_test_cases.xlsx",
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.caption(f"Generation mode: {st.session_state.get('mode','Not generated')}")
    else:
        st.info("Generate test cases in the Requirements tab first.")

with tab3:
    st.subheader("Coverage and quality analysis")
    cases = st.session_state.get("cases", [])
    if cases:
        analysis = analyze_coverage(st.session_state.get("requirements",""), cases)
        total = len(cases)
        critical = sum(1 for x in cases if str(x.get("priority","")).lower() == "critical")
        high = sum(1 for x in cases if str(x.get("priority","")).lower() == "high")
        duplicates = analysis["duplicate_pairs"]
        gaps = analysis["coverage_gaps"]
        a,b,c,d = st.columns(4)
        a.metric("Total test cases", total)
        b.metric("Critical priority", critical)
        c.metric("High priority", high)
        d.metric("Potential duplicates", len(duplicates))
        st.progress(min(1.0, analysis["coverage_score"]/100))
        st.write(f"**Requirement coverage estimate:** {analysis['coverage_score']}%")
        st.caption("This is a keyword-based MVP estimate, not a formal proof of coverage. Validate mappings with a QA reviewer.")
        st.markdown("#### Coverage gaps / requirement signals")
        if gaps:
            for gap in gaps:
                st.warning(gap)
        else:
            st.success("No obvious uncovered requirement signals detected by the MVP analyzer.")
        st.markdown("#### Potential duplicate test cases")
        if duplicates:
            for x,y,reason in duplicates:
                st.write(f"- **{x}** and **{y}** — {reason}")
        else:
            st.success("No obvious duplicate titles detected.")
        st.markdown("#### Priority distribution")
        priority_df = pd.DataFrame([{"Priority": p, "Count": sum(1 for x in cases if x.get("priority")==p)}
                                    for p in ["Critical","High","Medium","Low"]])
        st.bar_chart(priority_df.set_index("Priority"))
    else:
        st.info("Generate test cases first to view analysis.")

st.divider()
st.caption("Prototype note: AI-generated test cases are suggestions. QA review is required before production use.")
