import time
import uuid
import streamlit as st
from pipeline import stream_agent_response

st.set_page_config(
    layout="centered"
)

if "chats" not in st.session_state:
    first_chat_id = str(uuid.uuid4())
    st.session_state.chats = {
        first_chat_id: {
            "title": "New Chat",
            "messages": [],
            "updated_at": time.time()
        }
    }
    st.session_state.current_chat_id = first_chat_id

current_chat = st.session_state.chats[st.session_state.current_chat_id]
messages = current_chat["messages"]


@st.dialog("Clear Chat")
def clear_chat_dialog():
    st.write("Do you want to clear the messages in this chat or delete the entire chat?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clear messages", use_container_width=True):
            current_chat["messages"] = []
            current_chat["title"] = "New Chat"
            current_chat["updated_at"] = time.time()
            st.rerun()
    with col2:
        if st.button("Delete chat", use_container_width=True):
            del st.session_state.chats[st.session_state.current_chat_id]
            if not st.session_state.chats:
                new_id = str(uuid.uuid4())
                st.session_state.chats[new_id] = {
                    "title": "New Chat",
                    "messages": [],
                    "updated_at": time.time()
                }
                st.session_state.current_chat_id = new_id
            else:
                remaining = sorted(
                    st.session_state.chats.items(),
                    key=lambda item: item[1].get("updated_at", 0),
                    reverse=True
                )
                st.session_state.current_chat_id = remaining[0][0]
            st.rerun()


with st.sidebar:
    if st.button("+ New Chat", use_container_width=True):
        new_chat_id = str(uuid.uuid4())
        st.session_state.chats[new_chat_id] = {
            "title": f"Chat {len(st.session_state.chats) + 1}",
            "messages": [],
            "updated_at": time.time()
        }
        st.session_state.current_chat_id = new_chat_id
        st.rerun()

    if st.button("Clear Chat", use_container_width=True):
        clear_chat_dialog()

    st.markdown("---")
    st.subheader("Previous Chats")

    sorted_chats = sorted(
        st.session_state.chats.items(),
        key=lambda item: item[1].get("updated_at", 0),
        reverse=True
    )

    for chat_id, chat_data in sorted_chats:
        is_active = (chat_id == st.session_state.current_chat_id)
        if is_active:
            st.markdown(
                f"""
                <div style="
                    background-color: #383a40;
                    border: 1.5px solid #5c6068;
                    border-radius: 8px;
                    padding: 8px 14px;
                    margin-bottom: 8px;
                    color: #f1f2f4;
                    font-weight: 600;
                    font-size: 14px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                ">
                    {chat_data['title']}
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            if st.button(chat_data["title"], key=f"chat_{chat_id}", use_container_width=True):
                st.session_state.current_chat_id = chat_id
                st.rerun()

st.title("AI Chatbot")

for message in messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Type your message here...")

if user_input:
    if not messages:
        trimmed = user_input.strip()
        current_chat["title"] = trimmed[:28] + ("..." if len(trimmed) > 28 else "")

    messages.append({"role": "user", "content": user_input})
    current_chat["updated_at"] = time.time()

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            response_stream = stream_agent_response(messages)
            full_response = st.write_stream(response_stream)
            messages.append({"role": "assistant", "content": full_response})
            current_chat["updated_at"] = time.time()
        except Exception as error:
            st.error(f"Error generating response: {error}")
