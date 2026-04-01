"""
Gemini 2.5 Flash — ATS CV content generation.
Uses response_mime_type="application/json" to guarantee valid JSON output.
"""

import json
from google import genai
from google.genai import types


def generate_cv_content(
    profile:          dict,
    job_description:  str,
    company_research: dict,
    company_name:     str,
    job_title:        str,
    gemini_api_key:   str,
) -> dict:
    client = genai.Client(api_key=gemini_api_key)

    profile_json  = json.dumps(profile,          indent=2)
    research_json = json.dumps(company_research, indent=2)

    prompt = f"""You are a senior technical recruiter and ATS optimisation expert.
Create a perfectly tailored, ATS-friendly resume for the candidate below.

════════════════════════════════
CANDIDATE PROFILE
════════════════════════════════
{profile_json}

════════════════════════════════
TARGET ROLE
════════════════════════════════
Job Title  : {job_title or "Not specified"}
Company    : {company_name or "Not specified"}

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
1. Extract every required/preferred skill, tool, technology, and soft skill from the JD.
2. Include a skill ONLY if it genuinely appears in the candidate profile AND is JD-relevant. Never invent skills.
3. Select 2–4 projects that best match JD requirements. Discard unrelated ones.
4. Rewrite every experience bullet: [Action verb] + [specific task] + [quantified impact]. Weave in JD keywords naturally.
5. Match tone/vocabulary to the company culture from research data.
6. Rate match score 0–100 realistically.
7. Write a 2-sentence summary opening with the target job title highlighting top 2 strengths.
8. Add Trailhead in the header instead of github for Salesforce Jobs.
9. According to company location and job location, add remote or open to reloation in the heading.
10. Keep it concise enough to fit on a single page.

RULES: Never invent metrics or skills. Enhance wording only — do not fabricate.

════════════════════════════════
REQUIRED JSON SCHEMA
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
      "name": "", "description": "", "tech": [],
      "link": "", "date": "", "bullets": []
    }}
  ],
  "selected_experience": [
    {{
      "company": "", "role": "", "date": "",
      "location": "", "bullets": []
    }}
  ],
  "professional_summary": "",
  "ats_keywords_used":    [],
  "match_score":          0,
  "optimization_notes":   ""
}}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=16384,
            response_mime_type="application/json",   # ← guarantees valid JSON
        ),
    )

    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini returned invalid JSON.\nError: {e}\n"
            f"Raw (first 500 chars):\n{response.text[:500]}"
        )