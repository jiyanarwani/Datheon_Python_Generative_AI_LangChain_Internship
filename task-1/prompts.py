PROMPT_TEMPLATE = """You are a document extraction engine. Extract structured {document_type} data from the unstructured text below into strict JSON matching the schema.

TARGET FIELDS:
{target_fields}

EXTRACTION RULES:
1. Extract data only if it is explicitly present in the document. Do not invent or assume information.
2. For missing scalar fields (text, number, date), return null.
3. For missing list fields, return an empty list [].
4. Parse amounts and quantities as numbers (float/int), removing any currency symbols ($/€/£).
5. Output valid JSON only.

FEW-SHOT EXAMPLES:
{few_shot_examples}

UNSTRUCTURED TEXT:
\"\"\"
{document_text}
\"\"\"

JSON:"""


RESUME_FEW_SHOT = """--- Example ---
Input:
Alex Morgan
alex.morgan@innovatetech.io | +1 (555) 234-5678 | San Francisco, CA
Senior Backend Engineer with 6.0 years of experience in distributed systems.

Skills:
Python, Go, PostgreSQL, Redis, Docker, Kubernetes, AWS

Experience:
Senior Backend Engineer | Novacore Labs | Jan 2021 - Present
- Designed microservices handling 15M requests/day.
- Reduced database query latency by 45% with Redis.

Software Engineer | CloudScale Inc. | Jun 2018 - Dec 2020
- Built RESTful APIs using Python and Flask.

Education:
- B.S. in Computer Science, UC Berkeley (2014 - 2018)

Output:
{
  "full_name": "Alex Morgan",
  "email": "alex.morgan@innovatetech.io",
  "phone": "+1 (555) 234-5678",
  "skills": ["Python", "Go", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS"],
  "education": [
    {
      "institution": "UC Berkeley",
      "degree": "B.S. in Computer Science",
      "graduation_year": "2018"
    }
  ],
  "work_experience": [
    {
      "company": "Novacore Labs",
      "role": "Senior Backend Engineer",
      "duration": "Jan 2021 - Present",
      "responsibilities": [
        "Designed microservices handling 15M requests/day.",
        "Reduced database query latency by 45% with Redis."
      ]
    },
    {
      "company": "CloudScale Inc.",
      "role": "Software Engineer",
      "duration": "Jun 2018 - Dec 2020",
      "responsibilities": [
        "Built RESTful APIs using Python and Flask."
      ]
    }
  ],
  "years_of_experience": 6.0
}"""


INVOICE_FEW_SHOT = """--- Example ---
Input:
INVOICE
Apex Digital Solutions
1200 Market Street, Austin, TX 78701
Invoice Number: INV-2024-1108
Date: 2024-10-15
Currency: USD

Bill To: Horizon Media Group

Items:
1. Cloud Server Architecture Consulting (Qty: 20 hours @ $125.00/hr) - $2,500.00
2. Enterprise Security Audit (Qty: 1 @ $1,200.00) - $1,200.00

Total: $3,700.00

Output:
{
  "invoice_number": "INV-2024-1108",
  "vendor_name": "Apex Digital Solutions",
  "invoice_date": "2024-10-15",
  "currency": "USD",
  "items": [
    {
      "description": "Cloud Server Architecture Consulting",
      "quantity": 20.0,
      "unit_price": 125.0,
      "total_amount": 2500.0
    },
    {
      "description": "Enterprise Security Audit",
      "quantity": 1.0,
      "unit_price": 1200.0,
      "total_amount": 1200.0
    }
  ],
  "quantity": 21.0,
  "unit_price": null,
  "total_amount": 3700.0
}"""


DOCUMENT_CONFIGS = {
    "resume": {
        "document_type": "Resume",
        "target_fields": """- full_name (string or null)
- email (string or null)
- phone (string or null)
- skills (list of strings)
- education (list of objects with institution, degree, graduation_year)
- work_experience (list of objects with company, role, duration, responsibilities)
- years_of_experience (float or null)""",
        "few_shot_examples": RESUME_FEW_SHOT,
    },
    "invoice": {
        "document_type": "Invoice",
        "target_fields": """- invoice_number (string or null)
- vendor_name (string or null)
- invoice_date (string or null)
- currency (string or null)
- items (list of objects with description, quantity, unit_price, total_amount)
- quantity (float or null)
- unit_price (float or null)
- total_amount (float or null)""",
        "few_shot_examples": INVOICE_FEW_SHOT,
    },
}


def build_prompt(document_type: str, document_text: str) -> str:
    key = document_type.strip().lower()
    if key not in DOCUMENT_CONFIGS:
        raise ValueError(f"Unknown document type: '{document_type}'. Use 'resume' or 'invoice'.")

    cfg = DOCUMENT_CONFIGS[key]
    return PROMPT_TEMPLATE.format(
        document_type=cfg["document_type"],
        target_fields=cfg["target_fields"],
        few_shot_examples=cfg["few_shot_examples"],
        document_text=document_text.strip(),
    )
