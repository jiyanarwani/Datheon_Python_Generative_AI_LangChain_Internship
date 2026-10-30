import argparse
import json
import os
import sys
import threading
from typing import Optional, Tuple, Type

from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError

import prompts
import schemas


def load_api_key() -> str:
    load_dotenv()
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key == "your_gemini_api_key_here":
        print("[Error] GEMINI_API_KEY is not set.")
        print("Please create a .env file and add your key: GEMINI_API_KEY=your_key")
        return ""
    return key


def call_gemini(api_key: str, prompt: str, schema_cls: Type[BaseModel]) -> str:
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    client = genai.Client(api_key=api_key)

    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema_cls,
        temperature=0.0,
    )

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=config,
    )
    if not response or not response.text:
        raise ValueError("Empty response received from Gemini.")
    return response.text.strip()


def validate_json_response(raw_text: str, schema_cls: Type[BaseModel]) -> BaseModel:
    # Strip markdown code fences if model wrapped the JSON
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    data = json.loads(text)
    return schema_cls.model_validate(data)


# ==============================================================================
# Command Line Interface
# ==============================================================================

def get_document_type(cli_type: Optional[str]) -> Tuple[str, Type[BaseModel]]:
    mapping = {
        "1": ("resume", schemas.Resume),
        "resume": ("resume", schemas.Resume),
        "2": ("invoice", schemas.Invoice),
        "invoice": ("invoice", schemas.Invoice),
    }

    if cli_type and cli_type.lower() in mapping:
        return mapping[cli_type.lower()]

    print("\nSelect document type:")
    print("  1. Resume Analysis")
    print("  2. Invoice Analysis")

    while True:
        choice = input("Enter choice (1 or 2): ").strip().lower()
        if choice in mapping:
            return mapping[choice]
        print("Invalid choice. Please enter 1 or 2.")


def get_input_text(cli_file: Optional[str], cli_text: Optional[str]) -> str:
    if cli_text:
        return cli_text.strip()

    if cli_file:
        if not os.path.exists(cli_file):
            print(f"[Error] File not found: {cli_file}")
            sys.exit(1)
        with open(cli_file, "r", encoding="utf-8") as f:
            return f.read().strip()

    print("\nSelect input source:")
    print("  1. Read from text file")
    print("  2. Enter text manually")

    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            path = input("Enter file path: ").strip()
            if not os.path.exists(path):
                print(f"File not found: {path}")
                continue
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()

        elif choice == "2":
            print("Enter/paste text (type 'EOF' on a new line when done):")
            lines = []
            while True:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
            text = "\n".join(lines).strip()
            if text:
                return text
            print("Input cannot be empty.")
        else:
            print("Invalid choice. Please enter 1 or 2.")


def run_cli(args: argparse.Namespace) -> None:
    api_key = load_api_key()
    if not api_key:
        sys.exit(1)

    doc_type, schema_cls = get_document_type(args.type)
    text = get_input_text(args.file, args.text)

    print(f"\nParsing {doc_type} text with Gemini...")
    prompt = prompts.build_prompt(doc_type, text)

    try:
        raw_response = call_gemini(api_key, prompt, schema_cls)
    except errors.APIError as e:
        print(f"\n[Gemini API Error] {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[Error] API call failed: {e}")
        sys.exit(1)

    try:
        validated_result = validate_json_response(raw_response, schema_cls)
    except json.JSONDecodeError as e:
        print(f"\n[Error] Model returned invalid JSON: {e}")
        sys.exit(1)
    except ValidationError as err:
        print("\n[Validation Error] Output failed Pydantic schema validation:")
        for error in err.errors():
            loc = " -> ".join(str(i) for i in error.get("loc", []))
            print(f"  Field: {loc}")
            print(f"  Error: {error.get('msg')}")
            print(f"  Input: {error.get('input')}\n")
        sys.exit(1)

    formatted_json = validated_result.model_dump_json(indent=2)
    print("\nValidated JSON Result:")
    print(formatted_json)


# ==============================================================================
# Desktop GUI (Built-in Tkinter)
# ==============================================================================

