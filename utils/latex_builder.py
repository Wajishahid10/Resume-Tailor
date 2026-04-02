"""
LaTeX builder — Jake's Resume template + pdflatex compilation.
"""

import subprocess
import tempfile
import os
import shutil


# ─── Character escaping ───────────────────────────────────────────────────────

_LATEX_SPECIAL = [
    ("\\", r"\textbackslash{}"),
    ("&",  r"\&"),
    ("%",  r"\%"),
    ("$",  r"\$"),
    ("#",  r"\#"),
    ("_",  r"\_"),
    ("{",  r"\{"),
    ("}",  r"\}"),
    ("~",  r"\textasciitilde{}"),
    ("^",  r"\textasciicircum{}"),
]

def esc(text: str) -> str:
    """Escape special LaTeX characters in a plain-text string."""
    if not text:
        return ""
    result = text
    for char, replacement in _LATEX_SPECIAL:
        result = result.replace(char, replacement)
    return result


def esc_url(url: str) -> str:
    """Minimal URL escaping — only replace % and #."""
    return url.replace("%", r"\%").replace("#", r"\#")


def _strip_prefix(url: str) -> str:
    """Remove https:// or http:// using startswith — NOT lstrip (which strips chars)."""
    url = url.strip()
    for prefix in ("https://", "http://"):
        if url.startswith(prefix):
            return url[len(prefix):]
    return url


# ─── Salesforce role detection ────────────────────────────────────────────────

_SALESFORCE_KEYWORDS = {
    "salesforce", "sfdc", "apex", "lwc", "lightning",
    "trailhead", "service cloud", "sales cloud", "cpq", "force.com",
}

def _is_salesforce_role(job_title: str) -> bool:
    t = job_title.lower()
    return any(kw in t for kw in _SALESFORCE_KEYWORDS)


# ─── Location resolver ────────────────────────────────────────────────────────

def _resolve_location(profile: dict, job_location: str) -> str:
    """
    Returns the right location string for the CV header:
      - 'Remote'           if job is remote
      - profile.relocation if job is in a different city/country
      - profile.location   otherwise / if job_location is blank
    """
    profile_loc = profile.get("location",   "")
    relocation  = profile.get("relocation", "")
    jl = (job_location or "").strip().lower()
    if not jl:
        return profile_loc
    if "remote" in jl:
        return profile.get("remote", "Remote")
    if jl not in profile_loc.lower():
        return relocation or profile_loc
    return profile_loc


# ─── Section builders ─────────────────────────────────────────────────────────

def _build_education(profile: dict) -> str:
    lines = []
    for edu in profile.get("education", []):
        inst   = esc(edu.get("institution", ""))
        loc    = esc(edu.get("location", profile.get("location", "")))
        degree = esc(edu.get("degree", ""))
        date   = esc(edu.get("date", ""))
        gpa    = edu.get("gpa", "")
        cw     = edu.get("coursework", [])

        lines.append(
            f"    \\resumeSubheading\n"
            f"      {{{inst}}}{{{loc}}}\n"
            f"      {{{degree}}}{{{date}}}"
        )
        extras = []
        if gpa:
            extras.append(f"\\textbf{{GPA}}: {esc(gpa)}")
        if cw:
            extras.append(
                "\\textbf{Relevant Coursework}: "
                + ", ".join(esc(c) for c in cw[:6])
            )
        if extras:
            lines.append("      \\resumeItemListStart")
            for ex in extras:
                lines.append(f"        \\resumeItem{{{ex}}}")
            lines.append("      \\resumeItemListEnd")
    return "\n".join(lines)


def _build_experience(experiences: list) -> str:
    lines = []
    for exp in experiences:
        role    = esc(exp.get("role", ""))
        date    = esc(exp.get("date", ""))
        company = esc(exp.get("company", ""))
        loc     = esc(exp.get("location", ""))
        bullets = exp.get("bullets", [])

        lines.append(
            f"    \\resumeSubheading\n"
            f"      {{{role}}}{{{date}}}\n"
            f"      {{{company}}}{{{loc}}}\n"
            f"      \\resumeItemListStart"
        )
        for b in bullets:
            lines.append(f"        \\resumeItem{{{esc(b)}}}")
        lines.append("      \\resumeItemListEnd")
    return "\n".join(lines)


