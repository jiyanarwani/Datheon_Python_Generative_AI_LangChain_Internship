import argparse
import math
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")

import requests
from dotenv import load_dotenv
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

ddg_search = DuckDuckGoSearchRun()


def fetch_live_weather(query: str) -> str:
    patterns = [
        r'(?:weather|temperature|temp)\s+(?:in|of|for|at)?\s*([a-zA-Z\s]+)',
        r'([a-zA-Z\s]+?)\s+(?:weather|temperature|temp)'
    ]
    city = None
    for p in patterns:
        m = re.search(p, query, re.I)
        if m:
            clean = re.sub(r'\b(what|is|the|today|todays|now|current|in|of|for|at|celsius|fahrenheit|degree|degrees)\b', '', m.group(1), flags=re.I).strip()
            if clean and len(clean) > 2:
                city = clean
                break

    if not city:
        return ""

    try:
        data = requests.get(f"https://wttr.in/{city}?format=j1", timeout=4).json()
        curr = data["current_condition"][0]
        temp_c = curr["temp_C"]
        temp_f = curr["temp_F"]
        desc = curr["weatherDesc"][0]["value"].strip()
        humidity = curr["humidity"]
        wind = curr["windspeedKmph"]
        loc = data.get("nearest_area", [{}])[0].get("areaName", [{}])[0].get("value", city.title())
        return f"[Live Weather] {loc}: {desc}, {temp_c}°C ({temp_f}°F), Humidity: {humidity}%, Wind: {wind} km/h\n"
    except Exception:
        return ""


@tool
def web_search(query: str, thought: str = "") -> str:
    """Search the web using DuckDuckGo for live facts, current events, or real-time info."""
    res_list = []
    if any(w in query.lower() for w in ("weather", "temperature", "temp")):
        live_w = fetch_live_weather(query)
        if live_w:
            res_list.append(live_w)

    try:
        search_res = ddg_search.invoke(query)
        if search_res:
            res_list.append(search_res[:1500])
    except Exception as e:
        res_list.append(f"Search failed: {e}")

    return "\n".join(res_list).strip() or "No results found."


math_safe_env = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
math_safe_env.update({
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "pow": pow,
})

@tool
def calculator(expression: str, thought: str = "") -> str:
    """Evaluate a mathematical expression in Python. Supports basic arithmetic, sqrt, pow, trig, etc."""
    try:
        ans = eval(expression, {"__builtins__": {}, "math": math}, math_safe_env)
        return str(ans)
    except Exception as err:
        return f"Calculation error: {err}"


@tool
def read_file(file_path: str, thought: str = "") -> str:
    """Read and return content from a local text file."""
    if not os.path.exists(file_path):
        return f"File '{file_path}' not found."
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as err:
        return f"Error reading file '{file_path}': {err}"


tools = [web_search, calculator, read_file]
tools_map = {t.name: t for t in tools}

SYSTEM_PROMPT = """You are a helpful research agent equipped with:
- web_search: real-time DuckDuckGo web search
- calculator: math computation tool
- read_file: local file reader

Instructions:
- Provide your reasoning in the 'thought' field before making tool calls.
- Avoid repetitive or redundant searches. Once you have enough information, stop and produce the answer.
- Prefix your completed response with 'Final Answer: '."""


def get_text_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for item in content:
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict) and "text" in item:
                out.append(str(item["text"]))
            elif hasattr(item, "text"):
                out.append(str(getattr(item, "text")))
            else:
                out.append(str(item))
        return "".join(out)
    return str(content) if content is not None else ""


def build_model():
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        print("[!] Missing GOOGLE_API_KEY / GEMINI_API_KEY in environment or .env file.")
        sys.exit(1)

    os.environ["GOOGLE_API_KEY"] = key.strip()
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    base_llm = ChatGoogleGenerativeAI(
        model=model_name,
        api_key=key.strip(),
        temperature=0.0
    )
    return base_llm, base_llm.bind_tools(tools)


def run_agent_stream(query: str, max_steps: int = 8):
    base_llm, llm_with_tools = build_model()
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=query)
    ]

    for _ in range(max_steps):
        res = llm_with_tools.invoke(messages)
        messages.append(res)

        if not res.tool_calls:
            text = get_text_content(res.content).strip()
            if text.startswith("Final Answer:"):
                text = text[len("Final Answer:"):].strip()
            yield {"type": "final_answer", "content": text}
            return

        for call in res.tool_calls:
            name = call["name"]
            args = call["args"]
            call_id = call["id"]

            thought = args.get("thought", "").strip()
            if not thought:
                text_block = get_text_content(res.content).strip()
                thought = text_block if text_block else f"Invoking {name} to get data."

            yield {"type": "thought", "content": thought}

            call_args = {k: v for k, v in args.items() if k != "thought"}
            args_repr = ", ".join(f"{k}={repr(v)}" for k, v in call_args.items())
            yield {"type": "action", "content": f"{name}({args_repr})"}

            if name in tools_map:
                obs = tools_map[name].invoke(args)
            else:
                obs = f"Unknown tool: {name}"

            obs_text = str(obs).strip()
            yield {"type": "observation", "content": obs_text}
            messages.append(ToolMessage(content=obs_text, tool_call_id=call_id))

    # If steps run out, synthesize answer from collected context
    messages.append(HumanMessage(content="Step limit reached. Please provide your Final Answer using the information retrieved above."))
    synth_res = base_llm.invoke(messages)
    text = get_text_content(synth_res.content).strip()
    if text.startswith("Final Answer:"):
        text = text[len("Final Answer:"):].strip()
    yield {"type": "final_answer", "content": text}


def run_agent(query: str, max_steps: int = 8) -> str:
    print(f"\nUser Query: {query}")
    print("-" * 50)
    final_ans = ""

    for step in run_agent_stream(query, max_steps=max_steps):
        stype = step["type"]
        val = step["content"]

        if stype == "thought":
            print(f"Thought: {val}")
        elif stype == "action":
            print(f"Action: {val}")
        elif stype == "observation":
            preview = val if len(val) <= 250 else val[:250] + "... [truncated]"
            print(f"Observation: {preview}\n")
        elif stype == "final_answer":
            final_ans = val
            print(f"Final Answer: {val}")
            print("-" * 50)

    return final_ans


def main():
    parser = argparse.ArgumentParser(description="LangChain Agent CLI")
    parser.add_argument("--query", "-q", type=str, help="Research query to execute")
    args = parser.parse_args()

    if args.query:
        run_agent(args.query)
        return

    print("LangChain Research Agent (Web Search, Calculator, Local File Reader)")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            q = input("Query > ").strip()
            if not q:
                continue
            if q.lower() in ("exit", "quit", "q"):
                break
            run_agent(q)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break


if __name__ == "__main__":
    main()
