"""
Gemini 2.5 Flash — ATS CV content generation.
Uses the new google-genai SDK (google.genai.Client).
"""

import json
import re
from google import genai
from google.genai import types


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _clean_json(text: str) -> str:
    """Strip markdown fences that Gemini sometimes wraps around JSON."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$",          "", text)
    return text.strip()


def _parse_json(text: str) -> dict:
    clean = _clean_json(text)
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        # ── Recovery 1: find the last complete top-level object ────────────
        try:
            depth, last_close = 0, 0
            for i, ch in enumerate(clean):
                if ch == "{": depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        last_close = i + 1
            if last_close:
                return json.loads(clean[:last_close])
        except Exception:
            pass

        # ── Recovery 2: auto-close truncated JSON ──────────────────────────
        try:
            fixed = _autoclose_json(clean)
            return json.loads(fixed)
        except Exception:
            pass

        raise ValueError(
            f"Gemini returned unparseable JSON.\nOriginal error: {e}\n"
            f"Raw response (first 500 chars):\n{text[:500]}"
        )


def _autoclose_json(s: str) -> str:
    """Close any unclosed brackets/braces/strings in truncated JSON."""
    in_str, escape = False, False
    opens = []
    result = list(s)

    for ch in s:
        if escape:
            escape = False
            continue
        if ch == "\\" and in_str:
            escape = True
            continue
        if ch == '"':
            in_str = not in_str
            continue
        if not in_str:
            if ch in "{[": opens.append(ch)
            elif ch in "}]": opens.pop() if opens else None

    # If we ended mid-string, close it
    if in_str:
        result.append('"')

    # Close any open arrays / objects in reverse order
    closers = {"{": "}", "[": "]"}
    for opener in reversed(opens):
        result.append(closers[opener])

    return "".join(result)


# ─── Main function ────────────────────────────────────────────────────────────

def generate_cv_content(
    profile:          dict,
    job_description:  str,
    company_research: dict,
    company_name:     str,
    job_title:        str,
    gemini_api_key:   str,
) -> dict:
    """
    Calls Gemini 2.5 Flash to:
      1. Extract ATS keywords from the JD
      2. Select ONLY relevant skills / projects / experience from the profile
      3. Rewrite bullet points (action verb + metric + impact)
      4. Tailor tone to the company's culture (from research)
      5. Return structured JSON
    """
    client = genai.Client(api_key=gemini_api_key)

    profile_json  = json.dumps(profile,          indent=2)
    research_json = json.dumps(company_research, indent=2)

    prompt = f"""You are a senior technical recruiter and ATS optimisation expert.

Your job is to create a perfectly tailored, ATS-friendly resume for the candidate below.

════════════════════════════════
CANDIDATE PROFILE
════════════════════════════════
{profile_json}

════════════════════════════════
TARGET ROLE
════════════════════════════════
Job Title  : {job_title}
Company    : {company_name}

════════════════════════════════
JOB DESCRIPTION
════════════════════════════════
{job_description}

════════════════════════════════
COMPANY RESEARCH
════════════════════════════════
{research_json}

════════════════════════════════
INSTRUCTIONS
════════════════════════════════
1. **Keyword extraction** — identify every required and preferred skill, tool,
   technology, and soft skill mentioned in the JD.

2. **Skill selection** — include a skill ONLY if it genuinely appears in the
   candidate's profile AND is relevant to the JD. Never invent skills.

3. **Project selection** — pick 2–4 projects that best demonstrate the JD
   requirements. Discard unrelated projects entirely.

4. **Experience rewriting** — rewrite every bullet point using the formula:
   [Strong action verb] + [specific task] + [quantified outcome/impact].
   Naturally weave in JD keywords. Keep each bullet ≤ 2 lines.

5. **Company tone matching** — use vocabulary and priorities that match the
   company's culture (from the research data above).

6. **Match score** — rate how well the profile fits this specific JD (0–100).

7. **Professional summary** — write a 2-sentence ATS-friendly summary that
   opens with the target job title and highlights the top 2 strengths.

RULES:
- NEVER invent experience, metrics, or skills not in the profile.
- Keep bullets truthful — enhance wording and emphasis, do not fabricate.
- Match score must be realistic: low if profile is a poor fit.

════════════════════════════════
OUTPUT FORMAT  (return ONLY valid JSON, no markdown, no commentary)
════════════════════════════════
{{
  "selected_skills": {{
    "languages":  [],
    "frameworks": [],
    "tools":      [],
    "other":      []
  }},
  "selected_projects": [
    {{
      "name":        "",
      "description": "",
      "tech":        [],
      "link":        "",
      "date":        "",
      "bullets":     []
    }}
  ],
  "selected_experience": [
    {{
      "company":  "",
      "role":     "",
      "date":     "",
      "location": "",
      "bullets":  []
    }}
  ],
  "professional_summary":  "",
  "ats_keywords_used":     [],
  "match_score":           0,
  "optimization_notes":    ""
}}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=4096,
        ),
    )
    return _parse_json(response.text)