def _build_projects(projects: list) -> str:
    """
    Renders projects with:
      - Row 1: Bold project name (+ optional repo link)  |  date
      - Row 2: Italic tech stack (full width, no overflow)
    This matches the 3-arg \\resumeProjectHeading{name}{tech}{date} command.
    IMPORTANT: must stay in sync with \\resumeProjectHeading in _make_preamble.
    """
    lines = []
    for proj in projects:
        name    = esc(proj.get("name", ""))
        # Tech list is pre-filtered by Gemini to JD-relevant items only
        tech    = ", ".join(esc(t) for t in proj.get("tech", []))
        date    = esc(proj.get("date", ""))
        link    = proj.get("link", "").strip()
        bullets = proj.get("bullets", [])
        if not bullets and proj.get("description"):
            bullets = [proj["description"]]

        # Build the name part — repo link appended if available
        name_part = f"\\textbf{{{name}}}"
        if link:
            safe_link  = esc_url(_strip_prefix(link))
            name_part += f" $|$ \\href{{https://{safe_link}}}{{\\underline{{repo}}}}"

        # 3 args: {name+link} {tech} {date}
        # Row 1: name+link | date   Row 2: tech (full width)
        lines.append(
            f"    \\resumeProjectHeading\n"
            f"      {{{name_part}}}{{{tech}}}{{{date}}}\n"
            f"      \\resumeItemListStart"
        )
        for b in bullets:
            lines.append(f"        \\resumeItem{{{esc(b)}}}")
        lines.append("      \\resumeItemListEnd")
    return "\n".join(lines)


def _build_certifications(certifications: list) -> str:
    if not certifications:
        return ""
    lines = ["  \\resumeSubHeadingListStart"]
    for cert in certifications:
        name = esc(cert.get("name",   ""))
        date = esc(cert.get("date",   ""))
        # issuer = esc(cert.get("issuer", ""))
        # Issuer omitted — Salesforce certs already contain "Salesforce" in the name
        lines.append(
            f"    \\item\\small{{\\textbf{{{name}}} \\hfill {date}}}"
        )
        # Alternative: full subheading with issuer (uncomment if needed)
        # lines.append(
        #     f"    \\resumeSubheading\n"
        #     f"      {{{name}}}{{{date}}}\n"
        #     f"      {{{issuer}}}{{}}"
        # )
    lines.append("  \\resumeSubHeadingListEnd")
    return "\n".join(lines)


# ─── Skills label maps ────────────────────────────────────────────────────────

# Salesforce-specific category labels
_SF_SKILL_LABELS = {
    "sf_clouds":            "Salesforce Clouds",
    "sf_ai_automation":     "AI \\& Automation",
    "sf_features":          "Salesforce Features",
    "sf_development":       "Development",
    "sf_apis_integrations": "APIs \\& Integrations",
    "sf_cicd_deployment":   "CI/CD \\& Deployment",
    "sf_data_security":     "Data \\& Security",
    "sf_developer_tools":   "Developer Tools",
    "sf_languages":         "Languages",
    "sf_methodologies":     "Methodologies",
}

# Generic fallback labels
_GENERIC_SKILL_LABELS = {
    "languages":  "Languages",
    "frameworks": "Frameworks",
    "tools":      "Developer Tools",
    "other":      "Other",
}


def _build_skills(skills: dict) -> str:
    # Detect which label map to use based on keys present
    is_sf     = any(k in skills for k in _SF_SKILL_LABELS)
    label_map = _SF_SKILL_LABELS if is_sf else _GENERIC_SKILL_LABELS
    lines = []
    for key, label in label_map.items():
        items = skills.get(key, [])
        if items:
            joined = ", ".join(esc(s) for s in items)
            lines.append(f"    \\resumeItem{{\\textbf{{{label}}}: {joined}}}")
    return "\n".join(lines)


# ─── Jake's preamble ──────────────────────────────────────────────────────────

