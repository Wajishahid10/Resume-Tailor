"""
Company research via DuckDuckGo (no API key required).

Runs three searches per company, in PARALLEL using ThreadPoolExecutor:
  1. General overview / culture / mission / values
  2. Tech stack, engineering blog, tools used
  3. Recent news (last 12 months)
"""

from ddgs import DDGS
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _search(query: str, max_results: int = 4) -> list[dict]:
    """DuckDuckGo text search → [{title, snippet, link}]."""
    try:
        with DDGS() as ddgs:
            return [
                {"title": r.get("title", ""), "snippet": r.get("body", ""), "link": r.get("href", "")}
                for r in ddgs.text(query, max_results=max_results)
                if r.get("body")
            ]
    except Exception as e:
        return [{"title": "Search unavailable", "snippet": str(e), "link": ""}]


def _search_news(query: str, max_results: int = 3) -> list[dict]:
    """DuckDuckGo news search → [{title, snippet, link}]."""
    try:
        with DDGS() as ddgs:
            return [
                {"title": r.get("title", ""), "snippet": r.get("body", ""), "link": r.get("url", "")}
                for r in ddgs.news(query, max_results=max_results)
                if r.get("title")
            ]
    except Exception as e:
        return [{"title": "News unavailable", "snippet": str(e), "link": ""}]


# ─── Public API ───────────────────────────────────────────────────────────────

def research_company(
    company_name: str,
    job_title:    Optional[str] = None,
) -> dict:
    """
    Research a company using 3 parallel DuckDuckGo searches.
    Parallel execution cuts total time from ~9s sequential → ~3s.
    """
    role_hint = f"{job_title} " if job_title else ""

    tasks = {
        "general": (
            _search,
            f"{company_name} company culture mission values {role_hint}engineering",
            4,
        ),
        "tech": (
            _search,
            f"{company_name} engineering tech stack {role_hint}software tools",
            4,
        ),
        "news": (
            _search_news,
            f"{company_name} news 2025",
            3,
        ),
    }

    results = {"knowledge_graph": {}, "general": [], "tech": [], "news": []}

    # Run all three searches in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(fn, query, n): section
            for section, (fn, query, n) in tasks.items()
        }
        for future in as_completed(futures):
            section = futures[future]
            try:
                results[section] = future.result()
            except Exception as e:
                results[section] = [{"title": "unavailable", "snippet": str(e), "link": ""}]

    return results