"""
CV PDF parser.

Extracts raw text with pdfplumber, then sends to Gemini Flash
to structure it into the canonical profile schema.
Uses the new google-genai SDK (google.genai.Client).
"""

import json
import io
import pdfplumber
from google import genai
from google.genai import types


# ─── Text extraction ──────────────────────────────────────────────────────────

def extract_text_from_pdf(file_obj) -> str:
    """
    Extract all text from a PDF file object.
    Preserves page breaks with a separator so Gemini can reason
    about multi-page CVs.
    """
    pages = []
    with pdfplumber.open(file_obj) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if text:
                pages.append(f"[Page {i}]\n{text}")
    return "\n\n".join(pages)


# ─── Gemini structured extraction ─────────────────────────────────────────────

_SCHEMA = {
    "name":     "",
    "email":    "",
    "phone":    "",
    "linkedin": "",
    "github":   "",
    "location": "",
    "education": [
        {
            "institution": "",
            "degree":      "",
            "date":        "",
            "location":    "",
            "gpa":         "",
            "coursework":  [],
        }
    ],
    "experience": [
        {
            "company":  "",
            "role":     "",
            "date":     "",
            "location": "",
            "bullets":  [],
        }
    ],
    "projects": [
        {
            "name":        "",
            "description": "",
            "tech":        [],
            "link":        "",
            "date":        "",
        }
    ],
    "skills": {
        "languages":  [],
        "frameworks": [],
        "tools":      [],
        "other":      [],
    },
}

_SCHEMA_STR = json.dumps(_SCHEMA, indent=2)


def _clean_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$",          "", text)
    return text.strip()


def _gemini_extract(text: str, api_key: str) -> dict:
    client = genai.Client(api_key=api_key)

    prompt = f"""Extract ALL information from the CV text below and return it as JSON matching the schema exactly.

Rules:
- Preserve all dates exactly as written
- Copy bullet points verbatim
- Split skills: languages=programming languages, frameworks=libraries/frameworks, tools=DevOps/cloud/databases/IDEs, other=methodologies/soft skills
- Leave fields empty ("" or []) if not present

REQUIRED SCHEMA:
{_SCHEMA_STR}

CV TEXT:
{text}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=16384,
            response_mime_type="application/json",   # ← guarantees valid JSON
        ),
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini returned invalid JSON while parsing CV.\n"
            f"Error: {e}\nRaw (first 600 chars):\n{response.text[:600]}"
        )


# ─── Public API ───────────────────────────────────────────────────────────────

def parse_cv_pdf(uploaded_file, gemini_api_key: str) -> dict:
    """
    Parse an uploaded PDF CV into the canonical profile dict.

    Args:
        uploaded_file:   A Streamlit UploadedFile or any file-like object.
        gemini_api_key:  Gemini API key.

    Returns:
        Structured profile dict matching the _SCHEMA above.

    Raises:
        ValueError:  If Gemini returns bad JSON.
        RuntimeError: If the PDF has no extractable text.
    """
    raw_bytes = uploaded_file.read()
    file_obj  = io.BytesIO(raw_bytes)

    cv_text = extract_text_from_pdf(file_obj)

    if not cv_text.strip():
        raise RuntimeError(
            "Could not extract any text from this PDF. "
            "The file may be scanned/image-based — please use a text-based PDF."
        )

    profile = _gemini_extract(cv_text, gemini_api_key)

    # ── Post-processing: guarantee list types ──────────────────────────────
    for edu in profile.get("education", []):
        edu["coursework"] = list(edu.get("coursework") or [])

    for exp in profile.get("experience", []):
        exp["bullets"] = list(exp.get("bullets") or [])

    for proj in profile.get("projects", []):
        proj["tech"] = list(proj.get("tech") or [])

    skills = profile.get("skills", {})
    for cat in ["languages", "frameworks", "tools", "other"]:
        skills[cat] = list(skills.get(cat) or [])
    profile["skills"] = skills

    return profile