def _make_preamble(pages: int = 2) -> str:
    """
    Return Jake's resume preamble tuned for 1 or 2 page output.
    NOTE: \\resumeProjectHeading takes 3 args — {name}{tech}{date}.
          _build_projects MUST pass all 3 args or LaTeX will error.
    """
    if pages == 1:
        font_size      = "10pt"
        side_margin    = "-0.6in"
        top_margin     = "-0.65in"
        text_width     = "1.2in"
        text_height    = "1.3in"
        section_vspace = "-6pt"
    else:
        font_size      = "11pt"
        side_margin    = "-0.5in"
        top_margin     = "-0.5in"
        text_width     = "1.0in"
        text_height    = "1.0in"
        section_vspace = "-4pt"

    return rf"""
\documentclass[letterpaper,{font_size}]{{article}}

\usepackage{{latexsym}}
\usepackage[empty]{{fullpage}}
\usepackage{{titlesec}}
\usepackage{{marvosym}}
\usepackage[usenames,dvipsnames]{{color}}
\usepackage{{verbatim}}
\usepackage{{enumitem}}
\usepackage[hidelinks]{{hyperref}}
\usepackage{{fancyhdr}}
\usepackage[english]{{babel}}
\usepackage{{tabularx}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\input{{glyphtounicode}}

\pagestyle{{fancy}}
\fancyhf{{}}
\fancyfoot{{}}
\renewcommand{{\headrulewidth}}{{0pt}}
\renewcommand{{\footrulewidth}}{{0pt}}

\addtolength{{\oddsidemargin}}{{{side_margin}}}
\addtolength{{\evensidemargin}}{{{side_margin}}}
\addtolength{{\textwidth}}{{{text_width}}}
\addtolength{{\topmargin}}{{{top_margin}}}
\addtolength{{\textheight}}{{{text_height}}}

\urlstyle{{same}}
\raggedbottom
\raggedright
\setlength{{\tabcolsep}}{{0in}}

\titleformat{{\section}}{{
  \vspace{{{section_vspace}}}\scshape\raggedright\large
}}{{}}{{0em}}{{}}[\color{{black}}\titlerule \vspace{{-5pt}}]

\pdfgentounicode=1

% ── Jake's custom commands ──────────────────────────────────────────────────
\newcommand{{\resumeItem}}[1]{{\item\small{{#1 \vspace{{-1pt}}}}}}

\newcommand{{\resumeSubheading}}[4]{{
  \vspace{{-2pt}}\item
    \begin{{tabular*}}{{0.97\textwidth}}[t]{{l@{{\extracolsep{{\fill}}}}r}}
      \textbf{{#1}} & #2 \\
      \textit{{\small#3}} & \textit{{\small #4}} \\
    \end{{tabular*}}\vspace{{-6pt}}
}}

% 3-arg command: #1=name+link, #2=tech (own row, no overflow), #3=date
\newcommand{{\resumeProjectHeading}}[3]{{
    \item
    \begin{{tabular*}}{{0.97\textwidth}}{{l@{{\extracolsep{{\fill}}}}r}}
      \small#1 & \small #3 \\
      \small\textit{{#2}} & \\
    \end{{tabular*}}\vspace{{-6pt}}
}}

\newcommand{{\resumeSubItem}}[1]{{\resumeItem{{#1}}\vspace{{-4pt}}}}
\renewcommand\labelitemii{{$\vcenter{{\hbox{{\tiny$\bullet$}}}}$}}
\newcommand{{\resumeSubHeadingListStart}}{{\begin{{itemize}}[leftmargin=0.15in, label={{}}]}}
\newcommand{{\resumeSubHeadingListEnd}}{{\end{{itemize}}}}
\newcommand{{\resumeItemListStart}}{{\begin{{itemize}}[leftmargin=0.2in, itemsep=1pt, parsep=0pt]}}
\newcommand{{\resumeItemListEnd}}{{\end{{itemize}}\vspace{{-4pt}}}}
"""

# Keep for backward compat — used nowhere but kept so old imports don't break
JAKE_PREAMBLE = _make_preamble(2)


# ─── Full document ────────────────────────────────────────────────────────────

