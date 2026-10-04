from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StripePaymentSchema(BaseModel):
    """Contract for the normalized fields expected from a Stripe payment."""

    model_config = ConfigDict(extra="allow")

    transaction_id: str = Field(min_length=1)
    amount: int
    currency: str = Field(min_length=1)
    customer_email: EmailStr
    status: str = Field(min_length=1)
    created_at: datetime


class SalesforceLeadSchema(BaseModel):
    """Contract for the normalized fields expected from a Salesforce lead."""

    model_config = ConfigDict(extra="allow")

    lead_id: str = Field(min_length=1)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    company: str = Field(min_length=1)
    email: EmailStr
    phone: str = Field(min_length=1)
    created_date: str = Field(min_length=1)
