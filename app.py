import streamlit as st
from src.main import run_pipeline

st.set_page_config(
    page_title="Veritas | Verification Pipeline",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Veritas: Autonomous Multi-Agent Pipeline")
st.caption("Self-correcting research, synthesis, and verification agent engine")

# User Input
topic = st.text_input(
    "Research Topic",
    value="Hierarchical Agentic AI Memory Architectures in 2026",
    placeholder="Enter a topic to research and verify..."
)

if st.button("Run Verification Pipeline", type="primary"):
    if not topic.strip():
        st.warning("Please provide a valid topic.")
    else:
        with st.status("Executing Multi-Agent Workflow...", expanded=True) as status:
            st.write("🔎 Research Node: Formulating targeted search queries & collecting sources...")
            output = run_pipeline(topic)
            
            st.write("✍️ Synthesis Node: Generating cited technical report...")
            st.write(f"🛡️ Verifier Node: Verdict = **{output.get('verdict', 'UNKNOWN')}** (Iterations: {output.get('iteration', 1)})")
            status.update(label="Workflow Complete!", state="complete", expanded=False)

        # Output Layout
        col_main, col_audit = st.columns([3, 2])

        with col_main:
            st.subheader("Final Verified Report")
            st.markdown(output.get("draft", "No output generated."))

        with col_audit:
            st.subheader("Audit & Inspection")
            st.metric("Status", output.get("verdict", "N/A"))
            st.metric("Revisions Required", max(0, output.get("iteration", 1) - 1))
            
            with st.expander("Inspection: Citations & Sources", expanded=True):
                st.json(output.get("sources", []))
                
            if output.get("feedback"):
                with st.expander("Verifier Feedback History"):
                    st.write(output.get("feedback"))