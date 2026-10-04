import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from data_lake.storage import save_to_local_lake
from models.schemas import SalesforceLeadSchema

load_dotenv()
logger = logging.getLogger(__name__)

SALESFORCE_API_URL = os.getenv("SALESFORCE_API_URL", "").strip()
SALESFORCE_API_KEY = os.getenv("SALESFORCE_API_KEY", "").strip()
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


@retry(
    retry=retry_if_exception_type((requests.RequestException,)),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _get(url: str, headers: dict[str, str], params: dict[str, Any] | None = None) -> requests.Response:
    response = requests.get(url, headers=headers, params=params, timeout=30)
    if response.status_code == 429:
        raise requests.RequestException("Salesforce API rate limit reached")
    response.raise_for_status()
    return response


def _demo_payload() -> dict[str, Any]:
    return {
        "lead_id": "lead_001",
        "first_name": "John",
        "last_name": "Doe",
        "company": "ABC Technologies",
        "email": "john.doe@example.com",
        "phone": "+919876543210",
        "created_date": "2026-09-09",
    }


def _fetch_salesforce_leads() -> list[dict[str, Any]]:
    if not SALESFORCE_API_URL or not SALESFORCE_API_KEY:
        if DEMO_MODE:
            logger.warning("Salesforce API settings are missing; using DEMO_MODE payload.")
            return [_demo_payload()]
        raise RuntimeError("Set SALESFORCE_API_URL and SALESFORCE_API_KEY in .env")

    headers = {"Authorization": f"Bearer {SALESFORCE_API_KEY}", "Content-Type": "application/json"}
    records: list[dict[str, Any]] = []
    next_url: str | None = SALESFORCE_API_URL

    while next_url:
        payload = _get(next_url, headers).json()
        batch = payload.get("records", [])
        if not isinstance(batch, list):
            raise ValueError("Unexpected Salesforce response: records must be a list")

        for record in batch:
            records.append(record)

        next_url = payload.get("nextRecordsUrl")
        if next_url and next_url.startswith("/"):
            # Allow the URL returned by Salesforce to be relative to the configured host.
            from urllib.parse import urljoin
            next_url = urljoin(SALESFORCE_API_URL, next_url)

    return records


def _to_contract(payload: dict[str, Any]) -> dict[str, Any]:
    if "lead_id" in payload:
        contract = payload
    else:
        contract = {
            "lead_id": payload.get("Id"),
            "first_name": payload.get("FirstName"),
            "last_name": payload.get("LastName"),
            "company": payload.get("Company"),
            "email": payload.get("Email"),
            "phone": payload.get("Phone"),
            "created_date": payload.get("CreatedDate"),
        }

    SalesforceLeadSchema.model_validate(contract)
    return contract


def extract_salesforce() -> list[str]:
    """Extract Salesforce records, validate the contract, and persist raw JSON."""
    logger.info("Starting Salesforce extraction...")
    payloads = _fetch_salesforce_leads()
    saved: list[str] = []

    for index, raw_payload in enumerate(payloads, start=1):
        validated_contract = _to_contract(raw_payload)
        lead_id = validated_contract["lead_id"]
        filename = f"salesforce_{lead_id}_{index}.json"
        saved.append(save_to_local_lake(raw_payload, "salesforce", filename))

    logger.info("Salesforce extraction completed: %s record(s)", len(saved))
    return saved
