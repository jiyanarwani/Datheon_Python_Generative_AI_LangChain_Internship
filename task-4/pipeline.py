import math
import os
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

ddg_search = DuckDuckGoSearchRun()


def extract_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            elif hasattr(item, "text"):
                parts.append(str(getattr(item, "text")))
        return "".join(parts)
    return str(content) if content is not None else ""


@tool
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo for facts, news, and current info."""
    try:
        results = ddg_search.invoke(query)
        return results[:1500] if results else "No results found."
    except Exception as err:
        return f"Search error: {err}"


@tool
def calculator(expression: str) -> str:
    """Evaluate math expressions in Python."""
    try:
        safe_env = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
        safe_env.update({
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow
        })
        return str(eval(expression, {"__builtins__": {}}, safe_env))
    except Exception as err:
        return f"Calculation error: {err}"


@tool
def read_file(file_path: str) -> str:
    """Read local text files."""
    if not os.path.exists(file_path):
        return f"File '{file_path}' not found."
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as err:
        return f"Error reading file '{file_path}': {err}"


tools = [web_search, calculator, read_file]
tools_map = {t.name: t for t in tools}

SYSTEM_PROMPT = """You are a helpful AI assistant.
You can use tools to search the web, calculate math, or read local files when needed.
Format your responses clearly with Markdown."""


def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GOOGLE_API_KEY in .env file.")

    os.environ["GOOGLE_API_KEY"] = api_key.strip()
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    return ChatGoogleGenerativeAI(
        model=model_name,
        api_key=api_key.strip(),
        temperature=0.2
    )


def stream_agent_response(chat_history):
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for msg in chat_history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    response = llm_with_tools.invoke(messages)

    if response.tool_calls:
        messages.append(response)
        for tool_call in response.tool_calls:
            name = tool_call["name"]
            args = tool_call["args"]
            tool_id = tool_call["id"]

            if name in tools_map:
                try:
                    tool_output = tools_map[name].invoke(args)
                except Exception as err:
                    tool_output = f"Tool failed: {err}"
            else:
                tool_output = f"Unknown tool: {name}"

            messages.append(
                ToolMessage(content=str(tool_output), tool_call_id=tool_id)
            )

        for chunk in llm.stream(messages):
            text = extract_text(chunk.content)
            if text:
                yield text
    else:
        for chunk in llm.stream(messages):
            text = extract_text(chunk.content)
            if text:
                yield text
