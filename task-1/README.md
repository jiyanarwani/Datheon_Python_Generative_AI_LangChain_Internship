# AI-Based Document Parser with Strict JSON Validation

A Python desktop and CLI tool that uses the Google Gemini API to extract structured data from unstructured resumes and invoices, and validates the extracted output using Pydantic.

---

## Features

- **Desktop UI & CLI**: Built-in native desktop GUI (using standard `tkinter`) plus terminal CLI support.
- Extracts key details from unstructured text for both **Resumes** and **Invoices**.
- Enforces strict structured output via Gemini (`response_mime_type="application/json"` and `response_schema`).
- Validates data with **Pydantic**:
  - Rejects invalid emails and negative amounts/years.
  - Missing scalar values default to `null`.
  - Missing lists default to `[]`.
  - Never hallucinates or invents data.
- Parameterized prompt template with few-shot examples for each document type.
- Clean error handling with real-time status and validation error reporting.

---

## Project Structure

```text
├── main.py             # GUI application, CLI handling, Gemini API integration, and validation
├── prompts.py          # Prompt template, few-shot examples, and prompt builder
├── schemas.py          # Pydantic models (Resume, Invoice) and field validators
├── requirements.txt    # Project dependencies
└── README.md           # Setup and usage guide
```

---

## Schemas

### Resume
- `full_name`: string or `null`
- `email`: string (validated email format) or `null`
- `phone`: string or `null`
- `skills`: list of strings (defaults to `[]`)
- `education`: list of `{ institution, degree, graduation_year }` (defaults to `[]`)
- `work_experience`: list of `{ company, role, duration, responsibilities }` (defaults to `[]`)
- `years_of_experience`: non-negative float or `null`

### Invoice
- `invoice_number`: string or `null`
- `vendor_name`: string or `null`
- `invoice_date`: string or `null`
- `currency`: string or `null`
- `items`: list of `{ description, quantity, unit_price, total_amount }` (defaults to `[]`)
- `quantity`: non-negative float or `null`
- `unit_price`: non-negative float or `null`
- `total_amount`: non-negative float or `null`

---

## Output

The validated JSON is displayed directly in the GUI/terminal and can be copied to the clipboard.

Example Output (Invoice):
```json
{
  "invoice_number": "INV-2024-9421",
  "vendor_name": "VORTEX INNOVATIONS LLC",
  "invoice_date": "2024-11-12",
  "currency": "USD",
  "items": [
    {
      "description": "Enterprise Cloud Architecture Consulting",
      "quantity": 15.0,
      "unit_price": 160.0,
      "total_amount": 2400.0
    },
    {
      "description": "Custom API Integration & Security Audit",
      "quantity": 1.0,
      "unit_price": 1850.0,
      "total_amount": 1850.0
    },
    {
      "description": "High-Availability Cluster Server Setup",
      "quantity": 2.0,
      "unit_price": 450.0,
      "total_amount": 900.0
    }
  ],
  "quantity": 18.0,
  "unit_price": null,
  "total_amount": 5150.0
}
```
