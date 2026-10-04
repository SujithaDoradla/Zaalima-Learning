import logging
import os
from typing import Any

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from data_lake.storage import save_to_local_lake
from models.schemas import StripePaymentSchema

load_dotenv()
logger = logging.getLogger(__name__)

STRIPE_API_URL = os.getenv("STRIPE_API_URL", "").strip()
STRIPE_API_KEY = os.getenv("STRIPE_API_KEY", "").strip()
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
        raise requests.RequestException("Stripe API rate limit reached")
    response.raise_for_status()
    return response


def _demo_payload() -> dict[str, Any]:
    return {
        "transaction_id": "tx_101",
        "amount": 4999,
        "currency": "USD",
        "customer_email": "customer@example.com",
        "status": "succeeded",
        "created_at": "2026-09-09T10:30:00Z",
    }


def _fetch_stripe_payments() -> list[dict[str, Any]]:
    if not STRIPE_API_URL or not STRIPE_API_KEY:
        if DEMO_MODE:
            logger.warning("Stripe API settings are missing; using DEMO_MODE payload.")
            return [_demo_payload()]
        raise RuntimeError("Set STRIPE_API_URL and STRIPE_API_KEY in .env")

    headers = {"Authorization": f"Bearer {STRIPE_API_KEY}"}
    payments: list[dict[str, Any]] = []
    starting_after: str | None = None

    while True:
        params: dict[str, Any] = {"limit": 100}
        if starting_after:
            params["starting_after"] = starting_after

        payload = _get(STRIPE_API_URL, headers, params).json()
        data = payload.get("data", [])
        if not isinstance(data, list):
            raise ValueError("Unexpected Stripe response: data must be a list")

        payments.extend(data)
        if not payload.get("has_more") or not data:
            break

        last_id = data[-1].get("id")
        if not last_id:
            raise ValueError("Stripe pagination response did not contain an id")
        starting_after = last_id

    return payments


def _to_contract(payload: dict[str, Any]) -> dict[str, Any]:
    """Map a Stripe API object to the project contract, then validate it."""
    if "transaction_id" in payload:
        contract = payload
    else:
        contract = {
            "transaction_id": payload.get("id"),
            "amount": payload.get("amount", 0),
            "currency": payload.get("currency", "USD"),
            "customer_email": payload.get("customer_email") or "customer@example.com",
            "status": payload.get("status", "unknown"),
            "created_at": payload.get("created_at") or payload.get("created"),
        }

    # Validation happens before the raw payload is persisted. The original payload
    # is still what gets written to Bronze so source values are not transformed.
    StripePaymentSchema.model_validate(contract)
    return contract


def extract_stripe() -> list[str]:
    """Extract Stripe records, validate the contract, and persist raw JSON."""
    logger.info("Starting Stripe extraction...")
    payloads = _fetch_stripe_payments()
    saved: list[str] = []

    for index, raw_payload in enumerate(payloads, start=1):
        validated_contract = _to_contract(raw_payload)
        transaction_id = validated_contract["transaction_id"]
        filename = f"stripe_{transaction_id}_{index}.json"
        saved.append(save_to_local_lake(raw_payload, "stripe", filename))

    logger.info("Stripe extraction completed: %s record(s)", len(saved))
    return saved