def launch_gui() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from tkinter.scrolledtext import ScrolledText

    root = tk.Tk()
    root.title("AI Document Parser - Strict JSON Validation")
    root.geometry("900x700")
    root.minsize(750, 550)

    # Styling
    style = ttk.Style()
    style.theme_use("clam")

    main_frame = ttk.Frame(root, padding="15")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Header
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill=tk.X, pady=(0, 10))

    title_label = ttk.Label(header_frame, text="Document Parser", font=("Segoe UI", 16, "bold"))
    title_label.pack(side=tk.LEFT)

    subtitle = ttk.Label(header_frame, text="Gemini API + Strict Pydantic Validation", font=("Segoe UI", 9))
    subtitle.pack(side=tk.LEFT, padx=10, pady=4)

    # Document Type Selector
    type_frame = ttk.LabelFrame(main_frame, text=" Document Type ", padding="8")
    type_frame.pack(fill=tk.X, pady=(0, 10))

    doc_type_var = tk.StringVar(value="resume")
    rb_resume = ttk.Radiobutton(type_frame, text="Resume Analysis", value="resume", variable=doc_type_var)
    rb_resume.pack(side=tk.LEFT, padx=15)

    rb_invoice = ttk.Radiobutton(type_frame, text="Invoice Analysis", value="invoice", variable=doc_type_var)
    rb_invoice.pack(side=tk.LEFT, padx=15)

    # Input Section
    input_frame = ttk.LabelFrame(main_frame, text=" Unstructured Input Text ", padding="8")
    input_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    btn_toolbar = ttk.Frame(input_frame)
    btn_toolbar.pack(fill=tk.X, pady=(0, 5))

    def browse_file_into_ui():
        path = filedialog.askopenfilename(
            title="Select Text Document",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            input_text_box.delete("1.0", tk.END)
            input_text_box.insert(tk.END, content)
            status_var.set(f"Loaded from {os.path.basename(path)}")

    def clear_all():
        input_text_box.delete("1.0", tk.END)
        output_text_box.delete("1.0", tk.END)
        status_var.set("Cleared.")

    ttk.Button(btn_toolbar, text="Browse File...", command=browse_file_into_ui).pack(side=tk.LEFT, padx=(0, 5))
    ttk.Button(btn_toolbar, text="Clear", command=clear_all).pack(side=tk.LEFT, padx=5)

    input_text_box = ScrolledText(input_frame, height=8, font=("Consolas", 10), wrap=tk.WORD)
    input_text_box.pack(fill=tk.BOTH, expand=True)

    # Action Button
    action_frame = ttk.Frame(main_frame)
    action_frame.pack(fill=tk.X, pady=(0, 10))

    status_var = tk.StringVar(value="Ready. Select document type and input text.")

    def run_extraction_thread():
        raw_text = input_text_box.get("1.0", tk.END).strip()
        if not raw_text:
            messagebox.showwarning("Empty Input", "Please provide unstructured text or load a sample.")
            return

        api_key = load_api_key()
        if not api_key:
            messagebox.showerror("Missing API Key", "GEMINI_API_KEY is not set in .env file.")
            return

        doc_type = doc_type_var.get()
        schema_cls = schemas.Resume if doc_type == "resume" else schemas.Invoice

        btn_parse.config(state=tk.DISABLED)
        status_var.set(f"Extracting {doc_type} with Gemini API...")
        output_text_box.delete("1.0", tk.END)

        def worker():
            try:
                prompt = prompts.build_prompt(doc_type, raw_text)
                raw_response = call_gemini(api_key, prompt, schema_cls)
                validated = validate_json_response(raw_response, schema_cls)
                formatted_json = validated.model_dump_json(indent=2)

                def update_success():
                    output_text_box.insert(tk.END, formatted_json)
                    status_var.set("Validation successful!")
                    btn_parse.config(state=tk.NORMAL)

                root.after(0, update_success)

            except ValidationError as v_err:
                def update_val_err():
                    err_msg = "Output failed Pydantic schema validation:\n\n"
                    for e in v_err.errors():
                        loc = " -> ".join(str(i) for i in e.get("loc", []))
                        err_msg += f"- Field: {loc}\n  Error: {e.get('msg')}\n\n"
                    output_text_box.insert(tk.END, err_msg)
                    status_var.set("Pydantic validation failed.")
                    btn_parse.config(state=tk.NORMAL)

                root.after(0, update_val_err)

            except Exception as err:
                def update_fail():
                    messagebox.showerror("Error", f"Extraction failed: {err}")
                    status_var.set(f"Error: {err}")
                    btn_parse.config(state=tk.NORMAL)

                root.after(0, update_fail)

        threading.Thread(target=worker, daemon=True).start()

    btn_parse = ttk.Button(action_frame, text="Extract & Validate JSON", command=run_extraction_thread)
    btn_parse.pack(side=tk.LEFT, padx=(0, 10))

    # Output Section
    output_frame = ttk.LabelFrame(main_frame, text=" Validated JSON Output ", padding="8")
    output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

    output_text_box = ScrolledText(output_frame, height=10, font=("Consolas", 10), wrap=tk.WORD)
    output_text_box.pack(fill=tk.BOTH, expand=True)

    out_toolbar = ttk.Frame(output_frame)
    out_toolbar.pack(fill=tk.X, pady=(5, 0))

    def copy_output():
        content = output_text_box.get("1.0", tk.END).strip()
        if content:
            root.clipboard_clear()
            root.clipboard_append(content)
            status_var.set("Copied JSON to clipboard.")

    ttk.Button(out_toolbar, text="Copy to Clipboard", command=copy_output).pack(side=tk.LEFT)

    # Status Bar
    status_bar = ttk.Label(main_frame, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W, padding="4")
    status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Document Parser with Strict JSON Validation")
    parser.add_argument("--cli", action="store_true", help="Run in interactive command-line mode")
    parser.add_argument("--type", choices=["resume", "invoice"], help="Document type ('resume' or 'invoice')")
    parser.add_argument("--file", type=str, help="Path to input text file")
    parser.add_argument("--text", type=str, help="Raw document text")
    args = parser.parse_args()

    # If any CLI arguments are provided, run CLI mode. Otherwise, launch the GUI.
    if args.cli or args.type or args.file or args.text:
        run_cli(args)
    else:
        launch_gui()


if __name__ == "__main__":
    main()
