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

    if pages == 1:
        page_instruction = """── 1. ONE-PAGE CONSTRAINT (Absolute — non-negotiable) ──
The entire resume MUST fit on a single page. Hard maximums:
- Professional summary: exactly 2 sentences, max 35 words total.
- Most recent role: exactly 4 bullets, max 18 words each.
- All other roles: exactly 3 bullets each, max 18 words each.
- Projects: exactly 2, exactly 2 bullets each, max 15 words each.
- Skills: only the most JD-relevant items per category.
- Education: GPA + max 4 coursework items."""
    else:
        page_instruction = """── 1. TWO-PAGE CONTENT GUIDELINES ──
The resume should fill 1.5 to 2 pages — enough white space to breathe, enough
content to be comprehensive. Use these guidelines:
- Professional summary: exactly 3 sentences, max 60 words total.
- Most recent role: 5 bullets, max 25 words each.
- Second most recent role: 4-5 bullets, max 25 words each.
- Older roles: 3-4 bullets each, max 25 words each.
- Projects: 2-3 projects, 2-3 bullets each, max 22 words each.
- Skills: include all JD-relevant items; be thorough but not exhaustive.
- Education: GPA + up to 6 coursework items.
Write with detail and specificity — include technologies, tools, methodologies,
and quantified outcomes wherever available in the original profile."""


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
{page_instruction}

── 2. ATS PARSEABILITY & KEYWORD EXTRACTION ──
- Use ONLY plain ASCII characters. No Unicode dashes, bullets, or symbols.
- Use standard section names: Experience, Education, Projects, Technical Skills.
- Clean single-sentence bullets only. No semicolons splitting two ideas.
- Do NOT expand abbreviations in parentheses for known Salesforce terms.

KEYWORD EXTRACTION — do this before writing anything else:
1. Read the JD and extract EVERY named tool, technology, methodology, and
   Salesforce feature mentioned — including in passing.
2. For each JD keyword, check if the candidate has it OR a direct equivalent.
3. Every matched keyword MUST appear somewhere in the CV — in bullets, skills,
   or summary. A keyword present in the profile but absent from the output CV
   is a missed ATS hit. Do not drop matched keywords between iterations.
4. For JD tools the candidate hasn't used, surface the closest equivalent:
   - JD: Workato/Ironclad  -> candidate: Zapier, REST API integrations
   - JD: Asana/Confluence  -> candidate: Jira, technical documentation
   - JD: DocuSign          -> candidate: Connected Apps, third-party integrations
5. JD admin keywords to always surface if present in profile:
   "workflow rules", "assignment rules", "page layouts", "fields",
   "validation rules", "user adoption", "user support", "training",
   "Optimizer", "Health Check", "multi-org", "global reporting",
   "data extraction", "data loading", "ETL", "Data Loader"

KEYWORD DENSITY RULE — CRITICAL:
ATS score = matched keywords / total words. More words without more matches
LOWERS your score. Apply this hard filter to skills:
- Include a skill ONLY if it appears in the JD or is a direct analogue.
- Every item added to sf_features or sf_ai_automation that is NOT in the JD
  dilutes keyword density. Remove: Tab, Global Actions, Field Set, Object
  Access, Program Management, Outcome Management, Field History, Compact
  Layout, App Builder, App Management, Lightning Record Pages unless the JD
  explicitly mentions them.
- Target: sf_features should have 10-15 items max, all JD-matched.

── 3. PROFESSIONAL SUMMARY ──
- Open with the EXACT job title from the JD.
- Calculate total years from earliest role start date to 2026. Jun 2022 = 4 years.
- ALWAYS include JD domain/industry keywords by mapping them to genuine candidate
  experience, even if those terms don't appear in the skills section:
    "enterprise software"      → candidate has AppExchange products
    "third-party integrations" → candidate has Twilio, Stripe, REST APIs
    "middleware"               → candidate has API integration and event-driven work
    "infrastructure"           → candidate has CI/CD, sandboxes, deployment pipelines
    "Web3 / blockchain"        → write action words such as started Web3 or newbie/learning blockchain
    "data quality"             → candidate has Data Loader, Health Check, OWD work
  Match the JD's language exactly where the candidate's experience supports it.
- No "passionate about", "keen interest in", or third-person ("He/She/name").
- For 1-page: exactly 2 sentences. For 2-page: exactly 3 sentences.

