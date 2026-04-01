"""
ATS-Optimized CV Builder
─────────────────────────
Powered by Google Gemini · Jake's Resume Template · LaTeX PDF
Single-user · Streamlit Community Cloud
"""

import streamlit as st
import json
from datetime import datetime

from utils.cv_parser import parse_cv_pdf
from utils.researcher import research_company
from utils.gemini_client import generate_cv_content
from utils.latex_builder import build_latex, compile_latex_to_pdf

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ATS CV Builder",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f0f2f6;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 4px 0;
    }
    .keyword-badge {
        display: inline-block;
        background: #e8f4fd;
        color: #1f77b4;
        border-radius: 4px;
        padding: 2px 8px;
        margin: 2px;
        font-size: 0.85em;
        font-family: monospace;
    }
    .score-high { color: #28a745; font-weight: bold; }
    .score-mid  { color: #ffc107; font-weight: bold; }
    .score-low  { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _to_plain(obj):
    """Recursively convert Streamlit AttrDict / TOML objects to plain Python."""
    if isinstance(obj, dict) or hasattr(obj, "items"):
        return {k: _to_plain(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)) or hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [_to_plain(i) for i in obj]
    return obj


def load_profile_from_secrets() -> dict:
    """Load and normalise the [profile] block from secrets.toml."""
    try:
        raw = st.secrets["profile"]
        profile = _to_plain(raw)

        # Ensure lists for skills sub-keys
        for cat in ["languages", "frameworks", "tools", "other"]:
            skills = profile.get("skills", {})
            if cat in skills:
                skills[cat] = list(skills[cat])

        # Ensure bullets lists on experience / projects
        for exp in profile.get("experience", []):
            exp["bullets"] = list(exp.get("bullets", []))
        for proj in profile.get("projects", []):
            proj["tech"] = list(proj.get("tech", []))

        return profile
    except KeyError:
        return {}
    except Exception as e:
        st.sidebar.error(f"Secrets parse error: {e}")
        return {}


def get_gemini_key():
    gemini  = st.secrets.get("api_keys", {}).get("gemini",  "")
    return gemini


def score_color(score: int) -> str:
    if score >= 75: return "score-high"
    if score >= 50: return "score-mid"
    return "score-low"


# ─── Session state init ───────────────────────────────────────────────────────

defaults = {
    "profile":          None,
    "generated":        None,
    "latex_source":     None,
    "pdf_bytes":        None,
    "company_research": None,
    "research_done": False,
    "last_job_title":   "",
    "last_company":     "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

if st.session_state.profile is None:
    st.session_state.profile = load_profile_from_secrets()


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("👤 Profile")

    profile = st.session_state.profile

    if profile:
        st.success(f"**{profile.get('name', 'Loaded')}**")
        st.caption(f"{profile.get('email','')} · {profile.get('location','')}")

        with st.expander("🛠 Skills"):
            for cat, items in profile.get("skills", {}).items():
                if items:
                    st.markdown(f"**{cat.title()}**: {', '.join(items)}")

        with st.expander(f"🚀 Projects ({len(profile.get('projects', []))})"):
            for p in profile.get("projects", []):
                st.markdown(f"- **{p['name']}** — `{', '.join(p.get('tech',[]))}`")

        with st.expander(f"💼 Experience ({len(profile.get('experience', []))})"):
            for e in profile.get("experience", []):
                st.markdown(f"- **{e['role']}** @ {e['company']}")
    else:
        st.warning("No profile found in secrets.toml")

    st.divider()
    st.subheader("📤 Override Profile")
    st.caption("Upload a CV to replace your profile **for this session only**.")

    uploaded = st.file_uploader("Upload CV (PDF)", type=["pdf"], label_visibility="collapsed")
    if uploaded:
        gemini_key = get_gemini_key()
        if not gemini_key:
            st.error("Set `api_keys.gemini` in secrets first.")
        else:
            with st.spinner("Parsing CV with Gemini…"):
                try:
                    parsed = parse_cv_pdf(uploaded, gemini_key)
                    st.session_state.profile = parsed
                    st.success("Profile updated for this session!")

                    with st.expander("📋 Extracted JSON — copy to secrets.toml"):
                        st.json(parsed)

                    st.rerun()
                except Exception as err:
                    st.error(f"Parsing failed: {err}")

    st.divider()
    st.caption("🔑 **Keys stored in** `.streamlit/secrets.toml`")
    gemini_ok = get_gemini_key()
    st.markdown(f"{'✅' if gemini_ok else '❌'} Gemini API")
    st.markdown("✅ Company Research (DuckDuckGo)")


# ─── Main ─────────────────────────────────────────────────────────────────────

st.title("🎯 ATS-Optimized CV Builder")
st.caption("Google Gemini · Jake's Resume (LaTeX) · Single-user")

tab1, tab2, tab3 = st.tabs(["📝 Job Details", "⚙️ CV Preview", "📥 Download"])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Job Details
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    col_l, col_r = st.columns(2, gap="large")

    with col_l:
        st.subheader("🏢 Job Info")
        job_title    = st.text_input("Job Title", placeholder="e.g. Senior Software Engineer",
                            value=st.session_state.last_job_title or "Senior Salesforce Developer")
        company_name = st.text_input("Company Name (optional)", placeholder="e.g. Google",
                            value=st.session_state.last_company)

    with col_r:
        st.subheader("📋 Job Description")
        job_description = st.text_area(
            "Paste the full JD here *",
            height=220,
            placeholder="Copy and paste the complete job description…",
        )

    st.divider()

    # ── Company Research ──────────────────────────────────────────────────────
    rc1, rc2 = st.columns([3, 1])
    with rc1:
        st.subheader("🔍 Company Research")
    with rc2:
        research_btn = st.button(
            "🔍 Research",
            use_container_width=True,
            disabled=not company_name,
            help="Enter a company name above to enable research",
        )

    if research_btn and company_name:
        with st.spinner(f"Researching {company_name} via DuckDuckGo…"):
            try:
                st.session_state.company_research = research_company(
                    company_name, job_title=job_title
                )
                st.session_state.research_done = True
                st.session_state.last_company   = company_name
                st.session_state.last_job_title = job_title
            except Exception as err:
                st.error(f"Research error: {err}")

    if st.session_state.research_done and st.session_state.company_research:
        res = st.session_state.company_research
        kg  = res.get("knowledge_graph", {})

        if kg.get("description"):
            st.info(f"**{company_name}** — {kg['description']}")

        col_g, col_t, col_n = st.columns(3)
        panels = [
            (col_g, "🏢 Overview",          res.get("general", [])),
            (col_t, "💻 Tech / Engineering", res.get("tech",    [])),
            (col_n, "📰 Recent News",        res.get("news",    [])),
        ]
        for col, title, snippets in panels:
            with col:
                st.markdown(f"**{title}**")
                for s in snippets[:2]:
                    with st.expander(s.get("title", "")[:55]):
                        st.write(s.get("snippet", "—"))
                        st.caption(s.get("link", ""))

    st.divider()

    # ── Generate ──────────────────────────────────────────────────────────────
    missing = []
    if not job_title:        missing.append("Job Title")
    if not job_description:  missing.append("Job Description")
    if not st.session_state.profile: missing.append("Profile (upload CV or set secrets)")

    if missing:
        st.warning(f"⚠️ Please fill in: **{', '.join(missing)}**")

    gen_btn = st.button(
        "✨ Generate ATS-Optimized CV",
        type="primary",
        use_container_width=True,
        disabled=bool(missing),
    )

    if gen_btn:
        gemini_key = get_gemini_key()
        if not gemini_key:
            st.error("Gemini API key missing in secrets.")
        else:
            bar = st.progress(0)
            status = st.empty()

            try:
                if company_name:
                    status.info("🔍 Step 1/4 — Researching company via DuckDuckGo…")
                    bar.progress(10)
                    st.session_state.company_research = research_company(
                        company_name, job_title=job_title
                    )

                status.info("🤖 Step 2/4 — Analysing JD & selecting relevant content…")
                bar.progress(30)

                generated = generate_cv_content(
                    profile=st.session_state.profile,
                    job_description=job_description,
                    company_research=st.session_state.company_research or {},
                    company_name=company_name,
                    job_title=job_title,
                    gemini_api_key=gemini_key,
                )
                st.session_state.generated    = generated
                st.session_state.last_job_title = job_title
                st.session_state.last_company   = company_name

                status.info("🔧 Step 3/4 — Building LaTeX document…")
                bar.progress(65)

                latex_src = build_latex(
                    profile=st.session_state.profile,
                    generated=generated,
                    job_title=job_title,
                    company_name=company_name,
                )
                st.session_state.latex_source = latex_src

                status.info("⚙️ Step 4/4 — Compiling PDF with pdflatex…")
                bar.progress(85)

                pdf = compile_latex_to_pdf(latex_src)
                st.session_state.pdf_bytes = pdf

                bar.progress(100)
                score = generated.get("match_score", 0)
                cls   = score_color(score)
                status.success(
                    f"✅ Done! ATS Match Score: "
                    f"<span class='{cls}'>{score}/100</span>  —  "
                    f"switch to **CV Preview** or **Download** tab.",
                    icon=None,
                )
                st.markdown(
                    f"✅ Done! ATS Match Score: "
                    f"<span class='{cls}'>{score}/100</span>",
                    unsafe_allow_html=True,
                )

            except Exception as err:
                bar.empty()
                status.empty()
                st.error(f"❌ Generation failed: {err}")
                with st.expander("Error details"):
                    st.exception(err)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CV Preview
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.generated:
        st.info("👈 Complete **Job Details** and click **Generate** first.")
    else:
        gen   = st.session_state.generated
        score = gen.get("match_score", 0)

        # ── Score row ─────────────────────────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("ATS Match Score", f"{score}/100")
        m2.metric("Keywords Used",   len(gen.get("ats_keywords_used", [])))
        m3.metric("Projects Selected", len(gen.get("selected_projects", [])))
        m4.metric("Exp. Bullets",     sum(
            len(e.get("bullets", [])) for e in gen.get("selected_experience", [])
        ))

        st.divider()

        # ── Keywords ──────────────────────────────────────────────────────────
        st.subheader("🔑 ATS Keywords Incorporated")
        kw_html = " ".join(
            f'<span class="keyword-badge">{k}</span>'
            for k in gen.get("ats_keywords_used", [])
        )
        st.markdown(kw_html or "_None_", unsafe_allow_html=True)

        st.divider()

        # ── Skills + Notes ────────────────────────────────────────────────────
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("🛠 Selected Skills")
            for cat, items in gen.get("selected_skills", {}).items():
                if items:
                    st.markdown(f"**{cat.title()}**: {', '.join(items)}")

        with c2:
            st.subheader("💡 Optimisation Notes")
            st.info(gen.get("optimization_notes", "—"))

            summary = gen.get("professional_summary", "")
            if summary:
                st.subheader("📝 Professional Summary")
                st.write(summary)

        st.divider()

        # ── Projects ──────────────────────────────────────────────────────────
        st.subheader("🚀 Selected Projects")
        if not gen.get("selected_projects"):
            st.caption("No projects selected for this role.")
        for proj in gen.get("selected_projects", []):
            with st.expander(f"**{proj.get('name')}** — {', '.join(proj.get('tech', []))}  `{proj.get('date','')}`"):
                for b in proj.get("bullets", [proj.get("description", "")]):
                    st.markdown(f"• {b}")

        # ── Experience ────────────────────────────────────────────────────────
        st.subheader("💼 Tailored Experience Bullets")
        for exp in gen.get("selected_experience", []):
            label = f"**{exp.get('role')}** @ {exp.get('company')}  `{exp.get('date','')}`"
            with st.expander(label):
                for b in exp.get("bullets", []):
                    st.markdown(f"• {b}")

        st.divider()

        # ── LaTeX source ──────────────────────────────────────────────────────
        with st.expander("📄 View LaTeX Source (.tex)"):
            st.code(st.session_state.latex_source or "", language="latex")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Download
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    if not st.session_state.pdf_bytes:
        st.info("👈 Generate your CV first.")
    else:
        st.success("🎉 Your ATS-optimized CV is ready to download!")

        gen   = st.session_state.generated or {}
        score = gen.get("match_score", 0)
        cls   = score_color(score)

        st.markdown(
            f"<div class='metric-card'>ATS Match Score: "
            f"<span class='{cls}'>{score}/100</span></div>",
            unsafe_allow_html=True,
        )
        st.write("")

        safe_name = st.session_state.profile.get("name", "Resume").replace(" ", "_")
        date_str  = datetime.now().strftime("%Y%m%d")
        company_s = st.session_state.last_company.replace(" ", "_")
        base_name = f"CV_{safe_name}_{company_s}_{date_str}"

        dl1, dl2 = st.columns(2)

        with dl1:
            st.download_button(
                label="📥 Download PDF Resume",
                data=st.session_state.pdf_bytes,
                file_name=f"{base_name}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

        with dl2:
            st.download_button(
                label="📄 Download LaTeX Source (.tex)",
                data=(st.session_state.latex_source or "").encode(),
                file_name=f"{base_name}.tex",
                mime="text/plain",
                use_container_width=True,
            )

        st.divider()
        st.caption(
            "💡 Open the `.tex` file on [Overleaf](https://overleaf.com) to manually "
            "fine-tune formatting, fonts, or layout before your final submission."
        )

        with st.expander("📊 Full Generation Report"):
            st.json(gen)