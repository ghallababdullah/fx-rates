import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from fxscraper.models import BankRate
from fxscraper.sources.base import Source

MOSCOW = ZoneInfo("Europe/Moscow")
TIER = re.compile(r"^(до|от)\s+([\d.]+)$")   # matches "до 100.00" or "от 1000000.00"


class VtbSource(Source):
    code = "VTB"
    extra_headers = {"Referer": "https://www.vtb.ru/personal/platezhi-i-perevody/obmen-valjuty/"}

    def url(self) -> str:
        return "https://www.vtb.ru/api/currencyrates/table/optimized?category=10&type=1"

    def parse(self, content: str) -> list[BankRate]:
        data = json.loads(content, parse_float=Decimal)    # numbers become Decimal, not float

        # "2026-10-19T15:35:00.988" has no timezone. It's Moscow time, so convert to UTC.
        valid_from = (
            datetime.fromisoformat(data["dateFrom"])
            .replace(tzinfo=MOSCOW)
            .astimezone(timezone.utc)
        )

        rates = []
        last_tier_end: dict[str, Decimal] = {}   # remembers where the previous tier ended, per currency

        for row in data["rates"]:
            currency = row["currency1"]["code"]
            if currency not in self.currencies:
                continue

            amount_from, amount_to = self._tier(row.get("tooltip") or "", currency, last_tier_end)
            buy, sell = row["bid"], row["offer"]

            # Safety check: if this fails, VTB changed their format.
            if buy <= 0 or sell <= 0 or buy > sell:
                raise ValueError(f"VTB: suspicious {currency} rate: buy={buy} sell={sell}")

            rates.append(BankRate(
                source=self.code,
                channel=self.channel,
                base_currency=currency,
                quote_currency=row["currency2"]["code"],
                buy_rate=buy,
                sell_rate=sell,
                amount_from=amount_from,
                amount_to=amount_to,
                valid_from=valid_from,
            ))
        return rates

    @staticmethod
    def _tier(tooltip: str, currency: str, last_tier_end: dict[str, Decimal]):
        """'до 100' -> (previous end, 100).  'от 1000000' -> (1000000, None).  '' -> (None, None)."""
        match = TIER.match(tooltip.strip())
        if not match:
            return None, None
        word, value = match.group(1), Decimal(match.group(2))
        if word == "до":                                  # "up to"
            start = last_tier_end.get(currency)
            last_tier_end[currency] = value
            return start, value
        return value, None                                # "from"
