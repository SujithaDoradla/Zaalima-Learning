# Enterprise ETL Pipeline — Day 2 Ingestion Layer

This implementation covers the Day 2 Multi-Source Extraction & Ingestion Engine (Bronze layer).

## What is included

- Separate Stripe and Salesforce extractor modules
- Pydantic validation contracts
- Environment-variable configuration via `.env`
- Retry handling for transient HTTP/rate-limit failures
- Pagination support for Stripe and Salesforce response patterns
- Independent extractor execution
- Raw JSON persistence under `data_lake/raw/<source>/`
- Unit tests with Pytest
- Demo mode for local testing without real API credentials

## Run locally

1. Create/activate a Python 3.11+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Keep `DEMO_MODE=true` to test without external APIs, or set the real API URL/token values in `.env` and use `DEMO_MODE=false`.
4. Run:

```bash
python main.py
```

5. Run tests:

```bash
pytest -q
```

## Bronze-layer rule

The external source payload is validated against the Pydantic contract before it is written. The original payload is then persisted to the raw layer rather than being transformed by Pandas/Polars or other business logic. Transformations belong to the later Silver layer.
