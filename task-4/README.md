# AI Chatbot - Streamlit & LangChain (Task 4)
A responsive conversational web application wrapping a LangChain agent pipeline into Streamlit, featuring real-time streaming token output, multi-turn chat history and clear session state management.

## Technical Approach & Features
- **Streamlit Chat Components**: Built using `st.chat_message` and `st.chat_input` for a responsive, interactive chat experience.
- **Real-Time Token Streaming**: Streams responses token by token directly to the UI using Streamlit's native `st.write_stream` and LangChain's streaming generator.
- **Session State Management**: Uses `st.session_state` to store and persist conversation history across user interactions so the model retains multi-turn context.
- **Session Controls**: Left sidebar with `+ New Chat`, previous chat history sorted by recent activity, and a `Clear Chat` confirmation dialog to clear messages or delete sessions.
- **Integrated Agent Tools**: Equipped with DuckDuckGo web search, a Python math calculator and a local file reader.
