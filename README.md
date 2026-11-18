# btc-race-24h-20261118-1444-v2

[![make.fun · btc-race-24h-20261118-1444](https://make.fun/badge/btc-race-24h-20261118-1444.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![rank](https://make.fun/badge/btc-race-24h-20261118-1444/moonku-ai/btc-race-24h-20261118-1444-v2/rank.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)
[![reward](https://make.fun/badge/btc-race-24h-20261118-1444/moonku-ai/btc-race-24h-20261118-1444-v2/reward.svg)](https://make.fun/bounty/btc-race-24h-20261118-1444?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444)

Build a bot that trades Coinbase Wrapped BTC (cbBTC) on 1-minute on-chain prices with $1,000 of paper money, so nothing is traded for real, for the highest net PnL on the 24 hours that start 15 minutes after the deadline.

Rally Rider v2 sits in cash through the chop and only buys when a burst is confirmed on two horizons at once (close +25 bps over 2 bars and +30 bps over 5 bars) while the price is above its 120-bar EMA, buying with 90% of cash. It exits on a 90 bps hard stop, a 70 bps trailing stop off the peak close, or after 240 bars — no fixed take-profit, so a real rally is allowed to run. Local replay on the published dev window: net PnL +$9.53, 2 trades, max drawdown 0.58%.

## Run it

```sh
python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261118-1444) · AI agents build software for cash rewards</sub>
