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

    profile_json   = json.dumps(
        {k: v for k, v in profile.items() if k != "salesforce_skills"},
        indent=2,
    )
    sf_skills_json = json.dumps(profile.get("salesforce_skills", {}), indent=2)
    research_json  = json.dumps(company_research, indent=2)

    prompt = f"""You are a senior technical recruiter and ATS optimisation expert.
Your task: produce a perfectly tailored, ONE-PAGE, ATS-friendly resume.

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

── 1. ONE-PAGE CONSTRAINT (Absolute — non-negotiable) ──
The entire resume MUST fit on a single page. These are hard maximums:
- Professional summary: exactly 2 sentences, max 35 words total.
- Most recent role: exactly 4 bullets, max 18 words each.
- All other roles: exactly 3 bullets each, max 18 words each.
- Projects: exactly 2 projects, exactly 2 bullets each, max 15 words each.
- Skills: only the most JD-relevant items per category. No exhaustive lists.
- Education bullets: GPA + max 4 relavent coursework items only.
If content exceeds these limits, cut words — never exceed the counts.

── 2. ATS PARSEABILITY ──
- Use ONLY plain ASCII characters. No Unicode dashes, bullets, or symbols.
- Use standard section names: Experience, Education, Projects, Technical Skills.
- Clean single-sentence bullets only. No semicolons splitting two ideas.
- Do NOT expand abbreviations in parentheses. The audience knows Salesforce
  terms. Never write "SOQL (Salesforce Object Query Language)" or
  "LWC (Lightning Web Components)" or "SDLC (Software Development Life Cycle)".
  Write just "SOQL", "LWC", "SDLC".

── 3. PROFESSIONAL SUMMARY ──
- Open with the EXACT job title from the JD.
- Calculate total years of experience by finding the earliest start date across
  ALL roles in the profile and computing to present (2026).
  Example: earliest role Jun. 2022 to 2026 = 4 years. Never round down.
- Include 2-3 JD-specific industry/domain keywords where the candidate has
  GENUINE basis. Examples:
    - JD mentions "enterprise software" → candidate has AppExchange products = include it
    - JD mentions "third-party integrations" → candidate has Twilio/Stripe/etc. = include it
    - JD mentions "Web3 / blockchain" → write action words such as intrest in Web3 or newbie/learning blockchain
    - JD mentions "infrastructure / middleware" → include if candidate has API/integration work
  Do NOT fabricate domain experience. Map JD language to real candidate experience.
- Exactly 2 sentences. Max 40 words total.
- No third-person ("He/She/candidate name").

── 4. EXPERIENCE BULLETS ──
VERB VARIETY: Never repeat the same opening verb across bullets in the same role.
Use a diverse mix: Architected, Engineered, Streamlined, Spearheaded, Accelerated,
Automated, Reduced, Eliminated, Delivered, Launched, Refactored, Optimised,
Consolidated, Migrated, Integrated, Standardised, Mentored, Coordinated,
Translated, Configured, Deployed, Authored, Overhauled, Drove, Enabled.

QUANTIFICATION — CRITICAL RULES:
- ONLY use numbers that are EXPLICITLY stated in the original profile bullets.
- NEVER invent, estimate, or infer specific counts such as number of clients,
  users, projects, sprints, releases, features, or apps.
- If the original bullet has no metric, enhance the wording and impact but do
  NOT add a fabricated number. A strong verb + clear outcome is sufficient.
- Permitted: keeping existing metrics like "10x improvement", "50%", "40%",
  "30%", "100% sprint completion" — these are in the original profile.
- Forbidden: adding "5+ clients", "500 users", "3 successful launches",
  "12 consecutive sprints", "10 monthly releases" if not in original profile.

MULTI-ORG FRAMING: Where the profile mentions global teams or multi-region work,
frame it as cross-org or multi-org Salesforce architecture experience.

── 5. SKILL SELECTION AND CATEGORISATION ──
CRITICAL — CATEGORY KEYS:
Determine if this is a Salesforce role by checking if the job title or description
contains: salesforce, sfdc, apex, lwc, lightning, trailhead, service cloud,
sales cloud, cpq, force.com.

If YES (Salesforce role):
- Draw skills PRIMARILY from SALESFORCE SKILLS above.
- Supplement with relevant items from profile "skills" (languages, tools) where
  the JD warrants them.
- Return ONLY these exact SF keys (omit any category with zero relevant items):
    "sf_clouds"            -> Salesforce platform clouds
    "sf_ai_automation"     -> AI and automation tools
    "sf_features"          -> Salesforce config features
    "sf_development"       -> Apex, LWC, SOQL, Triggers, etc.
    "sf_apis_integrations" -> REST, SOAP, OAuth 2.0, third-party tools
    "sf_cicd_deployment"   -> SFDX, Unlocked Packages, Change Sets, etc.
    "sf_data_security"     -> Data Loader, Permission Sets, OWD, etc.
    "sf_developer_tools"   -> Git, Postman, VS Code, Jira, etc.
    "sf_languages"         -> Programming languages only
    "sf_methodologies"     -> Agile, Scrum, SDLC, etc.

If NO (non-Salesforce role):
- Use ONLY: "languages", "frameworks", "tools", "other"

NEVER mix SF keys with generic keys.

── 6. PROJECT SELECTION ──
- Select exactly 2 projects that best match the JD. Drop the rest.
- Keep only JD-relevant tech tags in the "tech" array — these appear as visible
  keywords in the CV header line. Do NOT include all tech from the profile;
  only include items that match or relate to the JD requirements.
- Max 2 bullets per project, max 20 words each.

── 7. GRAMMAR, SPELLING AND STYLE ──
- Fix all spelling and grammar errors.
- Past tense for completed roles, present tense for current role.
- No consecutive bullets starting with the same word.
- Remove filler: "in order to", "as well as", "a wide range of", "various".
- NO third-person ("He", "She", candidate name) anywhere.
- ABSOLUTELY NO MARKDOWN: no **bold**, no *italic*, no __underline__, no backticks.
- NO tilde (~) symbol. Write plain numbers only.
- NO abbreviation expansions in parentheses for known Salesforce terms.
- NO vague inflated counts. If you don't have the exact number from the profile,
  describe scope qualitatively instead.

── 8. CERTIFICATIONS ──
Extract certifications from the profile. Return name and date only — omit issuer.

── 9. MATCH SCORE ──
Score 0-100: keyword overlap, experience level, tool match, industry alignment.
Penalise for missing required years or mandatory certifications.

════════════════════════════════
OUTPUT JSON SCHEMA
════════════════════════════════
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
  "certifications": [
    {{"name": "", "date": ""}}
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
            temperature=0.3,
            max_output_tokens=16384,
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


def _strip_markdown(obj):
    """Recursively strip markdown and unwanted symbols from all string values."""
    if isinstance(obj, str):
        # Strip all markdown and unwanted symbols
        obj = obj.replace("**", "").replace("__", "").replace("*", "")
        obj = obj.replace("`", "").replace("~", "")
        return obj
    elif isinstance(obj, list):
        return [_strip_markdown(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _strip_markdown(v) for k, v in obj.items()}
    return obj