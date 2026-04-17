"""LLM service — Ollama integration with structured medical research prompting.

Uses the local Ollama server (configured via settings.ollama_base_url).
Falls back gracefully if Ollama is unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.core.config import get_settings
from app.schemas.contracts import (
    AnswerSection,
    ChatMessage,
    ClinicalTrialRecord,
    CitationRecord,
    PublicationRecord,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# ─── Conversational intent detection ─────────────────────────────────────────

_CONVERSATIONAL_PATTERNS: list[str] = [
    # Greetings
    'hello', 'hi', 'hey', 'howdy', 'hiya', 'sup', 'what\'s up', "what's up",
    # Identity
    'who are you', 'what are you', 'what can you do', 'what do you do',
    'tell me about yourself', 'introduce yourself', 'your name',
    # Pleasantries
    'how are you', 'how\'s it going', 'good morning', 'good afternoon',
    'good evening', 'good night', 'thanks', 'thank you', 'thx', 'ty',
    'cheers', 'cool', 'awesome', 'great', 'nice',
    # Help
    'help', 'what should i ask', 'how does this work', 'get started',
    'can you help', 'how do i use',
]

_MEDICAL_KEYWORDS: list[str] = [
    'disease', 'cancer', 'diabetes', 'treatment', 'symptoms', 'diagnosis',
    'trial', 'medication', 'drug', 'study', 'research', 'clinical', 'therapy',
    'patient', 'cure', 'syndrome', 'disorder', 'condition', 'infection',
    'surgery', 'hospital', 'doctor', 'physician', 'oncology', 'neurology',
    'cardiovascular', 'parkinson', 'alzheimer', 'covid', 'vaccine', 'gene',
]


def is_conversational(message: str) -> bool:
    """Return True if the message is a greeting / off-topic chat, not a medical query."""
    msg = message.lower().strip().rstrip('!?.')
    # Very short messages with no medical keywords are almost always conversational
    if len(msg.split()) <= 3:
        has_medical = any(kw in msg for kw in _MEDICAL_KEYWORDS)
        if not has_medical:
            return True
    # Explicit pattern match
    for pattern in _CONVERSATIONAL_PATTERNS:
        if pattern in msg:
            return True
    return False


_CONVERSATIONAL_SYSTEM_PROMPT = """You are Cura, a friendly AI medical research assistant built by Curalink.
You help patients, caregivers, and healthcare professionals find peer-reviewed research from PubMed and OpenAlex,
and discover relevant clinical trials from ClinicalTrials.gov.

When someone greets you or asks about yourself, respond in a warm, concise, and human tone.
Keep your reply to 2-3 sentences max. Do not mention JSON or structured formats.
Do not make up medical information. If asked a medical question, tell them to type it in and you'll research it."""

_FALLBACK_REPLIES: dict[str, str] = {
    'default': (
        "Hey there! I'm Cura, your AI medical research assistant. "
        "Ask me about any medical condition, treatment, or clinical trial — "
        "I'll pull real research from PubMed, OpenAlex, and ClinicalTrials.gov and synthesize it for you."
    ),
    'thanks': "You're welcome! Feel free to ask me anything about a medical condition or treatment.",
    'help': (
        "Sure! Just type a medical question like \'Latest treatments for Parkinson\'s disease\' "
        "or \'Clinical trials for Type 2 Diabetes in Canada\' and I\'ll get to work."
    ),
}


async def generate_conversational_response(message: str) -> tuple[list[AnswerSection], list[CitationRecord], str]:
    """Generate a friendly conversational reply without triggering any research pipeline."""
    # Decide which fallback to use
    msg_lower = message.lower()
    if any(w in msg_lower for w in ['thank', 'thx', 'ty', 'cheers']):
        fallback_text = _FALLBACK_REPLIES['thanks']
    elif any(w in msg_lower for w in ['help', 'how does', 'how do', 'get started']):
        fallback_text = _FALLBACK_REPLIES['help']
    else:
        fallback_text = _FALLBACK_REPLIES['default']

    # Try Ollama for a natural response first
    ollama_url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                ollama_url,
                json={
                    "model": settings.ollama_chat_model,
                    "messages": [
                        {"role": "system", "content": _CONVERSATIONAL_SYSTEM_PROMPT},
                        {"role": "user", "content": message},
                    ],
                    "stream": False,
                    "options": {"temperature": 0.7, "num_predict": 120},
                },
            )
            if response.status_code == 200:
                raw = response.json().get("message", {}).get("content", "").strip()
                if raw:
                    section = AnswerSection(heading="Cura", body=raw)
                    return [section], [], raw
    except Exception as exc:
        logger.debug("Ollama unavailable for conversational reply: %s", exc)

    # Hardcoded fallback
    section = AnswerSection(heading="Cura", body=fallback_text)
    return [section], [], fallback_text


