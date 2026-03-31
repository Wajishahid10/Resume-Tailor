"""
LaTeX builder — Jake's Resume template + pdflatex compilation.
"""

import subprocess
import tempfile
import os
import re
from typing import Optional


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
    # Handle backslash first before other replacements
    result = text
    for char, replacement in _LATEX_SPECIAL:
        result = result.replace(char, replacement)
    return result


def esc_url(url: str) -> str:
    """Minimal URL escaping — only replace % and #."""
    return url.replace("%", r"\%").replace("#", r"\#")


# ─── Section builders ─────────────────────────────────────────────────────────

def _build_education(profile: dict) -> str:
    lines = []
    for edu in profile.get("education", []):
        inst      = esc(edu.get("institution", ""))
        loc       = esc(edu.get("location", profile.get("location", "")))
        degree    = esc(edu.get("degree", ""))
        date      = esc(edu.get("date", ""))
        gpa       = edu.get("gpa", "")
        cw        = edu.get("coursework", [])

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
    lines = []
    for proj in projects:
        name    = esc(proj.get("name", ""))
        tech    = ", ".join(esc(t) for t in proj.get("tech", []))
        date    = esc(proj.get("date", ""))
        link    = proj.get("link", "").strip()
        bullets = proj.get("bullets", [])
        if not bullets and proj.get("description"):
            bullets = [proj["description"]]

        heading = f"\\textbf{{{name}}} $|$ \\emph{{{tech}}}"
        if link:
            safe_link = esc_url(link)
            if not safe_link.startswith("http"):
                safe_link = "https://" + safe_link
            heading += f" $|$ \\href{{{safe_link}}}{{\\underline{{repo}}}}"

        lines.append(
            f"    \\resumeProjectHeading\n"
            f"      {{{heading}}}{{{date}}}\n"
            f"      \\resumeItemListStart"
        )
        for b in bullets:
            lines.append(f"        \\resumeItem{{{esc(b)}}}")
        lines.append("      \\resumeItemListEnd")

    return "\n".join(lines)


def _build_skills(skills: dict) -> str:
    mapping = {
        "languages":  "Languages",
        "frameworks": "Frameworks",
        "tools":      "Developer Tools",
        "other":      "Other",
    }
    lines = []
    for key, label in mapping.items():
        items = skills.get(key, [])
        if items:
            joined = ", ".join(esc(s) for s in items)
            lines.append(f"    \\resumeItem{{\\textbf{{{label}}}: {joined}}}")
    return "\n".join(lines)


# ─── Full document ────────────────────────────────────────────────────────────

JAKE_PREAMBLE = r"""
\documentclass[letterpaper,11pt]{article}

\usepackage{latexsym}
\usepackage[empty]{fullpage}
\usepackage{titlesec}
\usepackage{marvosym}
\usepackage[usenames,dvipsnames]{color}
\usepackage{verbatim}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{fancyhdr}
\usepackage[english]{babel}
\usepackage{tabularx}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\input{glyphtounicode}

\pagestyle{fancy}
\fancyhf{}
\fancyfoot{}
\renewcommand{\headrulewidth}{0pt}
\renewcommand{\footrulewidth}{0pt}

\addtolength{\oddsidemargin}{-0.5in}
\addtolength{\evensidemargin}{-0.5in}
\addtolength{\textwidth}{1in}
\addtolength{\topmargin}{-.5in}
\addtolength{\textheight}{1.0in}

\urlstyle{same}
\raggedbottom
\raggedright
\setlength{\tabcolsep}{0in}

\titleformat{\section}{
  \vspace{-4pt}\scshape\raggedright\large
}{}{0em}{}[\color{black}\titlerule \vspace{-5pt}]

\pdfgentounicode=1

% ── Jake's custom commands ──────────────────────────────────────────────────
\newcommand{\resumeItem}[1]{\item\small{#1 \vspace{-2pt}}}

\newcommand{\resumeSubheading}[4]{
  \vspace{-2pt}\item
    \begin{tabular*}{0.97\textwidth}[t]{l@{\extracolsep{\fill}}r}
      \textbf{#1} & #2 \\
      \textit{\small#3} & \textit{\small #4} \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeProjectHeading}[2]{
    \item
    \begin{tabular*}{0.97\textwidth}{l@{\extracolsep{\fill}}r}
      \small#1 & #2 \\
    \end{tabular*}\vspace{-7pt}
}

\newcommand{\resumeSubItem}[1]{\resumeItem{#1}\vspace{-4pt}}
\renewcommand\labelitemii{$\vcenter{\hbox{\tiny$\bullet$}}$}
\newcommand{\resumeSubHeadingListStart}{\begin{itemize}[leftmargin=0.15in, label={}]}
\newcommand{\resumeSubHeadingListEnd}{\end{itemize}}
\newcommand{\resumeItemListStart}{\begin{itemize}}
\newcommand{\resumeItemListEnd}{\end{itemize}\vspace{-5pt}}
"""


