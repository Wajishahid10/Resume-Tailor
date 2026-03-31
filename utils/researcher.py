"""
Company research via DuckDuckGo (no API key required).

Runs three searches per company:
  1. General overview / culture / mission / values
  2. Tech stack, engineering blog, tools used
  3. Recent news (last 12 months)
"""

from ddgs import DDGS
from typing import Optional


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _search(query: str, max_results: int = 5) -> list[dict]:
    """Run a DuckDuckGo text search, return list of {title, snippet, link}."""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title   = r.get("title",   "")
                snippet = r.get("body",    "")   # DDG uses "body" not "snippet"
                link    = r.get("href",    "")
                if snippet:
                    results.append({"title": title, "snippet": snippet, "link": link})
    except Exception as e:
        results.append({
            "title":   "Search unavailable",
            "snippet": str(e),
            "link":    "",
        })
    return results


def _search_news(query: str, max_results: int = 4) -> list[dict]:
    """Run a DuckDuckGo news search."""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results):
                title   = r.get("title",   "")
                snippet = r.get("body",    "")
                link    = r.get("url",     "")   # news uses "url"
                if snippet or title:
                    results.append({"title": title, "snippet": snippet, "link": link})
    except Exception as e:
        results.append({
            "title":   "News unavailable",
            "snippet": str(e),
            "link":    "",
        })
    return results


# ─── Public API ───────────────────────────────────────────────────────────────

def research_company(
    company_name: str,
    serpapi_key:  Optional[str] = None,   # kept for signature compat, unused
    job_title:    Optional[str] = None,
) -> dict:
    """
    Research a company using DuckDuckGo (no API key required).

    Returns:
        {
            "knowledge_graph": {},        # always empty — DDG has no KG endpoint
            "general":  [{title, snippet, link}, ...],
            "tech":     [{title, snippet, link}, ...],
            "news":     [{title, snippet, link}, ...],
        }
    """
    role_hint = f"{job_title} " if job_title else ""

    general = _search(
        f"{company_name} company culture mission values {role_hint}engineering",
        max_results=5,
    )
    tech = _search(
        f"{company_name} engineering tech stack {role_hint}software tools blog",
        max_results=5,
    )
    news = _search_news(
        f"{company_name} news 2025",
        max_results=4,
    )

    return {
        "knowledge_graph": {},    # DDG doesn't provide a structured KG card
        "general":  general,
        "tech":     tech,
        "news":     news,
    }