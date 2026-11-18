import streamlit as st
from agent import run_agent_stream

st.set_page_config(page_title="LangChain Research Agent", layout="centered")

st.title("LangChain Research Agent")
st.caption("Equipped with DuckDuckGo Search, Math Calculator, and File Reader")

if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        if msg.get("steps"):
            with st.expander("Reasoning Chain", expanded=False):
                for step in msg["steps"]:
                    st_type = step["type"]
                    content = step["content"]
                    if st_type == "thought":
                        st.markdown(f"**Thought:** {content}")
                    elif st_type == "action":
                        st.code(content, language="python")
                    elif st_type == "observation":
                        preview = content[:200] + "..." if len(content) > 200 else content
                        st.caption(f"Observation: {preview}")
        st.markdown(msg["content"])

user_query = st.chat_input("Enter a query...")
if user_query:
    st.session_state.history.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        steps = []
        final_answer = ""

        with st.status("Thinking...", expanded=True) as status:
            for step in run_agent_stream(user_query):
                st_type = step["type"]
                content = step["content"]

                if st_type == "thought":
                    st.markdown(f"**Thought:** {content}")
                    steps.append(step)
                elif st_type == "action":
                    st.code(f"Action: {content}", language="python")
                    steps.append(step)
                elif st_type == "observation":
                    preview = content if len(content) <= 300 else content[:300] + "... [truncated]"
                    st.caption(f"Observation: {preview}")
                    steps.append(step)
                elif st_type == "final_answer":
                    final_answer = content

            status.update(label="Done", state="complete", expanded=True)

        if final_answer:
            st.markdown(final_answer)
            st.session_state.history.append({
                "role": "assistant",
                "content": final_answer,
                "steps": steps
            })
