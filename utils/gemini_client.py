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

    profile_json  = json.dumps({
        k: v for k, v in profile.items()
        if k != "salesforce_skills"   # sent separately below
    }, indent=2)
    sf_skills_json  = json.dumps(profile.get("salesforce_skills", {}), indent=2)
    research_json   = json.dumps(company_research, indent=2)

    # Calculate total years of experience from profile
    prompt = f"""You are a senior technical recruiter and ATS optimisation expert with deep knowledge of
Applicant Tracking Systems (ATS), resume parsing, and keyword optimisation.

Your task: produce a perfectly tailored, ATS-friendly resume for the candidate below.

════════════════════════════════
CANDIDATE PROFILE
════════════════════════════════
{profile_json}

════════════════════════════════
CANDIDATE SALESFORCE SKILLS
(use for Salesforce roles only)
════════════════════════════════
{sf_skills_json}

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
STRICT INSTRUCTIONS
════════════════════════════════

── 1. ATS PARSEABILITY (Critical — target 90%+ parse rate) ──
- Use ONLY plain ASCII characters. No Unicode dashes (–), bullets (•), arrows, or special symbols.
- Use standard section names exactly: "Experience", "Education", "Projects", "Technical Skills".
- Do NOT use tables, columns, text boxes, or nested structures in bullet text.
- Keep bullet points as clean single sentences — no semicolons splitting two ideas into one bullet.
- Spell out all abbreviations on first use: e.g. "Lightning Web Components (LWC)".

── 2. PROFESSIONAL SUMMARY ──
- Open with the EXACT job title from the JD (not a variation).
- State total years of experience accurately by summing all roles in the profile.
- Mention the top 2-3 hard skills most prominent in the JD.
- Max 3 sentences. No fluff. No "passionate about" or "keen interest in".
- If the JD mentions preferred industries (e.g. Web3, blockchain), only include if
  there is genuine evidence in the profile — otherwise omit entirely.

── 3. EXPERIENCE BULLETS — STRICT RULES ──
VERB VARIETY: Never repeat the same opening verb across bullets within the same role.
Use a diverse mix from this list (pick the most accurate for each action):
  Architected, Engineered, Streamlined, Spearheaded, Accelerated, Automated,
  Reduced, Eliminated, Delivered, Launched, Refactored, Optimised, Consolidated,
  Migrated, Integrated, Established, Standardised, Mentored, Coordinated,
  Translated, Configured, Deployed, Authored, Overhauled, Benchmarked,
  Collaborated, Scoped, Triaged, Resolved, Enabled, Expanded, Drove

QUANTIFICATION: Every bullet MUST contain at least one of:
  - A percentage improvement (e.g. "reducing deployment time by 35%")
  - A count (e.g. "across 4 sandboxes", "serving 12 enterprise clients")
  - A time saving (e.g. "cutting manual effort from 3 hours to 20 minutes")
  - A scale indicator (e.g. "processing 500k+ records per batch job")
  If the profile bullet has no metric, infer a REALISTIC one based on context
  (e.g. code review → "reducing post-deployment defects by ~20%"). Never fabricate
  implausible numbers. Use "~" prefix for estimated figures.

MULTI-ORG / GLOBAL FRAMING: Where the profile mentions global teams, cross-org
  work, or multi-region projects, explicitly frame it as multi-org or cross-org
  Salesforce architecture experience — this matches common enterprise JD language.

JD-SPECIFIC TOOLS: If the JD mentions tools the candidate has NOT used but has
  a close equivalent in their profile, surface the equivalent prominently and note
  transferability. Example: JD mentions Workato → candidate has Zapier/REST API
  integrations → write bullet to highlight integration automation expertise.

── 4. SKILL SELECTION & CATEGORISATION ──
- Include a skill ONLY if present in the candidate profile AND relevant to the JD.
- Never invent skills.
- If the JD mentions specific tools the candidate hasn't used but has a close
  equivalent, surface the equivalent prominently in the relevant category.

CRITICAL — CATEGORY KEYS:
First, determine if this is a Salesforce-related role by checking if the job title
or description contains any of: salesforce, sfdc, apex, lwc, lightning, trailhead,
service cloud, sales cloud, cpq, force.com.

If YES (Salesforce role):
- Draw skills PRIMARILY from the SALESFORCE SKILLS section above.
- Supplement with relevant items from profile "skills" → languages and tools
  (e.g. Python, Git, Postman) where the JD warrants them.
- Return using ONLY these exact SF category keys:
    "sf_clouds"            → platform clouds (Sales Cloud, Service Cloud, etc.)
    "sf_ai_automation"     → AI and automation tools (Agentforce, Flow Builder, etc.)
    "sf_features"          → Salesforce config features (CPQ, Dynamic Forms, etc.)
    "sf_development"       → code and dev (Apex, LWC, SOQL, Triggers, etc.)
    "sf_apis_integrations" → APIs and integrations (REST, SOAP, OAuth 2.0, etc.)
    "sf_cicd_deployment"   → DevOps (SFDX, Unlocked Packages, Change Sets, etc.)
    "sf_data_security"     → data and security (Data Loader, Permission Sets, etc.)
    "sf_developer_tools"   → general dev tools (Git, Postman, VS Code, Jira, etc.)
    "sf_languages"         → programming languages (JavaScript, Python, Apex, etc.)
    "sf_methodologies"     → process (Agile, Scrum, SDLC, Code Review, etc.)

If NO (non-Salesforce role):
- Draw skills ONLY from the profile "skills" section.
- Return using ONLY these generic keys:
    "languages", "frameworks", "tools", "other"

NEVER mix SF keys and generic keys. NEVER invent skills absent from the profile.

── 5. PROJECT SELECTION ──
- Select 2-3 projects maximum that best match JD requirements.
- Rewrite project bullets using the same verb variety and quantification rules above.
- Drop any project with zero relevance to the JD.

── 6. GRAMMAR & SPELLING ──
- Proofread every sentence. Fix all spelling and grammar errors.
- Use consistent tense: past tense for all completed roles, present for current role.
- Do not start two consecutive bullets with the same word.
- Remove filler phrases: "in order to", "as well as", "a wide range of", "various".
- NEVER use third-person ("He", "She", "Muhammad") in the professional summary.
  Write in first-person implied style: "Senior Salesforce Developer with X years..."
- ABSOLUTELY NO MARKDOWN in any text field. No **bold**, no *italic*, no __underline__,
  no `backticks`. Plain text only in all bullets, summaries, and descriptions.
- Keep it concise enough to fit on a single page.

── 7. MATCH SCORE ──
- Score 0-100 based on: keyword overlap, experience level match, tool match,
  industry alignment. Be realistic — penalise hard for missing required years
  or mandatory certifications.

── 8. CERTIFICATIONS ──
- Extract any certifications mentioned in the profile and return them in the
  "certifications" array. Each entry: {{"name": "", "issuer": "", "date": ""}}.

════════════════════════════════
OUTPUT JSON SCHEMA
════════════════════════════════
{{
  "selected_skills": {{
    "sf_clouds":            [],
    "sf_ai_automation":     [],
    "sf_features":          [],
    "sf_development":       [],
    "sf_apis_integrations": [],
    "sf_cicd_deployment":   [],
    "sf_data_security":     [],
    "sf_developer_tools":   [],
    "sf_languages":         [],
    "sf_methodologies":     []
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
  "certifications": [
    {{
      "name":   "",
      "issuer": "",
      "date":   ""
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
        result = json.loads(response.text)
        return _strip_markdown(result)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini returned invalid JSON.\nError: {e}\n"
            f"Raw (first 500 chars):\n{response.text[:500]}"
        )


def _strip_markdown(obj):
    """Recursively strip markdown bold/italic markers from all string values."""
    if isinstance(obj, str):
        obj = obj.replace("**", "").replace("__", "").replace("*", "").replace("`", "")
        return obj
    elif isinstance(obj, list):
        return [_strip_markdown(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _strip_markdown(v) for k, v in obj.items()}
    return obj