── 4. EXPERIENCE BULLETS ──
VERB VARIETY: Never repeat the same opening verb across bullets in the same role.
Use a diverse mix: Architected, Engineered, Streamlined, Spearheaded, Accelerated,
Automated, Reduced, Eliminated, Delivered, Launched, Refactored, Optimised,
Consolidated, Migrated, Integrated, Standardised, Mentored, Coordinated,
Translated, Configured, Deployed, Authored, Overhauled, Drove, Enabled.

QUANTIFICATION — CRITICAL RULES:
- ONLY use numbers that are EXPLICITLY stated in the original profile bullets.
- NEVER invent, estimate, or infer specific counts.
- Permitted metrics (from profile): "10x improvement", "50%", "40%", "30%",
  "100% sprint completion" — keep these exactly as written.
- Forbidden: any number not in the original profile.
- If a bullet has no metric, use scope qualifiers instead of numbers:
  e.g. "across the full SDLC", "for enterprise clients", "at org-wide scale".
- CURRENT ROLE PRIORITY: The most recent role must have the strongest, most
  specific bullets. Use precise technical language and scope indicators to
  compensate where metrics are absent. Never let the current role have weaker
  bullets than older roles.

OLDEST ROLE RULE: The Associate-level role bullets must show IMPACT and OUTCOMES.
Rewrite task-list bullets into achievement statements. Avoid "implemented X, Y,
and Z" constructions. Additionally — if the JD mentions "user support", "user
adoption", or "training", surface this from the profile's admin/CRM work:
frame cross-functional delivery, stakeholder engagement, and process automation
as supporting user adoption and operational efficiency.

MULTI-ORG FRAMING: Where the profile mentions global teams or multi-region work,
frame it as cross-org or multi-org Salesforce architecture experience.

── 5. SKILL SELECTION AND CATEGORISATION ──
CRITICAL — include a skill ONLY if directly relevant to THIS JD.
Apply these rules strictly:

KEYWORD RETENTION RULE: Any JD keyword matched to the candidate profile in
step 2 above MUST appear in the skills section under the correct category.
Never silently drop a matched keyword. If it fits two categories, pick the
most relevant one. Omit only if genuinely not in the profile at all.

For SALESFORCE roles use ONLY these SF keys:
    "sf_clouds"            -> only clouds explicitly mentioned or clearly implied by JD
    "sf_ai_automation"     -> only automation tools the JD references
    "sf_features"          -> only Salesforce features the JD requires or implies
    "sf_development"       -> Apex, LWC, SOQL etc. — only what the JD needs
    "sf_apis_integrations" -> only integration tools/protocols the JD mentions
    "sf_cicd_deployment"   -> only DevOps tools the JD references
    "sf_data_security"     -> only data/security items the JD mentions
    "sf_developer_tools"   -> Git, Postman, VS Code — only tools relevant to JD
    "sf_languages"         -> STRICT: Apex, SOQL, SOSL, JavaScript only for
                              Salesforce roles. NEVER add Java, C#, Kotlin,
                              Dart, C, C++, Rust unless JD explicitly asks.
    "sf_methodologies"     -> only methodologies the JD references. If JD
                              mentions "user adoption" or "training", add those.

For NON-SALESFORCE roles use: "languages", "frameworks", "tools", "other"
NEVER mix SF keys with generic keys.
Omit any category entirely if it has zero JD-relevant items.
HARD CAP: sf_features maximum 15 items. sf_apis_integrations maximum 15 items.
Remove any item not directly mentioned or implied by the JD.

── 6. PROJECT SELECTION ──
- Select exactly 2 projects that best match the JD. Drop the rest.
- Tech array: include ONLY JD-relevant items, maximum 6 tags per project.
  Fewer focused tags beat a long wrapped list — prioritise the most
  recognisable and JD-matching technologies.
- Max 2 bullets per project, max 20 words each. Show impact, not just tasks.

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
IMPORTANT: Preserve the full certification name exactly as written, including
any acronym in parentheses e.g. "Salesforce Certified Platform Developer I (PD1)".
Do NOT shorten or drop the acronym — ATS systems scan for "(PD1)" specifically.

── 9. MATCH SCORE ──
Score 0-100 based on:
- Keyword overlap: count how many JD keywords appear in the CV (highest weight)
- Experience level match: JD asks for X years, candidate has Y years
- Tool match: required tools present vs absent
- Industry alignment: domain keywords matched
- Admin vs dev balance: if JD is admin-heavy, penalise a dev-only CV

Be accurate — do not inflate. A score of 70+ requires 80%+ keyword coverage.

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