def _format_publications(publications: list[PublicationRecord]) -> str:
    if not publications:
        return "No publications retrieved."
    lines: list[str] = []
    for i, pub in enumerate(publications[:6], 1):
        authors_str = ", ".join(pub.authors[:3]) + (" et al." if len(pub.authors) > 3 else "")
        lines.append(
            f"[P{i}] {pub.title}\n"
            f"     Authors: {authors_str or 'Unknown'} | Year: {pub.publication_year or 'N/A'} | Source: {pub.source}\n"
            f"     Abstract: {pub.abstract_snippet or 'Not available'}\n"
            f"     URL: {pub.url}"
        )
    return "\n\n".join(lines)


def _format_trials(trials: list[ClinicalTrialRecord]) -> str:
    if not trials:
        return "No clinical trials retrieved."
    lines: list[str] = []
    for i, trial in enumerate(trials[:6], 1):
        lines.append(
            f"[T{i}] {trial.title}\n"
            f"     Status: {trial.recruiting_status} | Location: {trial.location or 'N/A'}\n"
            f"     Eligibility: {trial.eligibility_criteria or 'See full record'}\n"
            f"     Contact: {trial.contact_information or 'N/A'}\n"
            f"     URL: {trial.url}"
        )
    return "\n\n".join(lines)


def _build_system_prompt(
    disease: str,
    intent: str | None,
    location: str | None,
    publications: list[PublicationRecord],
    trials: list[ClinicalTrialRecord],
) -> str:
    return f"""You are Curalink, an evidence-first AI medical research assistant. Your job is to synthesize peer-reviewed publications and clinical trial data into clear, structured, personalized medical research summaries.

IMPORTANT RULES:
- Only use information from the provided publications and trials. Do NOT hallucinate or add external facts.
- Always cite sources by their reference number (e.g., [P1], [T2]).
- Be specific to the disease context: {disease}.
- If location is provided ({location or "not specified"}), mention relevant location-specific trials.
- Use plain language that a patient or caregiver can understand, while remaining medically accurate.

You MUST respond in this exact JSON format:
{{
  "condition_overview": "<2-3 sentence overview of the condition and current research landscape>",
  "research_insights": "<3-5 sentences synthesizing the key findings from the publications, citing [P1], [P2] etc.>",
  "clinical_trials_summary": "<2-4 sentences on relevant trials, their status and who might qualify, citing [T1], [T2] etc. If no trials, say so.>",
  "personalized_note": "<1-2 sentences tailored to the specific intent: {intent or 'general research'} — connect research to the user's situation>"
}}

--- RETRIEVED PUBLICATIONS ---
{_format_publications(publications)}

--- RETRIEVED CLINICAL TRIALS ---
{_format_trials(trials)}
"""


def _parse_llm_json(raw: str) -> dict[str, str]:
    """Extract JSON from LLM response, handling markdown code blocks."""
    raw = raw.strip()
    # Strip markdown code blocks if present
    if "```json" in raw:
        raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in raw:
        raw = raw.split("```", 1)[1].split("```", 1)[0].strip()
    # Find first { to last }
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start : end + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM JSON output.")
        return {}


