import logging

from extractors.salesforce_extractor import extract_salesforce
from extractors.stripe_extractor import extract_stripe


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def run_extractor(name: str, extractor):
    """Run one source independently so a source failure does not stop another."""
    try:
        files = extractor()
        logging.getLogger(__name__).info("%s completed: %d file(s)", name, len(files))
    except Exception:
        logging.getLogger(__name__).exception("%s extraction failed", name)


if __name__ == "__main__":
    run_extractor("Stripe", extract_stripe)
    run_extractor("Salesforce", extract_salesforce)
