import ssl
from abc import ABC, abstractmethod
from pathlib import Path

import certifi
import httpx

from fxscraper.models import BankRate

# scraper/certs/russian-ca-bundle.pem
CA_BUNDLE = Path(__file__).resolve().parents[2] / "certs" / "russian-ca-bundle.pem"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/129.0 Safari/537.36",
    "Accept": "application/json",
}


def make_ssl_context() -> ssl.SSLContext:
    """Normal trusted certificates + the Russian Trusted Root CA."""
    context = ssl.create_default_context(cafile=certifi.where())
    context.load_verify_locations(cafile=str(CA_BUNDLE))
    return context


class Source(ABC):
    code: str                     # "VTB"
    channel: str = "ONLINE"
    currencies = {"USD", "EUR", "CNY", "KZT", "GBP"}
    extra_headers: dict = {}      # a bank can add its own headers

    def fetch(self, client: httpx.Client) -> str:
        response = client.get(
            self.url(),
            headers={**DEFAULT_HEADERS, **self.extra_headers},
            timeout=15,
        )
        response.raise_for_status()   # error on 403, 500, etc.
        return response.text

    @abstractmethod
    def url(self) -> str:
        """The address to download. A method, because Alfa needs the current time in it."""

    @abstractmethod
    def parse(self, content: str) -> list[BankRate]:
        """Raw text in, rates out. No internet here, so tests can use saved files."""
