from datetime import datetime, timezone

import httpx

from fxscraper.sources.alfa import AlfaSource
from fxscraper.sources.base import make_ssl_context
from fxscraper.sources.vtb import VtbSource

SOURCES = [VtbSource(), AlfaSource()]


def main() -> None:
    all_rates = []

    with httpx.Client(verify=make_ssl_context()) as client:
        for source in SOURCES:
            try:
                rates = source.parse(source.fetch(client))
                all_rates.extend(rates)
                print(f"{source.code}: {len(rates)} rates")
            except Exception as error:
                print(f"{source.code}: FAILED - {error}")

    print(f"\nScraped at {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC\n")
    print(f"{'BANK':<6} {'CCY':<4} {'BUY':>10} {'SELL':>10}  TIER")

    # Sort by currency so you can compare banks side by side
    for r in sorted(all_rates, key=lambda r: (r.base_currency, r.source)):
        tier = ""
        if r.amount_from is not None or r.amount_to is not None:
            tier = f"{r.amount_from or 0} - {r.amount_to or '∞'}"
        print(f"{r.source:<6} {r.base_currency:<4} {r.buy_rate:>10} {r.sell_rate:>10}  {tier}")


if __name__ == "__main__":
    main()
