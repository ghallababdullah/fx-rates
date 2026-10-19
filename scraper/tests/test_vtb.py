from datetime import timezone
from decimal import Decimal
from pathlib import Path

from fxscraper.sources.vtb import VtbSource

FIXTURE = Path(__file__).parent / "fixtures" / "vtb.json"


def parse():
    return VtbSource().parse(FIXTURE.read_text(encoding="utf-8"))


def test_only_our_five_currencies():
    assert {r.base_currency for r in parse()} == {"USD", "EUR", "CNY", "KZT", "GBP"}


def test_prices_are_exact_and_sensible():
    for rate in parse():
        assert rate.quote_currency == "RUB"
        assert isinstance(rate.buy_rate, Decimal)
        assert 0 < rate.buy_rate <= rate.sell_rate


def test_usd_tiers_have_no_gaps():
    usd = [r for r in parse() if r.base_currency == "USD"]
    assert usd[0].amount_from is None        # first tier starts at 0
    assert usd[-1].amount_to is None         # last tier has no upper limit
    for previous, current in zip(usd, usd[1:-1]):
        assert current.amount_from == previous.amount_to


def test_gbp_has_no_tiers():
    gbp = [r for r in parse() if r.base_currency == "GBP"]
    assert len(gbp) == 1
    assert gbp[0].amount_from is None and gbp[0].amount_to is None


def test_time_is_utc():
    assert parse()[0].valid_from.tzinfo == timezone.utc
