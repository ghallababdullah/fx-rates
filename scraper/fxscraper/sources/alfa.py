import json
from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from fxscraper.models import BankRate
from fxscraper.sources.base import Source

MOSCOW = ZoneInfo("Europe/Moscow")
CLIENT_TYPE = "standardCC"   # individual customers
RATE_TYPE = "makeCash"       # matches the online rate on Alfa's site


class AlfaSource(Source):
    code = "ALFA"

    def url(self) -> str:
        params = {
            "clientType.eq": CLIENT_TYPE,
            "currencyCode.in": ",".join(sorted(self.currencies)),
            "date.lte": datetime.now(MOSCOW).isoformat(timespec="seconds"),   # "now"
            "lastActualForDate.eq": "true",
            "rateType.in": RATE_TYPE,
            "segmentType.eq": "none",
        }
        return "https://alfabank.ru/api/v1/scrooge/currencies/alfa-rates?" + urlencode(params)

    def parse(self, content: str) -> list[BankRate]:
        data = json.loads(content, parse_float=Decimal)
        rates = []

        for currency_block in data["data"]:
            currency = currency_block["currencyCode"]
            if currency not in self.currencies:
                continue

            latest = self._find_latest(currency_block)
            if latest is None:
                continue   # this currency has no online rate for individuals

            buy = latest["buy"]["originalValue"]
            sell = latest["sell"]["originalValue"]
            if buy <= 0 or sell <= 0 or buy > sell:
                raise ValueError(f"ALFA: suspicious {currency} rate: buy={buy} sell={sell}")

            rates.append(BankRate(
                source=self.code,
                channel=self.channel,
                base_currency=currency,
                quote_currency="RUB",
                buy_rate=buy,
                sell_rate=sell,
                amount_from=None,      # Alfa has no amount tiers
                amount_to=None,
                # "2026-10-19T17:18:00+03:00" already has a timezone, so just convert to UTC
                valid_from=datetime.fromisoformat(latest["date"]).astimezone(timezone.utc),
            ))
        return rates

    @staticmethod
    def _find_latest(currency_block: dict) -> dict | None:
        for by_client in currency_block["rateByClientType"]:
            if by_client["clientType"] != CLIENT_TYPE:
                continue
            for by_type in by_client["ratesByType"]:
                if by_type["rateType"] == RATE_TYPE:
                    return by_type["lastActualRate"]
        return None
