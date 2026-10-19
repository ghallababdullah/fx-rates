from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class BankRate:
    source: str                  # bank code: "VTB", "ALFA"
    channel: str                 # rate type: "ONLINE"
    base_currency: str           # the foreign currency: "USD"
    quote_currency: str          # the currency of the price: "RUB"
    buy_rate: Decimal            # price the bank pays when it buys USD from you
    sell_rate: Decimal           # price you pay when the bank sells USD to you
    amount_from: Decimal | None  # tier start (None = from 0)
    amount_to: Decimal | None    # tier end   (None = no limit)
    valid_from: datetime         # when the bank set this rate (UTC)
