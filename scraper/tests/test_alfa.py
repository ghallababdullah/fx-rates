from datetime import timezone
from decimal import Decimal
from pathlib import Path

from fxscraper.sources.alfa import AlfaSource

FIXTURE = Path(__file__).parent / "fixtures" / "alfa.json"


def parse():
    return AlfaSource().parse(FIXTURE.read_text(encoding="utf-8"))


def test_one_rate_per_currency():
    currencies = [r.base_currency for r in parse()]
    assert sorted(currencies) == ["CNY", "EUR", "GBP", "KZT", "USD"]


def test_prices_are_exact_and_sensible():
    for rate in parse():
        assert rate.quote_currency == "RUB"
        assert isinstance(rate.buy_rate, Decimal)
        assert 0 < rate.buy_rate <= rate.sell_rate


def test_no_tiers():
    for rate in parse():
        assert rate.amount_from is None and rate.amount_to is None


def test_time_is_utc():
    assert parse()[0].valid_from.tzinfo == timezone.utc


def test_url_contains_current_settings():
    url = AlfaSource().url()
    assert "clientType.eq=standardCC" in url
    assert "rateType.in=makeCash" in url