def build_latex(
    profile:      dict,
    generated:    dict,
    job_title:    str,
    company_name: str,
) -> str:
    """
    Assemble a complete Jake's-Resume LaTeX document.

    Uses AI-selected experience / projects / skills from `generated`,
    falling back to the raw profile values if a section is empty.
    """
    name     = esc(profile.get("name", "Your Name"))
    phone    = esc(profile.get("phone", ""))
    email    = profile.get("email", "")
    linkedin = profile.get("linkedin", "").strip().lstrip("https://").lstrip("http://")
    github   = profile.get("github",   "").strip().lstrip("https://").lstrip("http://")

    # Prefer generated content; fall back to raw profile
    experiences = generated.get("selected_experience") or profile.get("experience", [])
    projects    = generated.get("selected_projects")   or profile.get("projects",   [])
    skills      = generated.get("selected_skills")     or profile.get("skills",     {})
    summary     = generated.get("professional_summary", "")

    edu_tex  = _build_education(profile)
    exp_tex  = _build_experience(experiences)
    proj_tex = _build_projects(projects)
    sk_tex   = _build_skills(skills)

    # Optional summary section
    summary_block = ""
    if summary:
        summary_block = (
            "\\section{Professional Summary}\n"
            f"\\small{{{esc(summary)}}}\n\n"
        )

    doc = (
        "% ATS-Optimised Resume — Jake's Template\n"
        f"% Role: {esc(job_title)} @ {esc(company_name)}\n"
        f"{JAKE_PREAMBLE}\n"
        "\\begin{document}\n\n"
        "%---------- HEADING ----------\n"
        "\\begin{center}\n"
        f"    \\textbf{{\\Huge \\scshape {name}}} \\\\ \\vspace{{1pt}}\n"
        f"    \\small {phone} $|$\n"
        f"    \\href{{mailto:{email}}}{{\\underline{{{email}}}}} $|$\n"
        f"    \\href{{https://{esc_url(linkedin)}}}{{\\underline{{{esc(linkedin)}}}}}\n"
        + (f"    $|$ \\href{{https://{esc_url(github)}}}{{\\underline{{{esc(github)}}}}}\n"
           if github else "")
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
        "%----------- TECHNICAL SKILLS -----------\n"
        "\\section{Technical Skills}\n"
        " \\begin{itemize}[leftmargin=0.15in, label={}]\n"
        "    \\small{\\item{\n"
        f"{sk_tex}\n"
        "    }}\n"
        " \\end{itemize}\n\n"
        "\\end{document}\n"
    )
    return doc


# ─── Compilation ──────────────────────────────────────────────────────────────

def compile_latex_to_pdf(latex_content: str, timeout: int = 90) -> bytes:
    """
    Write LaTeX to a temp dir, run pdflatex twice, return PDF bytes.

    Raises RuntimeError with compiler output on failure.
    """
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
        for run in range(2):           # two passes for correct layout
            last_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
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
            "── Key errors ──\n" + "\n".join(error_lines) + "\n\n"
            "── stdout ──\n" + (last_result.stdout if last_result else "") + "\n"
            "── stderr ──\n" + (last_result.stderr if last_result else "")
        )
