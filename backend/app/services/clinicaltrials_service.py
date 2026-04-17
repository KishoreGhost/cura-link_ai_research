"""ClinicalTrials.gov v2 API service."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.schemas.contracts import ClinicalTrialRecord

logger = logging.getLogger(__name__)

_BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
_STATUSES = ["RECRUITING", "COMPLETED", "ACTIVE_NOT_RECRUITING"]


def _extract_contact(study: dict[str, Any]) -> str | None:
    """Extract contact info from a study JSON node."""
    contacts_module = (
        study.get("protocolSection", {})
        .get("contactsLocationsModule", {})
    )
    # Central contacts
    central = contacts_module.get("centralContacts", [])
    if central:
        c = central[0]
        name = c.get("name", "")
        email = c.get("email", "")
        phone = c.get("phone", "")
        parts = [p for p in [name, email, phone] if p]
        if parts:
            return " | ".join(parts)
    # Facility contacts
    locations = contacts_module.get("locations", [])
    for loc in locations[:1]:
        contacts = loc.get("contacts", [])
        if contacts:
            c = contacts[0]
            name = c.get("name", "")
            email = c.get("email", "")
            parts = [p for p in [name, email] if p]
            if parts:
                return " | ".join(parts)
    return None


def _extract_location(study: dict[str, Any]) -> str | None:
    locations = (
        study.get("protocolSection", {})
        .get("contactsLocationsModule", {})
        .get("locations", [])
    )
    if not locations:
        return None
    loc = locations[0]
    parts = [
        loc.get("city", ""),
        loc.get("state", ""),
        loc.get("country", ""),
    ]
    return ", ".join(p for p in parts if p) or None


def _extract_eligibility(study: dict[str, Any]) -> str | None:
    criteria = (
        study.get("protocolSection", {})
        .get("eligibilityModule", {})
        .get("eligibilityCriteria", "")
    )
    if not criteria:
        return None
    # Truncate for display
    return criteria[:400].strip() + ("..." if len(criteria) > 400 else "")


def _parse_study(study: dict[str, Any]) -> ClinicalTrialRecord | None:
    try:
        protocol = study.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        status_module = protocol.get("statusModule", {})
        description_module = protocol.get("descriptionModule", {})

        nct_id: str = id_module.get("nctId", "")
        title: str = (
            id_module.get("officialTitle")
            or id_module.get("briefTitle")
            or ""
        )
        if not title:
            return None

        status: str = status_module.get("overallStatus", "UNKNOWN")
        brief_summary: str = description_module.get("briefSummary", "")

        url = f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "https://clinicaltrials.gov/"

        return ClinicalTrialRecord(
            id=nct_id or f"ct-{hash(title)}",
            title=title,
            recruiting_status=status.replace("_", " ").title(),
            eligibility_criteria=_extract_eligibility(study),
            location=_extract_location(study),
            contact_information=_extract_contact(study),
            source="clinicaltrials",
            url=url,
            supporting_snippet=brief_summary[:250] if brief_summary else None,
            relevance_reason="Retrieved via ClinicalTrials.gov API v2",
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("Failed to parse ClinicalTrials study: %s", exc)
        return None


async def fetch_clinical_trials(
    disease: str,
    intent: str | None = None,
    location: str | None = None,
    page_size: int = 50,
) -> list[ClinicalTrialRecord]:
    """Fetch clinical trials for a disease from ClinicalTrials.gov."""
    query_term = f"{intent} {disease}" if intent else disease
    all_records: list[ClinicalTrialRecord] = []

    async with httpx.AsyncClient(timeout=20.0) as client:
        for status in _STATUSES:
            params: dict[str, Any] = {
                "query.cond": query_term,
                "filter.overallStatus": status,
                "pageSize": page_size,
                "format": "json",
                "fields": "protocolSection",
            }
            if location:
                params["query.locn"] = location

            try:
                response = await client.get(_BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                studies = data.get("studies", [])
                for study in studies:
                    record = _parse_study(study)
                    if record:
                        all_records.append(record)
            except Exception as exc:  # noqa: BLE001
                logger.warning("ClinicalTrials fetch failed for status %s: %s", status, exc)

    # deduplicate by ID
    seen: set[str] = set()
    unique: list[ClinicalTrialRecord] = []
    for rec in all_records:
        if rec.id not in seen:
            seen.add(rec.id)
            unique.append(rec)

    return unique
