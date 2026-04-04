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
    pages:            int = 2,
) -> dict:
    client = genai.Client(api_key=gemini_api_key)

    profile_json   = json.dumps(
        {k: v for k, v in profile.items() if k != "salesforce_skills"},
        indent=2,
    )
    sf_skills_json = json.dumps(profile.get("salesforce_skills", {}), indent=2)
    research_json  = json.dumps(company_research, indent=2)

    page_instruction = (
        """── 1. ONE-PAGE CONSTRAINT ──
- Summary: 2 sentences, max 35 words.
- Current role: 4 bullets max, 18 words each.
- Other roles: 3 bullets each, 18 words each.
- Projects: 2-3, 2 bullets each, 15 words each.
- Skills: JD-relevant items only.
- Education: GPA + 4 coursework items."""
        if pages == 1 else
        """── 1. TWO-PAGE GUIDELINES ──
- Summary: exactly 3 sentences, max 60 words.
- Current role: 5 bullets, max 25 words each.
- 2nd most recent: 4-5 bullets, max 25 words each.
- Older roles: 3-4 bullets each, max 25 words each.
- Projects: 2-3, 2-3 bullets each, max 22 words each.
- Skills: all JD-relevant items, thorough but not exhaustive.
- Education: GPA + up to 6 coursework items."""
    )

    prompt = f"""You are a senior technical recruiter and ATS expert.
Produce a perfectly tailored, ATS-friendly resume.

════════ CANDIDATE PROFILE ════════
{profile_json}

════════ SALESFORCE SKILLS (SF roles only) ════════
{sf_skills_json}

════════ TARGET ROLE ════════
Title   : {job_title or "Not specified"}
Company : {company_name or "Not specified"}

════════ JOB DESCRIPTION ════════
{job_description}

════════ COMPANY RESEARCH ════════
{research_json}

════════ INSTRUCTIONS ════════

{page_instruction}

── 2. ATS KEYWORD STRATEGY ──
Before writing, do these steps in order:

STEP A — Extract every keyword from the JD:
  Tools, Salesforce features, technologies, methodologies, domain terms.

STEP B — Match each JD keyword to the profile:
  Direct: candidate explicitly has this. Analogues:
  - Workato/Ironclad   -> Zapier, REST API integrations
  - Asana/Confluence   -> Jira, technical documentation
  - DocuSign           -> Connected Apps, third-party integrations
  - workflow rules     -> Flow, Process Builder
  - user adoption      -> stakeholder communication, cross-functional delivery
  - ETL/data loading   -> Data Loader, Bulk API, data migration
  - multi-org/global reporting -> global Agile teams, cross-org architecture

STEP C — Every matched keyword MUST appear somewhere in the output.
  HIGH PRIORITY — never drop these if matched in profile:
  assignment rules, page layouts, fields, Optimizer, Web-to-Lead,
  Web-to-Case, Bulk API, Streaming API, Permission Set Groups,
  Experience Cloud.

KEYWORD DENSITY RULE: ATS score = matched keywords / total words.
Irrelevant words lower score. Only include skills directly relevant to JD.
Do NOT include unless JD mentions them: Tab, Global Actions, Field Set,
Object Access, Compact Layout, Layout, App Management, Program Management,
Outcome Management, Field History.
No duplicate entries across categories (e.g. Jira in one section only).

── 3. PROFESSIONAL SUMMARY ──
- Open with EXACT job title from JD.
- Years = earliest role start to 2026. Jun 2022 = 4 years.
- Always mention Sales Cloud/Service Cloud by name if JD requires them.
- If JD mentions Web3/blockchain, frame as transferable strength:
  "bringing enterprise API and middleware depth to blockchain infrastructure".
  NEVER use: "eager to", "passionate about", "keen interest", "committed to",
  "adept at leveraging", "actively exploring", or any third-person.
- Map JD domain terms to real candidate experience:
  "enterprise software"  -> AppExchange, managed packages
  "third-party integrations" -> Twilio, Stripe, REST APIs, Named Credentials
  "middleware"           -> Platform Events, API layers, event-driven arch
  "infrastructure"       -> CI/CD, SFDX, sandbox management
  "data quality"         -> Data Loader, Health Check, validation rules, OWD
- 1-page: 2 sentences. 2-page: 3 sentences.

── 4. EXPERIENCE ──
MANDATORY: ALL roles from the profile MUST appear in selected_experience.
NEVER drop any role — every role adds recency, tenure, and keywords.

VERB VARIETY: Never repeat an opening verb within the same role.
Use: Architected, Engineered, Streamlined, Spearheaded, Automated,
Delivered, Refactored, Optimised, Migrated, Integrated, Standardised,
Coordinated, Translated, Configured, Deployed, Authored, Drove, Enabled.

QUANTIFICATION:
- ONLY use numbers explicitly in the original profile bullets.
- NEVER drop an existing metric — "saving 40% development time" must stay.
- No metric? Use scope qualifiers: "at org-wide scale", "across the full SDLC".

CURRENT ROLE: Must have the strongest, most specific bullets.
OLDEST ROLE: Impact and outcomes, not task lists. Avoid "implemented X, Y, Z".
MULTI-ORG: Frame global/multi-region work as cross-org Salesforce architecture.

── 5. SKILLS ──
Salesforce role detection: check title/JD for salesforce, sfdc, apex, lwc,
lightning, trailhead, service cloud, sales cloud, cpq, force.com.

If YES → use only these SF keys (omit categories with zero JD-relevant items):
  sf_clouds            -> clouds in JD. ALWAYS include Experience Cloud
                          if in profile — relevant to most SF roles.
  sf_ai_automation     -> automation tools the JD references
  sf_features          -> SF config features the JD requires (max 15 items).
                          ONLY platform features (things in Setup).
                          NEVER put User Support/Adoption/Training here.
  sf_development       -> Apex, LWC, SOQL — only what JD needs
  sf_apis_integrations -> integration tools JD mentions. ALWAYS include
                          Bulk API and Streaming API if in profile.
  sf_cicd_deployment   -> DevOps tools JD references
  sf_data_security     -> data/security items JD mentions. ALWAYS include
                          Permission Set Groups if in profile.
  sf_developer_tools   -> Git, Postman, VS Code, Jira — JD-relevant only
  sf_languages         -> Apex, SOQL, SOSL, JavaScript ONLY. Never add
                          Java, C#, Kotlin, Dart, C, C++, Rust unless JD asks.
  sf_methodologies     -> methodologies JD references. User Support,
                          User Adoption, Training go HERE not in sf_features.

If NO → use: "languages", "frameworks", "tools", "other"
Never mix SF and generic keys.

── 6. PROJECTS ──
- 2-3 projects matching JD. NEVER fewer than 2.
- Tech array: JD-relevant only, max 5 items (layout constraint).
- 2 bullets max per project, max 20 words, show impact not tasks.
- Prefer projects that add keywords not already in experience bullets.

── 7. STYLE ──
- Plain ASCII only. No Unicode dashes, curly quotes, special symbols.
- Fix all spelling/grammar. Past tense completed, present for current role.
- No consecutive bullets starting same word.
- No filler: "in order to", "as well as", "a wide range of".
- NO markdown, NO tilde, NO abbreviation expansions for SF terms.
- NO fabricated numbers. NEVER mention the company name (not a cover letter).

── 8. CERTIFICATIONS ──
Name and date only — no issuer.
Preserve full name with acronym: "Salesforce Certified Platform Developer I (PD1)"
ATS systems specifically scan for "(PD1)" — never shorten it.

── 9. MATCH SCORE ──
Score 0-100: keyword overlap (highest weight), experience level, tool match,
industry alignment. 70+ requires 80%+ keyword coverage. Do not inflate.

════════ OUTPUT SCHEMA ════════
{{
  "selected_skills": {{
    "sf_clouds": [], "sf_ai_automation": [], "sf_features": [],
    "sf_development": [], "sf_apis_integrations": [], "sf_cicd_deployment": [],
    "sf_data_security": [], "sf_developer_tools": [], "sf_languages": [],
    "sf_methodologies": []
  }},
  "selected_projects": [
    {{"name": "", "description": "", "tech": [], "link": "", "date": "", "bullets": []}}
  ],
  "selected_experience": [
    {{"company": "", "role": "", "date": "", "location": "", "bullets": []}}
  ],
  "certifications": [{{"name": "", "date": ""}}],
  "professional_summary": "",
  "ats_keywords_used": [],
  "match_score": 0,
  "optimization_notes": ""
}}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=8192,          # Reduced from 16384 — CVs never need more
            response_mime_type="application/json",
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


def _normalize_unicode(text: str) -> str:
    """Replace Unicode chars that pdflatex cannot handle."""
    replacements = [
        ("\u2013", "--"),    # en-dash
        ("\u2014", "---"),   # em-dash
        ("\u2018", "'"),     # left single quote
        ("\u2019", "'"),     # right single quote
        ("\u201C", "``"),    # left double quote
        ("\u201D", "''"),    # right double quote
        ("\u2026", "..."),   # ellipsis
        ("\u2022", "-"),     # bullet
        ("\u00A0", " "),     # non-breaking space
        ("\r\n",   " "),
        ("\n",     " "),     # newlines → space (prevents \par inside LaTeX groups)
        ("\r",     " "),
    ]
    for src, dst in replacements:
        text = text.replace(src, dst)
    return text


def _strip_markdown(obj):
    """Recursively strip markdown, unwanted symbols, and unsafe Unicode."""
    if isinstance(obj, str):
        obj = obj.replace("**", "").replace("__", "").replace("*", "")
        obj = obj.replace("`", "").replace("~", "")
        obj = _normalize_unicode(obj)
        return obj
    elif isinstance(obj, list):
        return [_strip_markdown(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _strip_markdown(v) for k, v in obj.items()}
    return obj