def build_latex(
    profile:      dict,
    generated:    dict,
    job_title:    str,
    company_name: str,
    job_location: str = "",
    pages:        int = 2,
) -> str:
    """
    Assemble a complete Jake's-Resume LaTeX document.
    Uses AI-selected experience / projects / skills from `generated`,
    falling back to the raw profile values if a section is empty.
    """
    name      = esc(profile.get("name", "Your Name"))
    phone     = esc(profile.get("phone", ""))
    email     = profile.get("email", "")
    linkedin  = _strip_prefix(profile.get("linkedin",  "").strip())
    github    = _strip_prefix(profile.get("github",    "").strip())
    trailhead = _strip_prefix(profile.get("trailhead", "").strip())

    # Trailhead for Salesforce roles, GitHub otherwise
    profile_link       = trailhead if (_is_salesforce_role(job_title) and trailhead) else github
    profile_link_label = "Trailhead" if (_is_salesforce_role(job_title) and trailhead) else "GitHub"
    display_location   = esc(_resolve_location(profile, job_location))

    # Prefer AI-selected content; fall back to raw profile
    experiences    = generated.get("selected_experience") or profile.get("experience",     [])
    projects       = generated.get("selected_projects")   or profile.get("projects",       [])
    skills         = generated.get("selected_skills")     or profile.get("salesforce_skills") or profile.get("skills", {})
    summary        = generated.get("professional_summary", "")
    certifications = generated.get("certifications")      or profile.get("certifications", [])

    # Page-aware preamble (font size + margins)
    preamble  = _make_preamble(pages)
    edu_tex   = _build_education(profile)
    exp_tex   = _build_experience(experiences)
    proj_tex  = _build_projects(projects)
    sk_tex    = _build_skills(skills)
    cert_tex  = _build_certifications(certifications)

    summary_block = ""
    if summary:
        summary_block = (
            "\\section{Professional Summary}\n"
            f"\\small{{{esc(summary)}}}\n\n"
        )

    cert_block = ""
    if cert_tex:
        cert_block = (
            "%----------- CERTIFICATIONS -----------\n"
            "\\section{Certifications}\n"
            f"{cert_tex}\n\n"
        )

    doc = (
        "% ATS-Optimised Resume -- Jake's Template\n"
        f"% Role: {esc(job_title)} @ {esc(company_name)}\n"
        f"{preamble}\n"
        "\\begin{document}\n\n"
        "%---------- HEADING ----------\n"
        "\\begin{center}\n"
        f"    \\textbf{{\\Huge \\scshape {name}}} \\\\ \\vspace{{1pt}}\n"
        f"    \\small {phone} $|$\n"
        f"    \\href{{mailto:{email}}}{{\\underline{{{email}}}}} $|$\n"
        f"    \\href{{https://{esc_url(linkedin)}}}{{\\underline{{{esc(linkedin)}}}}}"
        + (f" $|$ \\href{{https://{esc_url(profile_link)}}}{{\\underline{{{profile_link_label}}}}}"
           if profile_link else "")
        + f" $|$ {display_location}\n"
        + "\\end{center}\n\n"
        + summary_block
        + "%----------- EDUCATION -----------\n"
        "\\section{Education}\n"
        "  \\resumeSubHeadingListStart\n"
        f"{edu_tex}\n"
        "  \\resumeSubHeadingListEnd\n\n"
        "%----------- EXPERIENCE -----------\n"
        "\\section{Experience}\n"
        "  \\resumeSubHeadingListStart\n"
        f"{exp_tex}\n"
        "  \\resumeSubHeadingListEnd\n\n"
        "%----------- PROJECTS -----------\n"
        "\\section{Projects}\n"
        "    \\resumeSubHeadingListStart\n"
        f"{proj_tex}\n"
        "    \\resumeSubHeadingListEnd\n\n"
        + cert_block
        + "%----------- TECHNICAL SKILLS -----------\n"
        "\\section{Technical Skills}\n"
        " \\begin{itemize}[leftmargin=0.15in, label={}]\n"
        "    \\small{\\item{\n"
        f"{sk_tex}\n"
        "    }}\n"
        " \\end{itemize}\n\n"
        "\\end{document}\n"
    )
    return doc


# ─── pdflatex check + compile ─────────────────────────────────────────────────

def _check_pdflatex():
    """Raise a clear error if pdflatex is not available in PATH."""
    if shutil.which("pdflatex") is None:
        raise EnvironmentError(
            "pdflatex not found in PATH.\n\n"
            "-- Windows --\n"
            "  1. Download MiKTeX: https://miktex.org/download\n"
            "     (set 'Install missing packages on-the-fly = Yes')\n"
            "  2. Restart your terminal after install.\n\n"
            "-- macOS --\n"
            "  brew install --cask mactex\n\n"
            "-- Linux / Streamlit Cloud --\n"
            "  Ensure packages.txt contains: texlive-latex-extra texlive-fonts-recommended"
        )


# ─── Compilation ──────────────────────────────────────────────────────────────

def compile_latex_to_pdf(latex_content: str, timeout: int = 90) -> bytes:
    """
    Write LaTeX to a temp dir, run pdflatex twice, return PDF bytes.
    Two passes needed for correct layout (references, lengths).
    Raises RuntimeError with compiler output on failure.
    """
    _check_pdflatex()   # fast-fail with a helpful message if not installed

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "resume.tex")
        pdf_path = os.path.join(tmpdir, "resume.pdf")
        log_path = os.path.join(tmpdir, "resume.log")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory", tmpdir,
            tex_path,
        ]

        last_result = None
        for _ in range(2):   # Two passes for correct layout
            last_result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
            )

        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                return f.read()

        # Compile failed — collect log for diagnosis
        log_content = ""
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                log_content = f.read()

        error_lines = [
            line for line in log_content.splitlines()
            if line.startswith("!") or "Error" in line or "error" in line
        ][:20]

        raise RuntimeError(
            "pdflatex compilation failed.\n\n"
            "-- Key errors --\n" + "\n".join(error_lines) + "\n\n"
            "-- stdout --\n" + (last_result.stdout if last_result else "") + "\n"
            "-- stderr --\n" + (last_result.stderr if last_result else "")
        )