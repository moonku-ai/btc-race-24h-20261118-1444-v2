"""Rally Rider v2 - a cbBTC momentum bot for make.fun's btc-race-24h-20261118-1444.

Idea: Bitcoin's 1-minute tape spends most of the day chopping sideways, then
rips in short bursts. This bot sits in cash through the chop and only buys
when a burst is already confirmed on two horizons at once, while the price is
above its slow trend, then rides the burst with a wide trailing stop instead
of capping the win with a fixed take-profit.

Entry (all three must hold on the bar that just closed):
  * the close is above the 120-bar exponential moving average (slow trend up),
  * the close is at least 25 bps above the close 2 bars ago (a sharp burst),
  * the close is at least 30 bps above the close 5 bars ago (the burst is
    sustained, not a one-bar flicker).
Then it buys with 90% of its cash.

Exit (whichever comes first):
  * hard stop: the close falls 90 bps below the volume-weighted average
    fill price of the position,
  * trailing stop: the close falls 70 bps below the highest close seen
    since the entry,
  * time stop: 240 bars have passed since the fill.

The bot is long only, trades at most once per bar, never reads the wall
clock, the environment or any file, and keeps no randomness: two runs on
the same bars produce the same orders. Standard library only.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))

import makefun_bars

SYMBOL = "CBBTC"

# Entry: slow-trend filter plus a two-horizon momentum confirmation.
EMA_BARS = 120
ENTRY_2BAR_BPS = 25
ENTRY_5BAR_BPS = 30
SIZE_BPS = 9000  # buy with 90% of the cash on hand

# Exits: a hard stop, a trailing stop off the peak close, and a time stop.
STOP_BPS = 90
TRAIL_BPS = 70
MAX_HOLD_BARS = 240

# Never chase a fill more than 5% away from the latest close.
MAX_SLIPPAGE_BPS = 500

# Bars of history needed before the first trade (EMA warmed up + lookbacks).
MIN_BARS = 123


class Rider:
    """The strategy state. All prices are raw integer units at price_scale 5."""

    def __init__(self):
        self.closes = []
        self.ema = None
        self.entry_price = None  # volume-weighted average fill price, raw units
        self.entry_qty = 0
        self.peak_close = 0
        self.entry_seq = -1

    def note_fills(self, state, fills):
        """Fold this batch's fills into the entry price (buy fills) and clear
        the entry when a sell empties the position."""
        holding = state.positions.get(SYMBOL)
        for fill in fills or []:
            if fill.get("symbol") != SYMBOL or fill.get("status") != "filled":
                continue
            price = int(fill["price"])
            qty = int(fill["qty"])
            if fill.get("side") == "buy" and qty > 0:
                if self.entry_price is None:
                    self.entry_price = price
                    self.entry_qty = qty
                    # The fill lands on this batch, so the hold clock starts
                    # here, not on the bar the order was decided on.
                    self.entry_seq = state.seq
                else:
                    total = self.entry_qty + qty
                    self.entry_price = (
                        self.entry_price * self.entry_qty + price * qty
                    ) // total
                    self.entry_qty = total
                if price > self.peak_close:
                    self.peak_close = price
        if holding is None and self.entry_price is not None:
            self.entry_price = None
            self.entry_qty = 0
            self.peak_close = 0
            self.entry_seq = -1
        elif holding is not None and self.entry_price is None:
            # Fallback: derive the average entry price from the position cost.
            # value = qty * price * 10**quote_scale / 10**(qty_scale+price_scale)
            #       = qty * price / 10**7, so price = cost * 10**7 / qty.
            qty = holding.qty
            if qty > 0:
                self.entry_price = holding.cost * 10**7 // qty
                self.entry_qty = qty
                self.peak_close = self.entry_price

    def on_batch(self, state, batch):
        close = state.close(SYMBOL)
        if close is None:
            return []
        self.note_fills(state, batch.get("fills"))
        self.closes.append(close)
        if self.ema is None:
            self.ema = float(close)
        else:
            k = 2.0 / (EMA_BARS + 1)
            self.ema = close * k + self.ema * (1.0 - k)
        if close > self.peak_close and self.entry_price is not None:
            self.peak_close = close
        if state.warming_up or len(self.closes) < MIN_BARS:
            return []

        holding = state.positions.get(SYMBOL)
        if holding is not None:
            ret_bps = (close - self.entry_price) * 10000.0 / self.entry_price
            trail_bps = (self.peak_close - close) * 10000.0 / self.peak_close
            if (
                ret_bps <= -STOP_BPS
                or trail_bps >= TRAIL_BPS
                or state.seq - self.entry_seq >= MAX_HOLD_BARS
            ):
                return [
                    {
                        "side": "sell",
                        "symbol": SYMBOL,
                        "qty": holding.qty,
                        "max_slippage_bps": MAX_SLIPPAGE_BPS,
                    }
                ]
            return []

        # Flat: look for a confirmed burst above the slow trend.
        if close <= self.ema:
            return []
        r2 = (close - self.closes[-3]) * 10000.0 / self.closes[-3]
        r5 = (close - self.closes[-6]) * 10000.0 / self.closes[-6]
        if r2 < ENTRY_2BAR_BPS or r5 < ENTRY_5BAR_BPS:
            return []
        notional = state.cash * SIZE_BPS // 10000
        min_notional = int(state.hello["fees"]["min_notional_quote_units"])
        if notional < min_notional:
            return []
        return [
            {
                "side": "buy",
                "symbol": SYMBOL,
                "notional_quote_units": notional,
                "max_slippage_bps": MAX_SLIPPAGE_BPS,
            }
        ]


makefun_bars.run(Rider().on_batch)