def _build_answer_sections(parsed: dict[str, str], query: str) -> list[AnswerSection]:
    sections: list[AnswerSection] = []
    if parsed.get("condition_overview"):
        sections.append(AnswerSection(heading="Condition Overview", body=parsed["condition_overview"]))
    if parsed.get("research_insights"):
        sections.append(AnswerSection(heading="Research Insights", body=parsed["research_insights"]))
    if parsed.get("clinical_trials_summary"):
        sections.append(AnswerSection(heading="Clinical Trials", body=parsed["clinical_trials_summary"]))
    if parsed.get("personalized_note"):
        sections.append(AnswerSection(heading="Personalized Insight", body=parsed["personalized_note"]))
    if not sections:
        sections.append(
            AnswerSection(
                heading="Research Summary",
                body=f"Based on the retrieved evidence for your query about '{query}', "
                "the system retrieved relevant publications and clinical trials. "
                "Please review the evidence panel for detailed source information.",
            )
        )
    return sections


def _build_citations(
    publications: list[PublicationRecord],
    trials: list[ClinicalTrialRecord],
) -> list[CitationRecord]:
    citations: list[CitationRecord] = []
    for pub in publications[:6]:
        citations.append(
            CitationRecord(
                id=pub.id,
                source=pub.source,
                title=pub.title,
                year=pub.publication_year,
                authors=pub.authors,
                url=pub.url,
                snippet=pub.supporting_snippet or pub.abstract_snippet or "See source for details.",
            )
        )
    for trial in trials[:4]:
        citations.append(
            CitationRecord(
                id=trial.id,
                source="clinicaltrials",
                title=trial.title,
                year=None,
                authors=["ClinicalTrials.gov"],
                url=trial.url,
                snippet=trial.supporting_snippet or trial.eligibility_criteria or "See trial record.",
            )
        )
    return citations


async def generate_research_answer(
    query: str,
    disease: str,
    intent: str | None,
    location: str | None,
    conversation_history: list[ChatMessage],
    publications: list[PublicationRecord],
    trials: list[ClinicalTrialRecord],
) -> tuple[list[AnswerSection], list[CitationRecord], str]:
    """
    Call Ollama to generate a structured answer.
    Returns (answer_sections, citations, raw_assistant_text).
    """
    system_prompt = _build_system_prompt(disease, intent, location, publications, trials)

    # Build message list: system + history + current query
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
    for msg in conversation_history[-6:]:  # Keep last 6 messages for context
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": query})

    ollama_url = f"{settings.ollama_base_url.rstrip('/')}/api/chat"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                ollama_url,
                json={
                    "model": settings.ollama_chat_model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.3, "top_p": 0.9},
                },
            )
            response.raise_for_status()
            data = response.json()
            raw_content: str = data.get("message", {}).get("content", "")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ollama call failed: %s — using fallback summary.", exc)
        raw_content = ""

    citations = _build_citations(publications, trials)

    if raw_content:
        parsed = _parse_llm_json(raw_content)
        if parsed:
            sections = _build_answer_sections(parsed, query)
            return sections, citations, raw_content

    # Fallback: build sections from raw data without LLM
    fallback_sections = _build_fallback_sections(query, disease, publications, trials)
    return fallback_sections, citations, "(Ollama unavailable — evidence-based fallback summary)"


def _build_fallback_sections(
    query: str,
    disease: str,
    publications: list[PublicationRecord],
    trials: list[ClinicalTrialRecord],
) -> list[AnswerSection]:
    """Build a basic structured response from raw evidence without LLM."""
    sections: list[AnswerSection] = []

    sections.append(
        AnswerSection(
            heading="Condition Overview",
            body=f"Research overview for {disease}. {len(publications)} relevant publications and "
            f"{len(trials)} clinical trials were retrieved and ranked for your query.",
        )
    )

    if publications:
        top_pubs = publications[:3]
        insights = " | ".join(
            f"'{p.title[:60]}...' ({p.publication_year or 'N/A'}, {p.source})" for p in top_pubs
        )
        sections.append(
            AnswerSection(
                heading="Research Insights",
                body=f"Top retrieved publications: {insights}. Review the evidence panel for full abstracts and source links.",
            )
        )

    if trials:
        top_trials = trials[:3]
        trial_info = " | ".join(
            f"'{t.title[:50]}...' [{t.recruiting_status}]" for t in top_trials
        )
        sections.append(
            AnswerSection(
                heading="Clinical Trials",
                body=f"Relevant trials found: {trial_info}. Check eligibility and contact information in the trials panel.",
            )
        )

    return sections
