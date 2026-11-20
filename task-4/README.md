# AI Chatbot with Streamlit & LangChain (Task 4)

An interactive conversational AI web application built using **Streamlit** and **LangChain**, featuring real-time token streaming, multi-turn chat history, and clear session state management.

---

## Features

- **Streaming Token Output**: Real-time response generation using Streamlit's native `st.write_stream` connected to LangChain's streaming API.
- **Chat History & Sessions**: Multiple chat conversations organized in the left sidebar with **+ New Chat**, **Clear Chat**, and previous chats sorted by most recent activity.
- **Session State Management**: Explicit `st.session_state` management tracking messages and conversation history across turns.
- **Chat UI Components**: Clean, responsive user experience built with `st.chat_message` and `st.chat_input`.
- **Integrated Agent Tools**: Equipped with DuckDuckGo web search, a Python-based calculator, and a local file reader (`read_file`).

---

## Project Structure

```text
task-4/
├── app.py               # Streamlit chat interface and session state management
├── pipeline.py          # LangChain conversational agent pipeline & streaming generator
├── sample.txt           # Sample file for file reader testing
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables template
├── .env                 # Environment variables (API key and model)
└── README.md            # Project documentation and instructions
```

---

## Setup & Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create or verify your `.env` file in the `task-4` directory:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

---

## Running the Application

Launch the Streamlit web app with:
```bash
streamlit run app.py
```
*(Or `python -m streamlit run app.py` if `streamlit` is not in your system PATH)*

The application will start and open in your default browser at `http://localhost:8501`.

---

## Example Interactions

1. **Direct Conversational Query & Context Retention**:
   - **User**: *"My name is Maya."*
   - **Assistant**: *"Hello Maya! How can I assist you today?"*
   - **User**: *"What was my name again?"*
   - **Assistant**: *"Your name is Maya."*

2. **Tool Execution with Streaming Response**:
   - **User**: *"Calculate (14500 + 3200 + 4800) * 1.18"*
   - **Assistant**: Streams the computation and explanation token-by-token.

3. **Local File Reading**:
   - **User**: *"Read sample.txt and summarize the hardware budget report."*
   - **Assistant**: Reads `sample.txt` using the file reader tool and streams the summary.

4. **Web Search**:
   - **User**: *"What is the latest stable version of Python?"*
   - **Assistant**: Retrieves real-time results via DuckDuckGo and streams the answer.
