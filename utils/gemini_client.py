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
        page_instruction = """── 1. ONE-PAGE CONSTRAINT (Absolute) ──
- Professional summary: exactly 2 sentences, max 35 words total.
- Most recent role: exactly 4 bullets, max 18 words each.
- All other roles: exactly 3 bullets each, max 18 words each.
- Projects: 2-3, exactly 2 bullets each, max 15 words each.
- Skills: only the most JD-relevant items per category.
- Education: GPA + max 4 coursework items."""
    else:
        page_instruction = """── 1. TWO-PAGE CONTENT GUIDELINES ──
- Professional summary: exactly 3 sentences, max 60 words total.
- Most recent role: 5 bullets, max 25 words each.
- Second most recent role: 4-5 bullets, max 25 words each.
- Older roles: 3-4 bullets each, max 25 words each.
- Projects: 2-3 projects, 2-3 bullets each, max 22 words each.
- Skills: include all JD-relevant items; thorough but not exhaustive.
- Education: GPA + up to 6 coursework items."""

    prompt = f"""You are a senior technical recruiter and ATS optimisation expert.
Your task: produce a perfectly tailored, ATS-friendly resume.

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

── 2. ATS KEYWORD STRATEGY ──
Before writing anything, do this in order:

STEP A — Extract every keyword from the JD:
  Tools, technologies, Salesforce features, methodologies, and domain terms —
  including ones mentioned only once or in passing.

STEP B — Match each JD keyword to the candidate profile:
  Direct match: candidate explicitly has this skill/tool.
  Analogue match: candidate has an equivalent (examples below).
  No match: candidate has nothing comparable — do NOT invent it.

STEP C — Place every matched keyword somewhere in the CV:
  In a bullet, in skills, or in the summary. A matched keyword that appears
  nowhere in the output is a missed ATS hit. Do not drop matched keywords.

STEP D — Analogue mappings (surface these explicitly):
  JD: Workato, Ironclad       -> profile: Zapier, REST API integrations
  JD: Asana, Confluence       -> profile: Jira, technical documentation
  JD: DocuSign                -> profile: Connected Apps, third-party integrations
  JD: workflow rules          -> profile: Flow, Process Builder, automation
  JD: user adoption, training -> profile: stakeholder communication, cross-functional delivery
  JD: ETL, data loading       -> profile: Data Loader, Bulk API, data migration
  JD: multi-org, global reporting -> profile: global Agile teams, cross-org architecture

── 3. KEYWORD DENSITY RULE ──
ATS score = matched keywords / total words. Every word that is NOT a JD keyword
lowers your score. Apply this filter to the skills section:
- Include a skill ONLY if it appears in the JD or is a direct analogue (Step D).
- Do NOT include these unless the JD explicitly mentions them:
  Tab, Global Actions, Field Set, Object Access, Compact Layout, Layout,
  App Management, Program Management, Outcome Management, Field History,
  App Builder, Lightning Record Pages.
- No duplicate entries across categories. If Jira appears in Developer Tools,
  do not repeat it in Methodologies or APIs. Same for Workbench, Slack, Heroku.
- sf_features: maximum 15 items, all JD-matched.

── 4. PROFESSIONAL SUMMARY ──
- Open with the EXACT job title from the JD.
- Calculate total years from earliest role start date to 2026. Jun 2022 = 4 years.
- Mention Sales Cloud and/or Service Cloud by name if the JD requires them.
- Map JD domain terms to genuine candidate experience:
    "enterprise software"      -> AppExchange products, managed packages
    "third-party integrations" -> Twilio, Stripe, REST APIs, named credentials
    "middleware"               -> event-driven architecture, Platform Events, API layers
    "infrastructure"           -> CI/CD pipelines, SFDX, sandbox management
    "data quality"             -> Data Loader, Health Check, validation rules, OWD
    "Web3 / blockchain"        -> frame as transferable strength, not aspiration:
                                  "bringing enterprise integration and middleware depth
                                  to blockchain-adjacent platforms" or similar.
                                  NEVER use: "eager to", "passionate about",
                                  "keen interest", "committed to", "adept at leveraging",
                                  "actively exploring", "blockchain-aligned/enabled",
                                  or any third-person ("He/She/name").
- 1-page: exactly 2 sentences. 2-page: exactly 3 sentences.

── 5. EXPERIENCE BULLETS ──
VERB VARIETY: Never repeat the same opening verb within the same role.
Use a diverse mix: Architected, Engineered, Streamlined, Spearheaded,
Accelerated, Automated, Delivered, Refactored, Optimised, Consolidated,
Migrated, Integrated, Standardised, Coordinated, Translated, Configured,
Deployed, Authored, Overhauled, Drove, Enabled, Reduced, Eliminated.

QUANTIFICATION:
- ONLY use numbers explicitly stated in the original profile bullets.
- Permitted: 10x, 50%, 40%, 30%, 100% sprint completion — these are in profile.
- Forbidden: any number NOT in the original profile bullets.
- No metric available? Use scope qualifiers: "at org-wide scale", "across the
  full SDLC", "for enterprise clients", "spanning multiple orgs".

CURRENT ROLE: Most recent role must have the strongest, most specific bullets.
Use precise technical language to compensate where metrics are absent.

OLDEST ROLE: Must show impact and outcomes, not task lists. Rewrite
"implemented X, Y, Z" constructions into outcome-driven statements.
If the JD mentions user support / user adoption / training, frame the
candidate's stakeholder engagement and automation work in those terms.

MULTI-ORG: Frame global team / multi-region work as cross-org Salesforce
architecture experience wherever it appears.

── 6. SKILL CATEGORISATION ──
Determine if this is a Salesforce role by checking job title/description for:
salesforce, sfdc, apex, lwc, lightning, trailhead, service cloud, sales cloud,
cpq, force.com.

If YES (Salesforce role) — draw from SALESFORCE SKILLS section primarily,
supplement with relevant items from general profile skills (languages, tools).
Use ONLY these SF keys, omit any with zero JD-relevant items:
  "sf_clouds"            -> platform clouds mentioned or implied by JD
  "sf_ai_automation"     -> automation tools the JD references
  "sf_features"          -> Salesforce config features the JD requires (max 15)
  "sf_development"       -> Apex, LWC, SOQL — only what the JD needs
  "sf_apis_integrations" -> integration tools/protocols the JD mentions
  "sf_cicd_deployment"   -> DevOps tools the JD references
  "sf_data_security"     -> data/security items the JD mentions
  "sf_developer_tools"   -> Git, Postman, VS Code, Jira — only JD-relevant
  "sf_languages"         -> Apex, SOQL, SOSL, JavaScript ONLY for SF roles.
                            NEVER add Java, C#, Kotlin, Dart, C, C++, Rust
                            unless the JD explicitly requires them.
  "sf_methodologies"     -> process methodologies the JD references; include
                            "User Adoption" and "Training" if JD mentions them.

If NO (non-Salesforce role) — use: "languages", "frameworks", "tools", "other"
NEVER mix SF keys with generic keys.

── 7. PROJECT SELECTION ──
- Select 2-3 projects that best match JD requirements.
- Tech array: JD-relevant items only, maximum 6 tags per project.
  Fewer focused tags beat a long wrapped list.
- 2 bullets per project max, max 20 words each, show impact not just tasks.

── 8. GRAMMAR AND STYLE ──
- Plain ASCII only. No Unicode dashes (--), curly quotes, or special symbols.
- Fix all spelling and grammar errors.
- Past tense for completed roles, present tense for current role.
- No consecutive bullets starting with the same word.
- No filler: "in order to", "as well as", "a wide range of", "various".
- NO markdown: no **bold**, no *italic*, no backticks.
- NO tilde (~). Write plain numbers only.
- NO abbreviation expansions for known SF terms (SOQL, LWC, SDLC etc.).
- NO vague counts. Exact number from profile or qualitative scope — never invent.
- NEVER mention the company name anywhere. This is a CV not a cover letter.

── 9. CERTIFICATIONS ──
Return name and date only — omit issuer.
Preserve full name including acronym: "Salesforce Certified Platform Developer I (PD1)"
ATS systems scan for "(PD1)" specifically — never shorten or drop it.

── 10. MATCH SCORE ──
Score 0-100:
- Keyword overlap (highest weight): matched JD keywords / total CV words
- Experience level: JD requires X years, candidate has Y
- Tool match: required tools present vs absent
- Industry alignment: domain keywords matched
Score 70+ requires 80%+ keyword coverage. Be accurate, do not inflate.

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


def _normalize_unicode(text: str) -> str:
    """Replace Unicode characters that older LaTeX (pdflatex + inputenc) can't handle."""
    replacements = [
        ("\u2013", "--"),     # en-dash
        ("\u2014", "---"),    # em-dash
        ("\u2018", "'"),      # left single quote
        ("\u2019", "'"),      # right single quote / apostrophe
        ("\u201C", "``"),     # left double quote
        ("\u201D", "''"),     # right double quote
        ("\u2026", "..."),    # ellipsis
        ("\u2022", "-"),      # bullet
        ("\u00B7", "-"),      # middle dot
        ("\u00A0", " "),      # non-breaking space
        ("\r\n",   " "),      # Windows newline
        ("\n",     " "),      # Unix newline — prevents \par inside LaTeX groups
        ("\r",     " "),      # carriage return
    ]
    for src, dst in replacements:
        text = text.replace(src, dst)
    return text


def _strip_markdown(obj):
    """Recursively strip markdown, unwanted symbols, and unsafe Unicode."""
    if isinstance(obj, str):
        # Strip all markdown and unwanted symbols
        obj = obj.replace("**", "").replace("__", "").replace("*", "")
        obj = obj.replace("`", "").replace("~", "")
        obj = _normalize_unicode(obj)
        return obj
    elif isinstance(obj, list):
        return [_strip_markdown(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: _strip_markdown(v) for k, v in obj.items()}
    return obj