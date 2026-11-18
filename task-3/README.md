# LangChain Research Agent (Task 3)

A Python-based AI agent built with LangChain that uses function calling to autonomously pick and run tools for compound queries. It displays the full reasoning chain: `Thought -> Action -> Observation -> Final Answer`.

## Features & Tools

- **Web Search (`web_search`)**: DuckDuckGo search for live web lookups, with real-time weather observation support.
- **Calculator (`calculator`)**: Evaluates mathematical expressions using Python's `math` library.
- **File Reader (`read_file`)**: Reads local files and returns their text contents.

Both a **Command Line Interface (CLI)** and a **Streamlit Web UI** are provided.

## Project Structure

```
task-3/
├── agent.py          # Core agent logic and CLI runner
├── app.py            # Streamlit web UI
├── sample.txt        # Sample text file for testing
├── requirements.txt  # Project dependencies
├── .env.example      # Example environment file
└── README.md
```

## Setup

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Create `.env` file (see `.env.example`):
   ```env
   GOOGLE_API_KEY=your_api_key_here
   GEMINI_MODEL=gemini-3.5-flash-lite
   ```

## Running the Project

### Streamlit UI
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser to run queries interactively.

### CLI Mode

Single query:
```bash
python agent.py --query "Read sample.txt, calculate the total sum of all the budget items listed in the report, and then calculate an 18% tax on that total."
```

Interactive console:
```bash
python agent.py
```

## Sample Output

```
User Query: Read sample.txt, calculate the total sum of all the budget items listed in the report, and then calculate an 18% tax on that total.
--------------------------------------------------
Thought: Read the contents of sample.txt to find the budget items and their values.
Action: read_file(file_path='sample.txt')
Observation: Project Apollo Hardware Budget Report:
- Server Infrastructure: $14,500
- Networking Equipment: $3,200
- Backup Storage Units: $4,800
- Workstations: $7,500

Thought: Calculate the total sum of all the budget items listed in the report.
Action: calculator(expression='14500 + 3200 + 4800 + 7500')
Observation: 30000

Thought: Calculate an 18% tax on the total sum (30000).
Action: calculator(expression='30000 * 0.18')
Observation: 5400.0

Final Answer: 
Based on the report in `sample.txt`, the budget items are:
- Server Infrastructure: $14,500
- Networking Equipment: $3,200
- Backup Storage Units: $4,800
- Workstations: $7,500

- Total Sum: $30,000
- 18% Tax: $5,400
--------------------------------------------------
```
