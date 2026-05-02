"""
ai_engine.py  —  Helper.ai generation functions powered by GROQ / Sanity content queries.
Set env: GROQ_PROJECT_ID, GROQ_DATASET, GROQ_API_TOKEN
"""

import json
import re
from groq_client import groq_fetch

# ── GROQ helpers ─────────────────────────────────────────────────

def _escape_groq_string(value: str) -> str:
    return value.replace('\\', '\\\\').replace('"', '\\"').strip()


def _safe_text(value) -> str:
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return ''
    return str(value).strip()


def _content_text(result: dict) -> str:
    return _safe_text(
        result.get('content')
        or result.get('body')
        or result.get('summary')
        or result.get('description')
        or result.get('excerpt')
    )


def _load_groq_documents(topic: str, limit: int = 5) -> list[dict]:
    if not topic:
        return []
    safe_topic = _escape_groq_string(topic)
    query = (
        f'*[_type in ["article","post","page","resource","note","document"] && ('
        f'(defined(title) && title match "{safe_topic}") || '
        f'(defined(description) && description match "{safe_topic}") || '
        f'(defined(body) && body match "{safe_topic}") || '
        f'(defined(content) && content match "{safe_topic}") || '
        f'(defined(summary) && summary match "{safe_topic}")'
        f')] | order(_updatedAt desc)[0...{limit}]'
        '{title,description,body,content,summary,excerpt,_type}'
    )
    try:
        result = groq_fetch(query)
    except Exception as exc:
        raise RuntimeError(f"GROQ query failed: {exc}") from exc
    if isinstance(result, dict):
        return [result]
    return result or []


def _sentence_bullets(text: str, limit: int = 4) -> list[str]:
    if not text:
        return []
    candidates = [s.strip() for s in re.split(r'[\.\n]+', text) if s.strip()]
    bullets = []
    for item in candidates:
        if len(bullets) >= limit:
            break
        bullets.append(item if len(item) <= 120 else item[:117].rstrip() + '...')
    return bullets


def _build_summary(text: str, max_words: int = 30) -> str:
    words = [w for w in re.split(r'\s+', text) if w]
    if not words:
        return ''
    return ' '.join(words[:max_words]) + ('...' if len(words) > max_words else '')


def _fallback_content(topic: str) -> str:
    return f"No GROQ content was found for '{topic}'. Update your Sanity dataset or refine the query term."


# ── PPT Generator ─────────────────────────────────────────────────

def generate_ppt(topic: str) -> dict:
    docs = _load_groq_documents(topic, limit=4)
    slides = [
        {
            "slide_number": 1,
            "type": "title",
            "heading": topic,
            "body": f"A topic-focused presentation based on GROQ content for: {topic}",
            "bullet_points": [],
            "speaker_notes": f"Introduce the presentation topic and explain the goal of the slides."
        }
    ]

    if docs:
        for index, doc in enumerate(docs, start=2):
            content = _content_text(doc) or _fallback_content(topic)
            slides.append(
                {
                    "slide_number": index,
                    "type": "content",
                    "heading": doc.get('title') or doc.get('_type') or f"Section {index}",
                    "body": _build_summary(content, max_words=50),
                    "bullet_points": _sentence_bullets(content, limit=4),
                    "speaker_notes": f"Review the key information from the GROQ document titled '{doc.get('title', 'Untitled')}'."
                }
            )
    else:
        slides.append(
            {
                "slide_number": 2,
                "type": "content",
                "heading": "No GROQ content available",
                "body": _fallback_content(topic),
                "bullet_points": [],
                "speaker_notes": "This presentation is generated from fallback content because no GROQ matches were returned."
            }
        )

    slides.append(
        {
            "slide_number": len(slides) + 1,
            "type": "conclusion",
            "heading": "Summary",
            "body": f"This deck summarizes the most relevant GROQ search matches for '{topic}'.",
            "bullet_points": [
                "Use this deck as a starting point for deeper research.",
                "Refine your Sanity dataset or query for more precise content.",
                "Add slides as needed based on available content."
            ],
            "speaker_notes": "Conclude with next steps and how to extend the generated material."
        }
    )

    return {
        "title": f"{topic} — Presentation",
        "subtitle": "Generated from GROQ content search results.",
        "theme_color": "#5340B7",
        "slides": slides
    }


# ── Report Generator ──────────────────────────────────────────────

def generate_report(topic: str) -> dict:
    docs = _load_groq_documents(topic, limit=4)
    content = ' '.join(_content_text(doc) for doc in docs if _content_text(doc))
    summary = _build_summary(content or _fallback_content(topic), max_words=60)

    sections = [
        {
            "heading": "Introduction",
            "content": summary or _fallback_content(topic)
        },
        {
            "heading": "Key Findings",
            "content": _build_summary(content, max_words=80) or _fallback_content(topic)
        },
        {
            "heading": "Analysis",
            "content": _build_summary(content, max_words=90) or _fallback_content(topic)
        },
        {
            "heading": "Recommendations",
            "content": f"Use the GROQ search results to refine your topic and expand the dataset for better coverage."
        },
        {
            "heading": "Conclusion",
            "content": f"This report is generated from content returned by Sanity/GROQ for the search term '{topic}'."
        }
    ]

    return {
        "title": f"{topic} — Report",
        "abstract": summary or _fallback_content(topic),
        "sections": sections,
        "word_count_estimate": max(300, len(summary.split()) * 5),
        "keywords": [topic, "GROQ", "Sanity", "content discovery"]
    }


# ── Smart Notes Generator ─────────────────────────────────────────

def generate_notes(text: str) -> dict:
    docs = _load_groq_documents(text, limit=3)
    content = ' '.join(_content_text(doc) for doc in docs if _content_text(doc))
    summary = _build_summary(content or _fallback_content(text), max_words=60)

    key_points = _sentence_bullets(content, limit=6)
    if not key_points:
        key_points = [f"Search GROQ for '{text}' to discover related content."]

    sections = []
    for doc in docs[:2]:
        section_text = _content_text(doc)
        if section_text:
            sections.append(
                {
                    "heading": doc.get('title') or "GROQ Content",
                    "content": _build_summary(section_text, max_words=70),
                    "important_terms": [
                        {"term": doc.get('_type', 'content'), "definition": "A related content type from Sanity."}
                    ]
                }
            )

    if not sections:
        sections.append(
            {
                "heading": "GROQ Search Notes",
                "content": _fallback_content(text),
                "important_terms": [{"term": "GROQ", "definition": "A query language for Sanity content."}]
            }
        )

    flashcards = [
        {"question": "What is the main topic of these notes?", "answer": text},
        {"question": "What should you do if no GROQ results are returned?", "answer": "Refine your query or update your Sanity dataset."}
    ]

    return {
        "title": f"Notes — {text[:40]}{'…' if len(text) > 40 else ''}",
        "summary": summary or _fallback_content(text),
        "key_points": key_points,
        "sections": sections,
        "flashcards": flashcards,
        "exam_tips": [
            "Use GROQ queries to extract the most relevant content from Sanity.",
            "Keep queries focused and test with specific topic terms."
        ]
    }