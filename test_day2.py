import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from data_lake.storage import save_to_local_lake
from models.schemas import SalesforceLeadSchema, StripePaymentSchema


def test_stripe_schema_accepts_demo_payload():
    payload = {
        "transaction_id": "tx_101",
        "amount": 4999,
        "currency": "USD",
        "customer_email": "customer@example.com",
        "status": "succeeded",
        "created_at": "2026-09-09T10:30:00Z",
    }
    model = StripePaymentSchema.model_validate(payload)
    assert model.transaction_id == "tx_101"


def test_salesforce_schema_accepts_demo_payload():
    payload = {
        "lead_id": "lead_001",
        "first_name": "John",
        "last_name": "Doe",
        "company": "ABC Technologies",
        "email": "john.doe@example.com",
        "phone": "+919876543210",
        "created_date": "2026-09-09",
    }
    model = SalesforceLeadSchema.model_validate(payload)
    assert model.lead_id == "lead_001"


def test_invalid_stripe_email_is_rejected():
    with pytest.raises(ValidationError):
        StripePaymentSchema.model_validate({
            "transaction_id": "tx_1",
            "amount": 100,
            "currency": "USD",
            "customer_email": "not-an-email",
            "status": "succeeded",
            "created_at": "2026-09-09T10:30:00Z",
        })


def test_raw_storage_preserves_payload(tmp_path, monkeypatch):
    import data_lake.storage as storage
    monkeypatch.setattr(storage, "RAW_ROOT", tmp_path)

    payload = {"amount": 4999, "currency": "USD", "nested": {"a": 1}}
    path = save_to_local_lake(payload, "stripe", "sample.json")

    assert Path(path).exists()
    assert json.loads(Path(path).read_text(encoding="utf-8")) == payload
